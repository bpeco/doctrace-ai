import os
import json
import hmac
import hashlib
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
import datetime
import uuid



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


def update_changelog(diff: str):
    path = os.path.join(REPO_PATH, "CHANGELOG.md")
    entry = generate_changelog_entry(diff)

    with open(path, "r+") as f:
        lines = f.readlines()
        unreleased_idx = next((i for i, L in enumerate(lines) if L.strip() == "## [Unreleased]"), None)

        if unreleased_idx is None:
            first_section = next((i for i, L in enumerate(lines) if L.startswith("## ")), len(lines))
            unreleased_idx = first_section
            lines.insert(unreleased_idx, "\n")
            lines.insert(unreleased_idx, "## [Unreleased]\n")
        
        insert_idx = unreleased_idx + 1
        
        while insert_idx < len(lines) and lines[insert_idx].strip() == "":
            insert_idx += 1
        
        entry_lines = [ln + ("\n" if not ln.endswith("\n") else "") for ln in entry.splitlines()]
        entry_lines.append("\n")
        lines[insert_idx:insert_idx] = entry_lines
        
        f.seek(0)
        f.writelines(lines)
        f.truncate()

def bump_release_changelog():
    path = os.path.join(REPO_PATH, "CHANGELOG.md")

    with open(path, "r+") as f:
        lines = f.readlines()
        start = next((i for i, L in enumerate(lines) if L.strip() == "## [Unreleased]"), None)

        if start is None:
            return
        
        end = start + 1
        
        while end < len(lines) and not lines[end].startswith("## "):
            end += 1
        
        bullets = lines[start + 1 : end]
        del lines[start:end]
        
        today = datetime.date.today().isoformat()
        new_block = []
        new_block.append(f"## {today}\n")
        new_block.extend(bullets)
        new_block.append("\n")
        new_block.append("## [Unreleased]\n")
        new_block.append("\n")
        lines[start:start] = new_block
        
        f.seek(0)
        f.writelines(lines)
        f.truncate()

    LOCAL_REPO.git.add("CHANGELOG.md")
    LOCAL_REPO.index.commit(f"chore: release changelog for {today}")
    LOCAL_REPO.remotes.origin.push()

    
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
    x_sig: str = Header(None, alias="X-Hub-Signature"),
    x_sig256: str = Header(None, alias="X-Hub-Signature-256"),
    x_event: str = Header(None, alias="X-GitHub-Event"),
):
    body = await request.body()
    sig = x_sig256 or x_sig
    verify_signature(body, sig)
    payload = json.loads(body.decode())

    if x_event == "push":
        ref = payload.get("ref")
        head = payload.get("head_commit", {})
        msg = head.get("message", "")

        if msg.startswith("chore: release changelog"):
            return {"status": "ignored", "reason": "release bump"}

        if msg.startswith("Merge pull request") and "auto/docs-" in msg:
            return {"status": "ignored", "reason": "docs merge"}

        if ref == "refs/heads/main":
            old = payload.get("before")
            new = payload.get("after")
            if old and new:
                files, diff = get_repo_diff(REPO_PATH, old, new)

                LOCAL_REPO.remotes.origin.fetch("main")
                main_ref = LOCAL_REPO.remotes.origin.refs.main
                branch_name = f"auto/docs-{uuid.uuid4().hex[:8]}"
                if branch_name in LOCAL_REPO.heads:
                    LOCAL_REPO.delete_head(branch_name, force=True)
                LOCAL_REPO.create_head(branch_name, main_ref.commit)
                LOCAL_REPO.heads[branch_name].checkout()

                update_changelog(diff)

                LOCAL_REPO.git.add("CHANGELOG.md")
                LOCAL_REPO.index.commit("chore: generate changelog entry for [Unreleased]")
                LOCAL_REPO.remotes.origin.push(branch_name, force=True)

                pr_url = create_branch_and_pr(["CHANGELOG.md"], new)
                return {"status": "pr_created", "pr_url": pr_url}

        return {"status": "ignored", "event": x_event}

    if x_event == "pull_request":
        action = payload.get("action")
        pr = payload.get("pull_request", {})
        merged = pr.get("merged")
        base_ref = pr.get("base", {}).get("ref")
        head_ref = pr.get("head", {}).get("ref")

        if action == "closed" and merged and base_ref == "main" and head_ref.startswith("auto/docs-"):
            bump_release_changelog()
            return {"status": "changelog_released", "date": date.today().isoformat()}

    return {"status": "ignored", "event": x_event}



if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT)
