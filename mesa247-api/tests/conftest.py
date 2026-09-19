import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.engine import make_url

from app.config import Settings
from app.db import build_engine
from app.domain.time import now
from app.main import create_app
from app.notifier import get_notifier
from seed import seed


class RecordingNotifier:
    def __init__(self):
        self.sent = []
        self.fail = False

    def send_table_ready(self, ticket):
        self.sent.append(ticket.id)
        if self.fail:
            raise RuntimeError("Provider unavailable")


@pytest.fixture
def env(tmp_path):
    # MySQL integration runner supplies a freshly created, disposable database.
    url = os.environ.get("MESA247_TEST_DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    if "MESA247_TEST_DATABASE_URL" in os.environ:
        parsed = make_url(url)
        if parsed.host != "127.0.0.1" or not (parsed.database or "").startswith("mesa247_test_"):
            raise ValueError("Integration tests require a disposable local mesa247_test_* database")
    config = Settings(_env_file=None, database_url=url)
    engine = build_engine(config)
    app = create_app(config, engine)
    clock = [datetime(2026, 9, 18, 21, tzinfo=UTC)]
    notifier = RecordingNotifier()
    app.dependency_overrides[now] = lambda: clock[0]
    app.dependency_overrides[get_notifier] = lambda: notifier
    with TestClient(app, raise_server_exceptions=False) as client:
        with Session(engine) as session:
            # Delete only tables in the disposable integration database, never DATABASE_URL.
            if "MESA247_TEST_DATABASE_URL" in os.environ:
                from app.models import Base
                for table in reversed(Base.metadata.sorted_tables):
                    session.execute(table.delete())
                session.commit()
            tokens = dict(seed(session))
        yield {"client": client, "engine": engine, "clock": clock,
               "notifier": notifier, "tokens": tokens, "app": app}
    engine.dispose()


@pytest.fixture
def client(env):
    return env["client"]


@pytest.fixture
def headers(env):
    return {"Authorization": f"Bearer {env['tokens']['terraza-lima']}"}


@pytest.fixture
def join_ticket(client):
    def create(code="terraza-lima", **changes):
        body = {"request_id": str(uuid4()), "name": "Carla", "phone": "987 654 321", "party_size": 4}
        body.update(changes)
        return client.post(f"/api/public/locations/{code}/tickets", json=body)
    return create
