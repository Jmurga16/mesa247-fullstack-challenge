import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import hash_token
from app.config import settings
from app.db import get_session
from app.domain.queue import get_location
from app.domain.time import now
from app.errors import ApiError
from app.models import HostDevice, Location
from app.schemas import DemoLocation, DemoTablet

router = APIRouter(prefix="/api/demo", tags=["demo"])

# La tablet que abre la web de demo se distingue de la que imprime el seed: así
# el modo demo nunca revoca la sesión real de un local.
WEB_TABLET_LABEL = "Tablet demo (web)"


def demo_enabled(request: Request) -> None:
    """
    Andamiaje de la demo, no producto: con `DEMO_MODE=false` estas rutas dejan de
    existir y la aplicación entera sigue funcionando (la tablet se abre con su
    enlace, como en 09 § 2.1 O12). Apagado responde 404 y no 403, igual que el
    resto de la API: no se confirma que la ruta exista.
    """
    config = getattr(request.app.state, "config", settings)
    if not config.demo_mode:
        raise ApiError(404, "not_found", "No encontramos esa ruta.")


@router.get("/locations", response_model=list[DemoLocation], dependencies=[Depends(demo_enabled)])
def demo_locations(session: Session = Depends(get_session)):
    """Los locales que existen de verdad en esta base, para no ofrecer puertas muertas."""
    rows = session.scalars(select(Location).where(Location.is_active.is_(True)).order_by(Location.id)).all()
    return [DemoLocation(code=row.public_code, name=row.name, timezone=row.timezone) for row in rows]


@router.post("/locations/{code}/tablet", response_model=DemoTablet,
             dependencies=[Depends(demo_enabled)])
def open_demo_tablet(code: str, session: Session = Depends(get_session),
                     instant: datetime = Depends(now)):
    """
    Abre la tablet de un local sin pasar por el token impreso en consola: quien
    prueba la aplicación no tiene por qué manejar credenciales. Cada apertura
    revoca la anterior de ese local, de modo que solo hay una sesión de demo viva
    por local y el token sigue siendo opaco y revocable como cualquier otro.
    """
    location = get_location(session, code)
    for device in session.scalars(select(HostDevice).where(
            HostDevice.location_id == location.id, HostDevice.label == WEB_TABLET_LABEL,
            HostDevice.revoked_at.is_(None))):
        device.revoked_at = instant
    token = secrets.token_urlsafe(32)
    session.add(HostDevice(location_id=location.id, label=WEB_TABLET_LABEL,
                           token_hash=hash_token(token)))
    session.commit()
    return DemoTablet(token=token, location_name=location.name)
