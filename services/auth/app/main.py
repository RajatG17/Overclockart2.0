from fastapi import FastAPI
from .routes import router as auth_router


app = FastAPI(title="Auth Service")

app.include_router(auth_router)

@app.get("/health/live")
async def liveness() -> dict[str, str]:
    return {"status" : "ok"}

@app.get("/health/ready")
async def readiness() -> dict[str, str]:
    return {"status": "ready"}

