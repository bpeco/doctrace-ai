import os
from fastapi import FastAPI, Request, Header, HTTPException
from dotenv import load_dotenv
import hmac
import hashlib

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

# Helper to verify GitHub webhook signature
def verify_github_signature(payload_body: bytes, signature_header: str):
    if not GITHUB_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")
    sha_name, signature = signature_header.split('=', 1)
    if sha_name != 'sha1':
        raise HTTPException(status_code=400, detail="Unsupported signature type")
    mac = hmac.new(GITHUB_WEBHOOK_SECRET.encode(), msg=payload_body, digestmod=hashlib.sha1)
    if not hmac.compare_digest(mac.hexdigest(), signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

@app.post("/webhook")
async def webhook_receiver(request: Request, x_hub_signature: str = Header(None)):
    payload_bytes = await request.body()
    # Verify GitHub signature
    verify_github_signature(payload_bytes, x_hub_signature)

    payload = await request.json()
    # TODO: process commits/diff
    commits = payload.get("commits", [])
    return {"status": "received", "commit_count": len(commits)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT)
