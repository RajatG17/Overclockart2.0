from fastapi import FastAPI, HTTPException, status

from .routes import router as order_router
from .database import engine
from sqlalchemy import text

app = FastAPI(title="Order Service")

app.include_router(order_router)

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
            detail="Database unavailable",
        )

    return {"status": "ready"}

