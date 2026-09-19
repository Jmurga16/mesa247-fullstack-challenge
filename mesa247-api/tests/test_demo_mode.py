from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_demo_locations_lists_only_seeded_and_active(client, env):
    codes = [row["code"] for row in client.get("/api/demo/locations").json()]
    assert codes == ["terraza-lima", "vientos-lima", "casa-santiago"]

    from app.models import Location
    from sqlalchemy.orm import Session
    with Session(env["engine"]) as session:
        location = session.query(Location).filter_by(public_code="vientos-lima").one()
        location.is_active = False
        session.commit()
    assert "vientos-lima" not in [row["code"] for row in client.get("/api/demo/locations").json()]


def test_demo_tablet_opens_a_working_session(client):
    opened = client.post("/api/demo/locations/terraza-lima/tablet")
    assert opened.status_code == 200
    assert opened.json()["location_name"] == "La Terraza Azul"

    queue = client.get("/api/host/queue",
                       headers={"Authorization": f"Bearer {opened.json()['token']}"})
    assert queue.status_code == 200
    assert queue.json()["location"]["name"] == "La Terraza Azul"


def test_opening_again_revokes_the_previous_demo_tablet(client, env):
    first = client.post("/api/demo/locations/terraza-lima/tablet").json()["token"]
    second = client.post("/api/demo/locations/terraza-lima/tablet").json()["token"]

    assert client.get("/api/host/queue", headers={"Authorization": f"Bearer {first}"}).status_code == 401
    assert client.get("/api/host/queue", headers={"Authorization": f"Bearer {second}"}).status_code == 200
    # La sesión que reparte el seed es otra tablet: el modo demo no la toca.
    seeded = {"Authorization": f"Bearer {env['tokens']['terraza-lima']}"}
    assert client.get("/api/host/queue", headers=seeded).status_code == 200


def test_unknown_location_is_404(client):
    assert client.post("/api/demo/locations/no-existe/tablet").status_code == 404


def test_demo_mode_off_hides_the_routes(env):
    config = Settings(_env_file=None, database_url=str(env["engine"].url), demo_mode=False)
    with TestClient(create_app(config, env["engine"])) as off:
        assert off.get("/api/demo/locations").status_code == 404
        assert off.post("/api/demo/locations/terraza-lima/tablet").status_code == 404
        # Sin modo demo, la tablet sigue abriéndose con su token impreso.
        seeded = {"Authorization": f"Bearer {env['tokens']['terraza-lima']}"}
        assert off.get("/api/host/queue", headers=seeded).status_code == 200
