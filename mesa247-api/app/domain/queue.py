import math
import secrets
from datetime import datetime, timedelta

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.phones import field_error, normalize_phone
from app.domain.time import service_date
from app.errors import ApiError, not_found
from app.models import Location, Ticket, TicketEvent
from app.schemas import HostRow, JoinRequest, TicketPublic

TERMINAL = {"seated", "cancelled", "no_show", "removed", "expired"}
# action: allowed sources, target, event
TRANSITIONS = {
    "call": ({"waiting"}, "called", "called"),
    "seat": ({"waiting", "called"}, "seated", "seated"),
    "no-show": ({"called"}, "no_show", "no_show"),
    "leave": ({"waiting"}, "cancelled", "left"),
    "remove": ({"waiting", "called"}, "removed", "removed"),
    "cancel": ({"waiting", "called"}, "cancelled", "cancelled"),
    "expire": ({"waiting", "called"}, "expired", "expired"),  # sin ruta HTTP: lo dispara el alta
}


def add_event(session, ticket, kind, actor, instant, data=None):
    session.add(TicketEvent(ticket_id=ticket.id, location_id=ticket.location_id,
                            type=kind, actor=actor, created_at=instant, data=data or {}))


def active_key(location_id, day, phone):
    return f"{location_id}:{day.isoformat()}:{phone}"


def is_stale(ticket: Ticket, location: Location, instant: datetime) -> bool:
    """¿Este turno dejó de ser una espera real y ya no debe bloquear al teléfono?

    El día entero era una ventana demasiado ancha: quien perdió su llamado a las
    20:10 tenía el número bloqueado hasta el cierre. Se mira la hora, no la fecha.
    """
    if ticket.status == "called":
        return instant > ticket.called_at + timedelta(minutes=location.call_grace_minutes)
    if ticket.status == "waiting":
        return instant > ticket.joined_at + timedelta(minutes=location.waiting_ttl_minutes)
    return False


def release_if_stale(session: Session, location: Location, key: str, instant: datetime) -> None:
    """Prepara la caducidad sin commit; el alta nueva confirma ambas cosas juntas."""
    ticket = session.scalar(select(Ticket).where(Ticket.active_key == key))
    if ticket is None or not is_stale(ticket, location, instant):
        return
    apply_transition(session, ticket, "expire", "system", instant,
                     {"reason": "stale_on_rejoin", "previous_status": ticket.status}, commit=False)


def groups_ahead(session: Session, ticket: Ticket) -> int:
    return session.scalar(select(func.count()).select_from(Ticket).where(
        Ticket.location_id == ticket.location_id, Ticket.service_date == ticket.service_date,
        Ticket.status == "waiting",
        or_(Ticket.sort_key < ticket.sort_key,
            and_(Ticket.sort_key == ticket.sort_key, Ticket.id < ticket.id))))


def eta(ahead: int, minutes_per_party: int) -> int:
    return max(5, math.ceil((ahead + 1) * minutes_per_party / 5) * 5)


def join(session: Session, location: Location, body: JoinRequest, instant: datetime):
    request_query = select(Ticket).where(Ticket.location_id == location.id,
                                        Ticket.client_request_id == str(body.request_id))
    existing = session.scalar(request_query)
    if existing:
        return existing, False
    if body.party_size > location.max_party_size:
        field_error("party_size", f"El máximo en este local es {location.max_party_size} personas.")
    phone = normalize_phone(body.phone, location.country_code)
    day = service_date(location, instant)
    key = active_key(location.id, day, phone)
    ticket = Ticket(public_token=secrets.token_urlsafe(24), location_id=location.id,
                    service_date=day, source="qr", customer_name=body.name,
                    phone_e164=phone, party_size=body.party_size, status="waiting",
                    sort_key=int(instant.timestamp() * 1000), quoted_wait_min=0,
                    position_at_join=0, joined_at=instant, updated_at=instant,
                    consent_at=instant, active_key=key, client_request_id=str(body.request_id))
    try:
        # La caducidad anterior, su evento, el turno nuevo y joined son una transacción.
        release_if_stale(session, location, key, instant)
        session.add(ticket)
        session.flush()
        ahead = groups_ahead(session, ticket)
        ticket.position_at_join = ahead + 1
        ticket.quoted_wait_min = eta(ahead, location.minutes_per_party)
        add_event(session, ticket, "joined", "customer", instant)
        session.commit()
    except IntegrityError:
        session.rollback()
        existing = session.scalar(request_query)
        if existing:
            return existing, False
        if session.scalar(select(Ticket.id).where(Ticket.active_key == key)):
            raise ApiError(409, "already_in_queue", "Ya tienes un turno activo en este local. "
                           "Usa 'Ya estoy en la lista de espera' para volver a él.")
        raise
    except Exception:
        session.rollback()
        raise
    return ticket, True


