import hashlib
from dataclasses import dataclass
from datetime import datetime

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.domain.time import now
from app.errors import ApiError
from app.models import HostDevice, Location

bearer = HTTPBearer(auto_error=False)


def hash_token(raw: str) -> str:
    # Credencial opaca: se guarda solo el resumen, nunca el token.
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class HostContext:
    device: HostDevice
    location: Location


def unauthorized():
    return ApiError(401, "unauthorized",
                    "Esta tablet no tiene una sesión válida. Vuelve a abrir el enlace del local.")


def get_host(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), session: Session = Depends(get_session),
             instant: datetime = Depends(now)) -> HostContext:
    # El local sale del token, nunca del cuerpo ni de la query.
    if credentials is None or not credentials.credentials.strip():
        raise unauthorized()
    token = credentials.credentials.strip()
    device = session.scalar(select(HostDevice).where(
        HostDevice.token_hash == hash_token(token), HostDevice.revoked_at.is_(None)))
    if device is None:
        raise unauthorized()
    location = session.get(Location, device.location_id)
    if location is None or not location.is_active:
        raise unauthorized()
    device.last_seen_at = instant
    session.commit()
    return HostContext(device=device, location=location)
