import pytest
from sqlalchemy import event, select
from sqlalchemy.orm import Session

from app.domain.queue import apply_transition
from app.models import Ticket, TicketEvent


def ticket_id(client, headers):
    return client.get("/api/host/queue", headers=headers).json()["rows"][0]["id"]


def test_call_twice_sends_one_notification(client, join_ticket, headers, env):
    join_ticket()
    ident = ticket_id(client, headers)
    for _ in range(2):
        result = client.post(f"/api/host/tickets/{ident}/call", headers=headers)
        assert result.status_code == 200
        assert result.json()["notify_state"] == "sent"
    assert env["notifier"].sent == [ident]
    with Session(env["engine"]) as session:
        assert session.get(Ticket, ident).call_count == 1
        assert list(session.scalars(select(TicketEvent.type).order_by(TicketEvent.id))) == ["joined", "called", "notification_sent"]


@pytest.mark.parametrize("first,second,public", [
    ("leave", "seat", False), (None, "no-show", False), ("seat", "cancel", True),
    ("call", "leave", False), ("remove", "call", False),
])
def test_invalid_transitions_return_409(client, join_ticket, headers, first, second, public):
    token = join_ticket().json()["token"]
    ident = ticket_id(client, headers)
    if first:
        assert client.post(f"/api/host/tickets/{ident}/{first}", headers=headers).status_code == 200
    path = f"/api/public/tickets/{token}/{second}" if public else f"/api/host/tickets/{ident}/{second}"
    result = client.post(path, headers=headers)
    assert result.status_code == 409
    assert result.json()["error"] == "invalid_transition"


@pytest.mark.parametrize("action,status", [
    ("seat", "seated"), ("leave", "cancelled"), ("no-show", "no_show"),
    ("remove", "removed"), ("expire", "expired"),
])
def test_terminal_states_release_active_key(client, join_ticket, headers, env, action, status):
    join_ticket()
    ident = ticket_id(client, headers)
    if action == "no-show":
        client.post(f"/api/host/tickets/{ident}/call", headers=headers)
    if action == "expire":
        with Session(env["engine"]) as session:
            apply_transition(session, session.get(Ticket, ident), "expire", "system", env["clock"][0])
    else:
        for _ in range(2):
            assert client.post(f"/api/host/tickets/{ident}/{action}", headers=headers).status_code == 200
    with Session(env["engine"]) as session:
        ticket = session.get(Ticket, ident)
        assert ticket.status == status
        assert ticket.active_key is None
        assert ticket.closed_at == env["clock"][0]
        assert len(list(session.scalars(select(TicketEvent).where(TicketEvent.type == ("left" if action == "leave" else status))))) == 1
    assert join_ticket().status_code == 201


def test_notifier_failure_keeps_ticket_called(client, join_ticket, headers, env):
    join_ticket()
    env["notifier"].fail = True
    ident = ticket_id(client, headers)
    result = client.post(f"/api/host/tickets/{ident}/call", headers=headers)
    assert result.status_code == 200
    assert result.json()["status"] == "called"
    assert result.json()["notify_state"] == "failed"
    with Session(env["engine"]) as session:
        assert "notification_failed" in list(session.scalars(select(TicketEvent.type)))


def test_event_failure_rolls_back_transition(client, join_ticket, headers, env):
    join_ticket()
    ident = ticket_id(client, headers)
    def reject_event(mapper, connection, target):
        if target.type == "seated":
            raise RuntimeError("Simulated event storage failure")
    event.listen(TicketEvent, "before_insert", reject_event)
    try:
        with Session(env["engine"]) as session:
            with pytest.raises(RuntimeError):
                apply_transition(session, session.get(Ticket, ident), "seat", "system", env["clock"][0])
    finally:
        event.remove(TicketEvent, "before_insert", reject_event)
    with Session(env["engine"]) as session:
        ticket = session.get(Ticket, ident)
        assert ticket.status == "waiting" and ticket.active_key and ticket.closed_at is None
        assert list(session.scalars(select(TicketEvent.type))) == ["joined"]


def test_public_cancel_called_and_no_show_retry(client, join_ticket, headers):
    token = join_ticket().json()["token"]
    ident = ticket_id(client, headers)
    client.post(f"/api/host/tickets/{ident}/call", headers=headers)
    assert client.post(f"/api/public/tickets/{token}/cancel").json()["status"] == "cancelled"
    next_ticket = join_ticket()
    assert next_ticket.status_code == 201
    next_token = next_ticket.json()["token"]
    ident = ticket_id(client, headers)
    client.post(f"/api/host/tickets/{ident}/call", headers=headers)
    client.post(f"/api/host/tickets/{ident}/no-show", headers=headers)
    repeat = client.post(f"/api/public/tickets/{next_token}/cancel")
    assert repeat.status_code == 200 and repeat.json()["status"] == "no_show"
    with_token = client.post("/api/public/locations/terraza-lima/lookup", json={"phone": "987654321"})
    assert with_token.status_code == 404
