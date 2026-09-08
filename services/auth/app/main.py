from fastapi import FastAPI, HTTPException, status
from .routes import router as auth_router
from sqlalchemy import text

from .database import engine

app = FastAPI(title="Auth Service")

app.include_router(auth_router)

@app.get("/health/live")
async def liveness() -> dict[str, str]:
    return {"status" : "ok"}

@app.get("/health/ready")
async def readiness() -> dict[str, str]:
    try:
        async with engine.connect() as connection:
            await connection.execute(
                text("SELECT 1")
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable"
        )

    return {"status": "ready"}
