import uvicorn
from fastapi import FastAPI

from core.config import settings

app = FastAPI()


@app.get("/health", status_code=200, tags=["health"])
async def health_check():
    return {"status": "ok"}


@app.get("/ready", status_code=200, tags=["health"])
async def readiness_check():
    return {"status": "ready"}


if __name__ == "__main__":
    uvicorn.run("src.main:app", port=settings.PORT, reload=True)
