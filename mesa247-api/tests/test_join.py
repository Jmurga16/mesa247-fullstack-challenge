from datetime import timedelta
from uuid import uuid4

import pytest
from sqlalchemy import event as sqlalchemy_event, func, select
from sqlalchemy.orm import Session

from app.models import Ticket, TicketEvent


def test_join_retry_same_request_id_returns_same_ticket(client, join_ticket, env):
    request_id = str(uuid4())
    first = join_ticket(request_id=request_id)
    second = join_ticket(request_id=request_id)
    assert (first.status_code, second.status_code) == (201, 200)
    assert first.json() == second.json()
    token = first.json()["token"]
    client.post(f"/api/public/tickets/{token}/cancel")
    assert join_ticket(request_id=request_id).json()["status"] == "cancelled"
    with Session(env["engine"]) as session:
        assert session.scalar(select(func.count()).select_from(Ticket)) == 1
        assert session.scalar(select(func.count()).select_from(TicketEvent).where(TicketEvent.type == "joined")) == 1


def test_join_same_phone_other_request_id_returns_409_without_token(join_ticket):
    first = join_ticket()
    duplicate = join_ticket(phone="+51 987654321")
    assert duplicate.status_code == 409
    assert duplicate.json()["error"] == "already_in_queue"
    assert "token" not in duplicate.json()
    assert first.json()["token"] not in duplicate.text


@pytest.mark.parametrize("code,phone,normalized", [
    ("terraza-lima", "987 654 321", "+51987654321"),
    ("casa-santiago", "9 8765 4321", "+56987654321"),
])
def test_phone_normalization(join_ticket, env, code, phone, normalized):
    result = join_ticket(code=code, phone=phone)
    assert result.status_code == 201
    with Session(env["engine"]) as session:
        assert session.scalar(select(Ticket)).phone_e164 == normalized


@pytest.mark.parametrize("changes", [
    {"phone": "basura"}, {"name": "  "}, {"name": "a" * 41},
    {"party_size": 0}, {"party_size": 21}, {"party_size": 51},
    {"party_size": True}, {"request_id": "not-uuid"}, {"location_id": 2},
])
def test_validation(join_ticket, changes):
    assert join_ticket(**changes).status_code == 422


def test_public_ticket_does_not_leak_data(client, join_ticket):
    token = join_ticket().json()["token"]
    join_ticket(name="Otro comensal", phone="999888777")
    result = client.get(f"/api/public/tickets/{token}")
    assert set(result.json()) == {"token", "location_name", "name", "party_size", "status",
                                  "groups_ahead", "eta_min", "joined_at", "called_at", "deadline_at", "server_now"}
    assert "Otro comensal" not in result.text
    assert "987" not in result.text
    assert result.headers["cache-control"] == "no-store"
    assert client.get("/api/public/tickets/inventado").status_code == 404
    assert client.get(f"/api/public/tickets/{token.swapcase()}").status_code == 404


def test_join_blocked_while_the_previous_turn_is_alive(join_ticket, env, headers, client):
    """Mientras la espera sigue viva, el mismo teléfono no abre un segundo turno."""
    first = join_ticket()
    env["clock"][0] += timedelta(minutes=30)
    assert join_ticket().status_code == 409

    ticket_id = client.get("/api/host/queue", headers=headers).json()["rows"][0]["id"]
    client.post(f"/api/host/tickets/{ticket_id}/call", headers=headers)
    env["clock"][0] += timedelta(minutes=9)  # llamado, dentro de sus 10 minutos
    assert join_ticket().status_code == 409
    assert client.get(f"/api/public/tickets/{first.json()['token']}").json()["status"] == "called"


def test_join_replaces_the_turn_whose_call_already_expired(join_ticket, env, headers, client):
    """Pasados los 10 minutos del llamado, el teléfono vuelve a estar libre."""
    first = join_ticket()
    ticket_id = client.get("/api/host/queue", headers=headers).json()["rows"][0]["id"]
    client.post(f"/api/host/tickets/{ticket_id}/call", headers=headers)
    env["clock"][0] += timedelta(minutes=11)

    second = join_ticket()
    assert second.status_code == 201
    assert second.json()["token"] != first.json()["token"]
    assert client.get(f"/api/public/tickets/{first.json()['token']}").json()["status"] == "expired"
    with Session(env["engine"]) as session:
        expired = session.scalar(select(Ticket).where(Ticket.public_token == first.json()["token"]))
        assert (expired.active_key, expired.closed_at) == (None, env["clock"][0])
        event = session.scalar(select(TicketEvent).where(
            TicketEvent.ticket_id == expired.id, TicketEvent.type == "expired"))
        assert event.data["reason"] == "stale_on_rejoin"
        assert event.data["previous_status"] == "called"


def test_join_replaces_a_turn_forgotten_in_the_list(join_ticket, env):
    """Una espera olvidada tampoco bloquea el número para siempre."""
    first = join_ticket()
    env["clock"][0] += timedelta(minutes=119)
    assert join_ticket().status_code == 409

    env["clock"][0] += timedelta(minutes=2)  # pasa waiting_ttl_minutes (120)
    second = join_ticket()
    assert second.status_code == 201
    assert second.json()["groups_ahead"] == 0  # el olvidado ya no cuenta delante


def test_stale_replacement_rolls_back_everything_if_new_join_fails(
        join_ticket, env, headers, client):
    """No se pierde el turno anterior si falla crear el reemplazo."""
    first = join_ticket()
    ticket_id = client.get("/api/host/queue", headers=headers).json()["rows"][0]["id"]
    client.post(f"/api/host/tickets/{ticket_id}/call", headers=headers)
    env["clock"][0] += timedelta(minutes=11)

    def reject_joined_event(mapper, connection, target):
        if target.type == "joined":
            raise RuntimeError("Simulated joined event failure")

    sqlalchemy_event.listen(TicketEvent, "before_insert", reject_joined_event)
    try:
        assert join_ticket().status_code == 500
    finally:
        sqlalchemy_event.remove(TicketEvent, "before_insert", reject_joined_event)

    with Session(env["engine"]) as session:
        previous = session.scalar(select(Ticket).where(
            Ticket.public_token == first.json()["token"]))
        assert previous.status == "called"
        assert previous.active_key is not None
        assert previous.closed_at is None
        assert session.scalar(select(func.count()).select_from(Ticket)) == 1
        assert session.scalar(select(func.count()).select_from(TicketEvent).where(
            TicketEvent.type == "expired")) == 0
