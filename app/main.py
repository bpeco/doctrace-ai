import os
import json
import hmac
import hashlib
from datetime import date
from fastapi import FastAPI, Request, Header, HTTPException
from dotenv import load_dotenv
from json import JSONDecodeError
from git import Repo
from github import Github
from app.utils.get_utils import get_repo_diff
from app.agents.changelog import generate_changelog_entry

# Load environment variables
load_dotenv()
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")  # owner/repo
PORT = int(os.getenv("PORT", 8000))

# Local and remote repo clients
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

# Helper: verify GitHub webhook signature
def verify_github_signature(payload_body: bytes, signature_header: str):
    if not GITHUB_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")
    if not signature_header:
        raise HTTPException(status_code=400, detail="Missing signature header")
    if signature_header.startswith("sha256="):
        _, signature = signature_header.split("=", 1)
        digestmod = hashlib.sha256
    elif signature_header.startswith("sha1="):
        _, signature = signature_header.split("=", 1)
        digestmod = hashlib.sha1
    else:
        raise HTTPException(status_code=400, detail="Unsupported signature type")
    mac = hmac.new(GITHUB_WEBHOOK_SECRET.encode(), msg=payload_body, digestmod=digestmod)
    if not hmac.compare_digest(mac.hexdigest(), signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

@app.post("/webhook")
async def webhook_receiver(
    request: Request,
    x_hub_signature: str = Header(None, alias="X-Hub-Signature"),
    x_hub_signature_256: str = Header(None, alias="X-Hub-Signature-256"),
    x_github_event: str = Header(None, alias="X-GitHub-Event"),
):
    # Ping endpoint
    if x_github_event == "ping":
        return {"status": "pong"}
    # Only handle push events
    if x_github_event != "push":
        return {"status": "ignored", "event": x_github_event}

    # Read raw payload and verify signature
    payload_body = await request.body()
    sig_header = x_hub_signature_256 or x_hub_signature
    verify_github_signature(payload_body, sig_header)

    # Parse JSON payload
    try:
        payload = json.loads(payload_body.decode())
    except JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Only process pushes to main branch
    ref = payload.get("ref")
    if ref != "refs/heads/main":
        return {"status": "ignored", "ref": ref}

    # Extract commit SHAs
    old_rev = payload.get("before")
    new_rev = payload.get("after")
    if not old_rev or not new_rev:
        raise HTTPException(status_code=400, detail="Missing revisions in payload")

    # Get unified diff and changed files
    try:
        changed_files, diff_text = get_repo_diff(REPO_PATH, old_rev, new_rev)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting diff: {e}")

    # Generate changelog entry
    entry = generate_changelog_entry(diff_text)

    # Append entry under Unreleased in CHANGELOG.md
    changelog_file = os.path.join(REPO_PATH, "CHANGELOG.md")
    with open(changelog_file, "r+") as f:
        content = f.read()
        marker = "## [Unreleased]"
        idx = content.find(marker)
        if idx == -1:
            raise HTTPException(status_code=500, detail="CHANGELOG.md missing [Unreleased] section")
        head = content[: idx + len(marker) ]
        tail = content[idx + len(marker) :]
        new_content = head + "\n" + entry + "\n" + tail
        f.seek(0)
        f.write(new_content)
        f.truncate()

    # Create branch, commit, push, and open PR
    branch = f"auto/docs-{new_rev[:7]}"
    LOCAL_REPO.git.checkout("-b", branch)
    LOCAL_REPO.index.add(["CHANGELOG.md"])
    LOCAL_REPO.index.commit(f"chore: update changelog for {new_rev[:7]}")
    LOCAL_REPO.remotes.origin.push(branch)

    pr = GH_REPO.create_pull(
        title=f"docs: update changelog for {new_rev[:7]}",
        body="Automated changelog update",
        head=branch,
        base="main",
    )

    return {
        "status": "pr_created",
        "pr_url": pr.html_url,
        "changed_files": changed_files,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT)
