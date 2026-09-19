from datetime import timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import HostDevice, Location


def test_host_cannot_touch_other_location(client, join_ticket, env, headers):
    join_ticket(code="vientos-lima")
    other_headers = {"Authorization": f"Bearer {env['tokens']['vientos-lima']}"}
    ident = client.get("/api/host/queue", headers=other_headers).json()["rows"][0]["id"]
    assert client.get("/api/host/queue", headers=headers).json()["rows"] == []
    for action in ("call", "seat", "no-show", "leave", "remove"):
        assert client.post(f"/api/host/tickets/{ident}/{action}", headers=headers).status_code == 404


def test_lookup_returns_active_ticket_of_today(client, join_ticket, headers):
    ticket = join_ticket().json()
    lookup = lambda: client.post("/api/public/locations/terraza-lima/lookup", json={"phone": "+51 987654321"})
    assert lookup().json()["token"] == ticket["token"]
    ident = client.get("/api/host/queue", headers=headers).json()["rows"][0]["id"]
    client.post(f"/api/host/tickets/{ident}/call", headers=headers)
    assert lookup().json()["status"] == "called"


@pytest.mark.parametrize("scenario", ["none", "terminal", "other_location", "yesterday"])
def test_lookup_404_when_none(client, join_ticket, env, scenario):
    if scenario != "none":
        result = join_ticket(code="vientos-lima" if scenario == "other_location" else "terraza-lima")
        if scenario == "terminal":
            client.post(f"/api/public/tickets/{result.json()['token']}/cancel")
        if scenario == "yesterday":
            env["clock"][0] += timedelta(days=1)
    response = client.post("/api/public/locations/terraza-lima/lookup", json={"phone": "987654321"})
    assert response.status_code == 404
    assert "token" not in response.json()


def test_auth_and_inactive_locations(client, env, headers, join_ticket):
    assert client.get("/api/host/queue").status_code == 401
    assert client.get("/api/host/queue", headers={"Authorization": "Bearer invalid"}).status_code == 401
    with Session(env["engine"]) as session:
        location = session.scalar(select(Location).where(Location.public_code == "terraza-lima"))
        location.is_active = False
        session.commit()
    assert client.get("/api/host/queue", headers=headers).status_code == 401
    assert client.get("/api/public/locations/terraza-lima").status_code == 404
    assert join_ticket().status_code == 404


def test_revoked_device(client, env, headers):
    with Session(env["engine"]) as session:
        device = session.scalar(select(HostDevice).order_by(HostDevice.id))
        device.revoked_at = env["clock"][0]
        session.commit()
    assert client.get("/api/host/queue", headers=headers).status_code == 401
