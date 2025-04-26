from fastapi import FastAPI, Request

app = FastAPI(
    title="doctrace-ai",
    description="Auto-doc & changelog generator service",
    version="0.0.1"
)

@app.get("/")
async def root():
    return {"message": "doctrace-ai is up and running"}

@app.post("/webhook")
async def webhook_receiver(request: Request):
    payload = await request.json()
    # TODO: aquí procesaremos el payload del GitHub Webhook
    return {"status": "received", "files_changed": len(payload.get("commits", []))}