def apply_transition(session: Session, ticket: Ticket, action: str, actor: str, instant: datetime,
                     data=None, *, commit=True):
    sources, target, kind = TRANSITIONS[action]
    repeat = {target} | ({"no_show"} if action == "cancel" else set())
    observed = ticket.status
    if observed in repeat:
        return ticket, False
    if observed not in sources:
        raise ApiError(409, "invalid_transition", "Este turno ya no permite esa acción. Actualiza la lista.")
    values = {"status": target, "updated_at": instant}
    if target in TERMINAL:
        values.update(closed_at=instant, active_key=None)
    if target == "called":
        values.update(called_at=instant, call_count=Ticket.call_count + 1)
    if target == "seated":
        values["seated_at"] = instant
    # Compare the observed status, not all allowed sources: detects an intervening call.
    result = session.execute(update(Ticket).where(
        Ticket.id == ticket.id, Ticket.location_id == ticket.location_id,
        Ticket.status == observed).values(**values).execution_options(synchronize_session=False))
    if result.rowcount == 0:
        session.rollback()  # discard snapshots before rereading, including on MySQL
        session.refresh(ticket)
        if ticket.status in repeat:
            return ticket, False
        raise ApiError(409, "invalid_transition", "Otro anfitrión ya lo atendió. Actualiza la lista.")
    try:
        add_event(session, ticket, kind, actor, instant, data)
        if commit:
            session.commit()
        else:
            session.flush()
    except Exception:
        session.rollback()
        raise
    session.refresh(ticket)
    return ticket, True


def deadline(ticket, location):
    if ticket.status == "called" and ticket.called_at:
        return ticket.called_at + timedelta(minutes=location.call_grace_minutes)
    return None


def public_ticket(session, ticket, location, instant):
    ahead = groups_ahead(session, ticket) if ticket.status == "waiting" else None
    return TicketPublic(token=ticket.public_token, location_name=location.name,
                        name=ticket.customer_name, party_size=ticket.party_size, status=ticket.status,
                        groups_ahead=ahead, eta_min=eta(ahead, location.minutes_per_party) if ahead is not None else None,
                        joined_at=ticket.joined_at, called_at=ticket.called_at,
                        deadline_at=deadline(ticket, location), server_now=instant)


def host_row(session, ticket, location, instant):
    notification = session.scalar(select(TicketEvent.type).where(
        TicketEvent.ticket_id == ticket.id,
        TicketEvent.type.in_(["notification_sent", "notification_failed"]))
        .order_by(TicketEvent.id.desc()).limit(1))
    due = deadline(ticket, location)
    return HostRow(id=ticket.id, name=ticket.customer_name, party_size=ticket.party_size,
                   status=ticket.status, waiting_min=max(0, int((instant - ticket.joined_at).total_seconds() // 60)),
                   called_at=ticket.called_at, deadline_at=due,
                   on_the_way=ticket.on_the_way_at is not None, overdue=due is not None and instant > due,
                   notify_state=notification.removeprefix("notification_") if notification else "none")


def avg_wait_min(session, location_id, day):
    rows = session.execute(select(Ticket.joined_at, Ticket.seated_at).where(
        Ticket.location_id == location_id, Ticket.service_date == day, Ticket.status == "seated")).all()
    return round(sum((seat - joined).total_seconds() / 60 for joined, seat in rows) / len(rows), 1) if rows else None


def get_location(session, code):
    location = session.scalar(select(Location).where(Location.public_code == code, Location.is_active.is_(True)))
    if not location:
        raise not_found()
    return location


def get_public_ticket(session, token):
    ticket = session.scalar(select(Ticket).where(Ticket.public_token == token))
    if not ticket:
        raise not_found()
    return ticket
