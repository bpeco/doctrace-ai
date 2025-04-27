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

# Load environment variables
load_dotenv()
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")  # format: owner/repo
PORT = int(os.getenv("PORT", 8000))

# Initialize Git clients
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


def extract_diff(payload: dict) -> tuple[list, str]:
    """Extract changed_files list and unified diff between commits."""
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
    """Generate changelog entry and append under ## [Unreleased]."""
    entry = generate_changelog_entry(diff)
    path = os.path.join(REPO_PATH, "CHANGELOG.md")
    with open(path, "r+") as f:
        content = f.read()
        if "## [Unreleased]" not in content:
            raise HTTPException(500, "CHANGELOG.md missing [Unreleased]")
        head, tail = content.split("## [Unreleased]", 1)
        new = head + "## [Unreleased]" + "\n" + entry + "\n" + tail
        f.seek(0)
        f.write(new)
        f.truncate()


def apply_doc_patches(diff: str) -> list:
    """Generate docstring patches and apply them. Returns list of modified files."""
    patches = generate_docstrings(diff)
    for file_path, text in patches.items():
        tmp = tempfile.NamedTemporaryFile(mode='w', delete=False)
        tmp.write(text)
        tmp.close()
        print(f"Wirting tmp >>> {tmp}")
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
    # Health-checks
    if x_event == "ping":
        return {"status": "pong"}
    if x_event != "push":
        return {"status": "ignored", "event": x_event}

    body = await request.body()
    sig = x_signature256 or x_signature
    verify_signature(body, sig)

    try:
        payload = json.loads(body.decode())
    except JSONDecodeError:
        raise HTTPException(400, "Invalid JSON body")

    if payload.get("ref") != "refs/heads/main":
        return {"status": "ignored", "ref": payload.get("ref")}

    # Process changes
    changed, diff = extract_diff(payload)
    update_changelog(diff)
    docs_changed = apply_doc_patches(diff)

    # Commit all changes and open PR
    files_to_commit = ["CHANGELOG.md"] + docs_changed
    pr_url = create_branch_and_pr(files_to_commit, payload.get("after"))

    return {"status": "pr_created", "pr_url": pr_url, "changed_files": changed}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT)
