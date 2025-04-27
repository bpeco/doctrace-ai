import os
from fastapi import FastAPI, Request, Header, HTTPException
from dotenv import load_dotenv
import hmac
import hashlib
from json import JSONDecodeError
from app.utils.get_utils import get_repo_diff

# Load environment variables from .env
load_dotenv()


GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
PORT = int(os.getenv("PORT", 8000))

app = FastAPI(
    title="doctrace-ai",
    description="Auto-doc & changelog generator service",
    version="0.1.0"
)

@app.get("/")
async def root():
    return {"message": "doctrace-ai is up and running"}

# Helper to verify GitHub webhook signature for both SHA-256 and SHA-1
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
    # Handle ping event
    if x_github_event == "ping":
        return {"status": "pong"}

    # Only process push events
    if x_github_event != "push":
        return {"status": "ignored", "event": x_github_event}

    # Read raw body for signature verification
    payload_bytes = await request.body()
    signature_header = x_hub_signature_256 or x_hub_signature
    verify_github_signature(payload_bytes, signature_header)

    # Parse JSON payload
    try:
        payload = await request.json()
    except JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Extract old and new revisions from payload
    old_rev = payload.get("before")
    new_rev = payload.get("after")
    if not old_rev or not new_rev:
        raise HTTPException(status_code=400, detail="Missing before or after revisions in payload")

    # Determine repository path (assumes current working dir)
    repo_path = os.getcwd()

    # Extract changed files and diff text
    try:
        changed_files, diff_text = get_repo_diff(repo_path, old_rev, new_rev)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting diff: {e}")

    # Respond with basic diff info (for testing)
    return {
        "status": "received",
        "commit_count": len(payload.get("commits", [])),
        "changed_files": changed_files,
        "diff_snippet": diff_text[:1000]  # first 1000 chars
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT)
