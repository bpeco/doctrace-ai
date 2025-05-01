import os
import json
import hmac
import hashlib
from datetime import date
import tempfile
from fastapi import FastAPI, Request, Header, HTTPException
from dotenv import load_dotenv
from json import JSONDecodeError
from git import Repo
from github import Github
from app.utils.get_utils import get_repo_diff
from app.agents.changelog import generate_changelog_entry
from app.agents.docs_generator import generate_docstrings
import uvicorn
import re


# Load environment variables
load_dotenv()

# GitHUB configuration for managing webhooks and repository
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")  # format: owner/repo
PORT = int(os.getenv("PORT", 8000))
REPO_PATH = os.getcwd()
LOCAL_REPO = Repo(REPO_PATH)
GH_CLIENT = Github(GITHUB_TOKEN)
GH_REPO = GH_CLIENT.get_repo(GITHUB_REPO)

app = FastAPI(
    title="doctrace-ai",
    description="Auto-doc & changelog generator service",
    version="0.1.0"
)

@app.get("/")
async def root():
    return {"message": "doctrace-ai is up and running"}


def verify_signature(payload: bytes, signature: str):
    """Verify GitHub HMAC signature."""
    if not GITHUB_WEBHOOK_SECRET:
        raise HTTPException(500, "Webhook secret not configured")
    if not signature:
        raise HTTPException(400, "Missing signature header")
    algo = hashlib.sha256 if signature.startswith("sha256=") else hashlib.sha1
    _, sig = signature.split("=", 1)
    mac = hmac.new(GITHUB_WEBHOOK_SECRET.encode(), msg=payload, digestmod=algo)
    if not hmac.compare_digest(mac.hexdigest(), sig):
        raise HTTPException(401, "Invalid signature")


def extract_diff(payload: dict, base_branch: str | None = None) -> tuple[list, str]:
    """
    Extract the list of changed files and the unified diff between commits.
    If base_branch is provided, it compares against the head of that branch.
    """
    if base_branch:
        LOCAL_REPO.remotes.origin.fetch(base_branch)
        old = LOCAL_REPO.commit(base_branch).hexsha
    else:
        old = payload.get("before")

    new = payload.get("after")
    if not old or not new:
        raise HTTPException(400, "Missing before/after revisions")

    try:
        files, diff = get_repo_diff(REPO_PATH, old, new)
    except Exception as e:
        raise HTTPException(500, f"Error extracting diff: {e}")

    return files, diff



def update_changelog(diff: str) -> None:
    """
    Generate changelog entry and insert it under the ## [Unreleased] section.
    """
    entry = generate_changelog_entry(diff)
    path = os.path.join(REPO_PATH, "CHANGELOG.md")

    with open(path, "r+") as f:
        lines = f.readlines()

        unreleased_idx = None
        for idx, line in enumerate(lines):
            if line.strip() == "## [Unreleased]":
                unreleased_idx = idx
                break

        if unreleased_idx is None:
            for idx, line in enumerate(lines):
                if re.match(r"^## \d{4}-\d{2}-\d{2}", line):
                    unreleased_idx = idx
                    break

            if unreleased_idx is None:
                unreleased_idx = len(lines)

            lines.insert(unreleased_idx, "\n")
            lines.insert(unreleased_idx, "## [Unreleased]\n")


        insert_idx = unreleased_idx + 1
        while insert_idx < len(lines) and lines[insert_idx].strip() == "":
            insert_idx += 1


        entry_lines = [ln + ("\n" if not ln.endswith("\n") else "")
                       for ln in entry.splitlines()]

        entry_lines.append("\n")


        lines[insert_idx:insert_idx] = entry_lines

        f.seek(0)
        f.writelines(lines)
        f.truncate()


# Deprecated
def apply_doc_patches(diff: str) -> list:
    """Generate docstring patches and apply them. Returns list of modified files."""
    patches = generate_docstrings(diff)
    for file_path, text in patches.items():
        tmp = tempfile.NamedTemporaryFile(mode='w', delete=False)
        tmp.write(text)
        tmp.close()
        print(f"=== Debug patch for {file_path} ===")
        print(text)
        LOCAL_REPO.git.apply('--unidiff-zero', tmp.name)
    return list(patches.keys())


def create_branch_and_pr(files: list, rev: str) -> str:
    """Commit given files, push branch and open a PR; returns PR URL."""
    branch = f"auto/docs-{rev[:7]}"
    LOCAL_REPO.git.checkout("-b", branch)
    LOCAL_REPO.index.add(files)
    LOCAL_REPO.index.commit(f"chore: update changelog and docs for {rev[:7]}")
    LOCAL_REPO.remotes.origin.push(branch)
    pr = GH_REPO.create_pull(
        title=f"docs: update changelog and docstrings for {rev[:7]}",
        body="Automated update of changelog and docstrings.",
        head=branch,
        base="main"
    )
    return pr.html_url

@app.post("/webhook")
async def webhook_receiver(
    request: Request,
    x_signature: str = Header(None, alias="X-Hub-Signature"),
    x_signature256: str = Header(None, alias="X-Hub-Signature-256"),
    x_event: str = Header(None, alias="X-GitHub-Event")
):
    # Filter events to only process push events
    if x_event != "push":
        return {"status": "ignored", "event": x_event}

    body = await request.body()
    sig = x_signature256 or x_signature
    verify_signature(body, sig)

    try:
        payload = json.loads(body.decode())
    except JSONDecodeError:
        raise HTTPException(400, "Invalid JSON body")

    ref = payload.get("ref")
    if not ref or not ref.startswith("refs/heads/"):
        return {"status": "ignored", "ref": ref}
    branch = ref.replace("refs/heads/", "")

    # Define 'main' branch for diff (I could use another branch if needed)
    MAIN_BRANCH = "main"
    if branch.startswith("feature/") or branch.startswith("fix/"):
        base_branch = MAIN_BRANCH
    else:
        return {"status": "ignored", "ref": ref}

    changed, diff = extract_diff(payload, base_branch)
    update_changelog(diff)

    files_to_commit = ["CHANGELOG.md"]
    pr_url = create_branch_and_pr(files_to_commit, payload.get("after"))

    return {"status": "pr_created", "pr_url": pr_url, "changed_files": changed}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT)
