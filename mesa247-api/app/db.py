from collections.abc import Iterator

from fastapi import Request
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.config import Settings


def build_engine(settings: Settings):
    sqlite = settings.database_url.startswith("sqlite:")
    args = {"check_same_thread": False} if sqlite else {}
    if settings.database_ssl_ca and not sqlite:
        args["ssl"] = {"ca": settings.database_ssl_ca, "check_hostname": True}
    options = {} if sqlite else {"isolation_level": "READ COMMITTED"}
    engine = create_engine(settings.database_url, connect_args=args,
                           pool_pre_ping=True, hide_parameters=True, **options)
    if sqlite:
        @event.listens_for(engine, "connect")
        def configure_sqlite(connection, _):
            cursor = connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout=5000")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    return engine


def get_session(request: Request) -> Iterator[Session]:
    with Session(request.app.state.engine, expire_on_commit=False) as session:
        yield session
