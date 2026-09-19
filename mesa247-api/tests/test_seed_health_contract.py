import json
from pathlib import Path

from sqlalchemy import event, func, select
from sqlalchemy.orm import Session

from app.models import HostDevice, Location, TicketEvent
from app.notifier import FakeNotifier
from seed import seed


def test_seed_rerun_and_explicit_rotation(env, client, headers):
    with Session(env["engine"]) as session:
        assert all(token is None for _, token in seed(session))
        assert session.scalar(select(func.count()).select_from(Location)) == 3
        assert session.scalar(select(func.count()).select_from(HostDevice)) == 3
        tokens = dict(seed(session, rotate_tokens=True))
    assert client.get("/api/host/queue", headers=headers).status_code == 401
    assert client.get("/api/host/queue", headers={"Authorization": f"Bearer {tokens['terraza-lima']}"}).status_code == 200


def test_health_and_openapi_contract(client, env):
    assert client.get("/healthz").json() == {"status": "ok"}
    assert client.get("/readyz").json() == {"status": "ok"}
    spec = client.get("/openapi.json").json()
    assert spec["paths"]["/api/host/queue"]["get"]["security"] == [{"HTTPBearer": []}]
    assert "security" not in spec["paths"]["/api/public/tickets/{token}"]["get"]
    artifact = Path(__file__).resolve().parents[2] / "mesa247-docs/api/openapi.json"
    assert spec == json.loads(artifact.read_text(encoding="utf-8"))


def test_notifier_masks_personal_data(caplog):
    from types import SimpleNamespace
    FakeNotifier().send_table_ready(SimpleNamespace(id=1, phone_e164="+51987654321", customer_name="Private name"))
    assert "321" in caplog.text
    assert "987654321" not in caplog.text and "Private name" not in caplog.text


def test_failed_notification_event_does_not_undo_call(env, client, headers, join_ticket):
    join_ticket()
    ident = client.get("/api/host/queue", headers=headers).json()["rows"][0]["id"]
    def fail(mapper, connection, target):
        if target.type == "notification_sent":
            raise RuntimeError("Event unavailable")
    event.listen(TicketEvent, "before_insert", fail)
    try:
        response = client.post(f"/api/host/tickets/{ident}/call", headers=headers)
    finally:
        event.remove(TicketEvent, "before_insert", fail)
    assert response.status_code == 200 and response.json()["status"] == "called"
    assert response.json()["notify_state"] == "none"
    assert client.post(f"/api/host/tickets/{ident}/call", headers=headers).status_code == 200
    assert env["notifier"].sent == [ident]
