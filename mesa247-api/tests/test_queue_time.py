from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from app.domain.time import service_date


def test_service_date():
    instant = datetime(2026, 9, 19, 8, 30, tzinfo=UTC)
    lima = SimpleNamespace(timezone="America/Lima", day_cutoff_hour=5)
    santiago = SimpleNamespace(timezone="America/Santiago", day_cutoff_hour=5)
    assert service_date(lima, instant).isoformat() == "2026-09-18"
    assert service_date(santiago, instant).isoformat() == "2026-09-19"
    lima.day_cutoff_hour = 3
    assert service_date(lima, instant).isoformat() == "2026-09-19"


def test_position_ignores_called_and_closed_with_ties(client, join_ticket, headers):
    tokens = [join_ticket(phone=phone).json()["token"] for phone in ("987654321", "999888777", "988777666")]
    def positions():
        return [client.get(f"/api/public/tickets/{token}").json()["groups_ahead"] for token in tokens]
    assert positions() == [0, 1, 2]
    rows = client.get("/api/host/queue", headers=headers).json()["rows"]
    client.post(f"/api/host/tickets/{rows[0]['id']}/call", headers=headers)
    assert positions() == [None, 0, 1]
    client.post(f"/api/host/tickets/{rows[1]['id']}/seat", headers=headers)
    assert positions() == [None, None, 0]


def test_happy_path_deadline_average_and_day_filter(client, join_ticket, headers, env):
    token = join_ticket().json()["token"]
    queue = client.get("/api/host/queue", headers=headers).json()
    assert queue["waiting_count"] == 1 and queue["avg_wait_min"] is None
    ident = queue["rows"][0]["id"]
    env["clock"][0] += timedelta(minutes=7)
    client.post(f"/api/host/tickets/{ident}/call", headers=headers)
    public = client.get(f"/api/public/tickets/{token}").json()
    assert public["status"] == "called" and public["deadline_at"].endswith("Z")
    env["clock"][0] += timedelta(minutes=11)
    assert client.get("/api/host/queue", headers=headers).json()["rows"][0]["overdue"]
    client.post(f"/api/host/tickets/{ident}/seat", headers=headers)
    assert client.get("/api/host/queue", headers=headers).json()["avg_wait_min"] == 18
    join_ticket()
    env["clock"][0] += timedelta(days=1)
    assert client.get("/api/host/queue", headers=headers).json()["rows"] == []
    assert join_ticket().status_code == 201
