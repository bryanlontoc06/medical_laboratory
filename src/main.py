from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from loguru import logger

from core.config import settings
from db.database import Base, engine
from src import models


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup
    registered_tables = list(Base.metadata.tables.keys())
    logger.info(f"🚀 Initializing models from: {models.__name__}")
    logger.info(f"📦 Tables detected in registry: {registered_tables}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.success("✅ Database sync complete. Tables are ready!")
    yield
    # Shutdown
    await engine.dispose()
    logger.warning("🛑 Database connection closed. Application shutdown.")


app = FastAPI(lifespan=lifespan)


@app.get("/health", status_code=200, tags=["health"])
async def health_check():
    return {"status": "ok"}


@app.get("/ready", status_code=200, tags=["health"])
async def readiness_check():
    return {"status": "ready"}


if __name__ == "__main__":
    uvicorn.run("src.main:app", port=settings.PORT, reload=True)
