from fastapi import FastAPI

app = FastAPI(title="Order Service")

@app.get("/health/live")
async def liveness() -> dict[str, str]:
    return {"status" : "ok"}

@app.get("/health/ready")
async def readiness() -> dict[str, str]:
    return {"status": "ready"}

