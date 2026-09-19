from datetime import timedelta

from sqlalchemy.orm import Session

from app.domain.queue import apply_transition
from app.models import Ticket

PHONES = ["987654321", "999888777", "988777666", "955444333", "977666555", "944333222"]


def report(client, headers, **params):
    result = client.get("/api/host/report", headers=headers, params=params)
    assert result.status_code == 200
    return result.json()


def queue_ids(client, headers):
    return [row["id"] for row in client.get("/api/host/queue", headers=headers).json()["rows"]]


def test_report_counts_outcomes_and_holds_the_invariant(client, join_ticket, headers, env):
    sizes = [4, 2, 6, 2, 3, 5]
    for phone, size in zip(PHONES, sizes):
        join_ticket(phone=phone, party_size=size)
    ids = queue_ids(client, headers)
    env["clock"][0] += timedelta(minutes=20)
    # Dos desenlaces confirmados por el anfitrión y uno por el comensal.
    client.post(f"/api/host/tickets/{ids[0]}/seat", headers=headers)
    client.post(f"/api/host/tickets/{ids[1]}/call", headers=headers)
    client.post(f"/api/host/tickets/{ids[1]}/no-show", headers=headers)
    client.post(f"/api/host/tickets/{ids[2]}/leave", headers=headers)
    # Cierre administrativo: uno caducado sin llamado y otro ya llamado.
    client.post(f"/api/host/tickets/{ids[3]}/call", headers=headers)
    with Session(env["engine"]) as session:
        for ident in (ids[3], ids[4]):
            apply_transition(session, session.get(Ticket, ident), "expire", "system", env["clock"][0])
    # El sexto sigue esperando: el día no ha cerrado.
    body = report(client, headers)
    assert body["joined"] == 6
    assert body["seated"] == 1
    assert body["left_before_seating"] == 2   # el que se fue y el caducado sin llamado
    assert body["no_show"] == 2               # el no vino y el caducado tras el llamado
    assert body["pending"] == 1
    assert body["expired"] == 2
    assert body["avg_wait_min"] == 20
    assert body["joined_guests"] == sum(sizes)
    assert body["seated_guests"] == 4
    assert body["location"]["name"] and body["service_date"] and body["server_now"]
    assert body["joined"] == (body["seated"] + body["left_before_seating"]
                              + body["no_show"] + body["pending"])


def test_report_ignores_removed_and_reports_no_average_without_seated(client, join_ticket, headers):
    join_ticket(phone=PHONES[0])
    join_ticket(phone=PHONES[1])
    ids = queue_ids(client, headers)
    client.post(f"/api/host/tickets/{ids[0]}/remove", headers=headers)
    body = report(client, headers)
    assert body["joined"] == 1 and body["pending"] == 1
    # "Sin datos" y "0 minutos" no son lo mismo y no se muestran igual (04 § 6).
    assert body["avg_wait_min"] is None


def test_report_is_isolated_by_location_and_by_day(client, join_ticket, headers, env):
    join_ticket()
    join_ticket(code="vientos-lima")
    other_day = (env["clock"][0] - timedelta(days=1)).date().isoformat()
    assert report(client, headers)["joined"] == 1
    assert report(client, headers, date=other_day)["joined"] == 0
    assert report(client, headers, date=other_day)["service_date"] == other_day


def test_report_requires_a_tablet_session(client):
    assert client.get("/api/host/report").status_code == 401
    assert client.get("/api/host/report", headers={"Authorization": "Bearer nope"}).status_code == 401
