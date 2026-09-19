from fastapi import FastAPI

from app.config import settings

app = FastAPI(title=settings.app_name)


@app.get("/healthz", tags=["health"])
def healthz() -> dict[str, str]:
    return {"status": "ok"}
