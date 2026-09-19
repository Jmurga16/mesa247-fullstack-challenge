import argparse
import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import hash_token
from app.config import settings
from app.db import build_engine
from app.domain.time import now
from app.models import Base, HostDevice, Location

# Los tres locales del piloto del enunciado: dos en Lima y uno en Santiago.
LOCATIONS = [
    ("terraza-lima", "La Terraza Azul", "PE", "America/Lima"),
    ("vientos-lima", "Cuatro Vientos", "PE", "America/Lima"),
    ("casa-santiago", "Casa Mediterránea", "CL", "America/Santiago"),
]


def seed(session: Session, rotate_tokens=False):
    links = []
    for code, name, country, timezone in LOCATIONS:
        location = session.scalar(select(Location).where(Location.public_code == code))
        if location is None:
            location = Location(public_code=code, name=name, country_code=country, timezone=timezone)
            session.add(location)
            session.flush()
        else:
            # Renombrar un local de demo no debe obligar a borrar la base.
            location.name, location.country_code, location.timezone = name, country, timezone
            location.is_active = True
        devices = session.scalars(select(HostDevice).where(
            HostDevice.location_id == location.id, HostDevice.label == "Tablet demo",
            HostDevice.revoked_at.is_(None))).all()
        token = None
        if not devices or rotate_tokens:
            for device in devices:
                device.revoked_at = now()
            token = secrets.token_urlsafe(32)
            session.add(HostDevice(location_id=location.id, label="Tablet demo", token_hash=hash_token(token)))
        links.append((code, token))
    session.commit()
    return links


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Datos demo; no crea comensales.")
    parser.add_argument("--rotate-tokens", action="store_true", help="Revoca y reemplaza los tokens demo existentes")
    args = parser.parse_args()
    engine = build_engine(settings)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        for code, token in seed(session, args.rotate_tokens):
            print(f"\n{code}\n  QR: {settings.web_base_url}/q/{code}")
            if token:
                print(f"  Tablet: {settings.web_base_url}/host?token={token}")
                print(f"  Bearer: {token}")
            else:
                print("  Token existente: usa el guardado o ejecuta --rotate-tokens para reemplazarlo.")
    engine.dispose()
