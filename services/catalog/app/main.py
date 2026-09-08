from fastapi import FastAPI

from .routes import router as catalog_router

app = FastAPI(title="Catalog Service")

app.include_router(catalog_router)

@app.get("/health/live")
async def liveness() -> dict[str, str]:
    return {"status" : "ok"}

@app.get("/health/ready")
async def readiness() -> dict[str, str]:
    return {"status": "ready"}

