from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.queue import apply_transition
from app.errors import ApiError
from app.models import Ticket, TicketEvent


def race(env, actions):
    barrier = Barrier(2)
    def execute(action):
        with Session(env["engine"]) as session:
            ticket = session.scalar(select(Ticket))
            barrier.wait(timeout=10)
            try:
                _, changed = apply_transition(session, ticket, action, "host_device:1", env["clock"][0])
                return 200, changed
            except ApiError as exc:
                return exc.status, False
    with ThreadPoolExecutor(max_workers=2) as pool:
        return list(pool.map(execute, actions))


def test_two_connections_call_once(env, join_ticket):
    join_ticket()
    assert sorted(race(env, ["call", "call"])) == [(200, False), (200, True)]
    with Session(env["engine"]) as session:
        assert session.scalar(select(Ticket)).call_count == 1
        assert list(session.scalars(select(TicketEvent.type))).count("called") == 1


def test_two_connections_call_and_seat_conflict(env, join_ticket):
    join_ticket()
    assert sorted(race(env, ["call", "seat"])) == [(200, True), (409, False)]


def test_simultaneous_join_same_request(client, join_ticket):
    request_id = str(uuid4())
    barrier = Barrier(2)
    def execute(_):
        barrier.wait(timeout=10)
        return join_ticket(request_id=request_id)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(execute, range(2)))
    assert sorted(r.status_code for r in results) == [200, 201]
    assert results[0].json()["token"] == results[1].json()["token"]


def test_simultaneous_replacement_of_stale_turn_creates_one_ticket(
        client, join_ticket, headers, env):
    join_ticket()
    ticket_id = client.get("/api/host/queue", headers=headers).json()["rows"][0]["id"]
    client.post(f"/api/host/tickets/{ticket_id}/call", headers=headers)
    env["clock"][0] += timedelta(minutes=11)
    barrier = Barrier(2)

    def execute(_):
        barrier.wait(timeout=10)
        return join_ticket(request_id=str(uuid4()))

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(execute, range(2)))

    assert sorted(response.status_code for response in results) == [201, 409]
    with Session(env["engine"]) as session:
        assert session.scalar(select(func.count()).select_from(Ticket)) == 2
        assert session.scalar(select(func.count()).select_from(Ticket).where(
            Ticket.status == "expired")) == 1
        assert session.scalar(select(func.count()).select_from(Ticket).where(
            Ticket.status == "waiting")) == 1
        assert session.scalar(select(func.count()).select_from(TicketEvent).where(
            TicketEvent.type == "expired")) == 1
