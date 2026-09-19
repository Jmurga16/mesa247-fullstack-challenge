from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException

from app.config import Settings, settings
from app.db import build_engine
from app.errors import ApiError
from app.models import Base
from app.routers import host, public
from app.schemas import ErrorResponse

def create_app(config: Settings | None = None, engine=None) -> FastAPI:
    config = config or settings
    logging.getLogger("mesa247").setLevel(logging.INFO)
    if not logging.getLogger("mesa247").handlers:
        logging.getLogger("mesa247").addHandler(logging.StreamHandler())

    @asynccontextmanager
    async def lifespan(application):
        application.state.engine = engine if engine is not None else build_engine(config)
        if config.create_tables:
            Base.metadata.create_all(application.state.engine)
        yield
        if engine is None:
            application.state.engine.dispose()

    application = FastAPI(title=config.app_name, lifespan=lifespan, responses={
        code: {"model": ErrorResponse} for code in (401, 404, 409, 503)
    })

    @application.exception_handler(ApiError)
    async def api_error(request, exc):
        headers = {"WWW-Authenticate": "Bearer"} if exc.status == 401 else None
        return JSONResponse(status_code=exc.status,
                            content={"error": exc.error, "message": exc.message}, headers=headers)

    @application.exception_handler(SQLAlchemyError)
    async def database_error(request, exc):
        return JSONResponse(status_code=503, content={"error": "temporarily_unavailable",
                            "message": "No pudimos conectar. Inténtalo de nuevo en unos segundos."})

    @application.exception_handler(HTTPException)
    async def http_error(request, exc):
        return JSONResponse(status_code=exc.status_code, content={
            "error": "not_found" if exc.status_code == 404 else "http_error",
            "message": "No encontramos esa ruta." if exc.status_code == 404 else "La solicitud no está permitida."})

    @application.exception_handler(Exception)
    async def unexpected_error(request, exc):
        logging.getLogger("mesa247").error("Fallo inesperado: %s", type(exc).__name__)
        return JSONResponse(status_code=500, content={"error": "internal_error",
                            "message": "No pudimos completar la solicitud. Inténtalo de nuevo."})

    @application.middleware("http")
    async def private_responses(request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
            response.headers["Referrer-Policy"] = "no-referrer"
        return response

    @application.get("/healthz", tags=["health"])
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/readyz", tags=["health"])
    def readyz(request: Request) -> dict[str, str]:
        with request.app.state.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ok"}

    application.include_router(public.router)
    application.include_router(host.router)
    return application


app = create_app()
