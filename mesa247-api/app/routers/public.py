from datetime import datetime

import phonenumbers
from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.domain.phones import normalize_phone
from app.domain.queue import (active_key, apply_transition, get_location, get_public_ticket,
                              join, public_ticket)
from app.domain.time import now, service_date
from app.errors import ApiError
from app.models import Location, Ticket
from app.schemas import JoinRequest, LocationPublic, LookupRequest, TicketPublic

router = APIRouter(prefix="/api/public", tags=["public"])


@router.get("/locations/{code}", response_model=LocationPublic)
def location_info(code: str, session: Session = Depends(get_session)):
    location = get_location(session, code)
    return LocationPublic(code=location.public_code, name=location.name, country=location.country_code,
                          phone_prefix=f"+{phonenumbers.country_code_for_region(location.country_code)}",
                          max_party_size=location.max_party_size)


@router.post("/locations/{code}/tickets", response_model=TicketPublic, status_code=201,
             responses={200: {"model": TicketPublic, "description": "Reintento de la misma solicitud"}})
def join_queue(code: str, body: JoinRequest, response: Response,
               session: Session = Depends(get_session), instant: datetime = Depends(now)):
    location = get_location(session, code)
    ticket, created = join(session, location, body, instant)
    response.status_code = 201 if created else 200
    return public_ticket(session, ticket, location, instant)


@router.post("/locations/{code}/lookup", response_model=TicketPublic)
def lookup(code: str, body: LookupRequest, session: Session = Depends(get_session),
           instant: datetime = Depends(now)):
    location = get_location(session, code)
    phone = normalize_phone(body.phone, location.country_code)
    day = service_date(location, instant)
    ticket = session.scalar(select(Ticket).where(
        Ticket.active_key == active_key(location.id, day, phone),
        Ticket.location_id == location.id, Ticket.service_date == day,
        Ticket.status.in_(["waiting", "called"])))
    if not ticket:
        raise ApiError(404, "not_found", "No encontramos una espera activa con ese número en este local hoy. "
                       "Si acabas de anotarte revisa el número; si no, vuelve a unirte.")
    return public_ticket(session, ticket, location, instant)


@router.get("/tickets/{token}", response_model=TicketPublic)
def ticket_info(token: str, session: Session = Depends(get_session), instant: datetime = Depends(now)):
    ticket = get_public_ticket(session, token)
    return public_ticket(session, ticket, session.get(Location, ticket.location_id), instant)


@router.post("/tickets/{token}/cancel", response_model=TicketPublic)
def cancel(token: str, session: Session = Depends(get_session), instant: datetime = Depends(now)):
    ticket = get_public_ticket(session, token)
    ticket, _ = apply_transition(session, ticket, "cancel", "customer", instant)
    return public_ticket(session, ticket, session.get(Location, ticket.location_id), instant)
