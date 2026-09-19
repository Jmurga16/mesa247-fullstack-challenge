from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import HostContext, get_host
from app.db import get_session
from app.domain.queue import apply_transition, avg_wait_min, host_row
from app.domain.time import now, service_date
from app.errors import not_found
from app.models import Ticket
from app.notifier import Notifier, get_notifier, notify_called
from app.schemas import HostQueue, HostRow

router = APIRouter(prefix="/api/host", tags=["host"])


@router.get("/queue", response_model=HostQueue)
def queue(host: HostContext = Depends(get_host), session: Session = Depends(get_session),
          instant: datetime = Depends(now)):
    location = host.location
    day = service_date(location, instant)
    tickets = session.scalars(select(Ticket).where(
        Ticket.location_id == location.id, Ticket.service_date == day,
        Ticket.status.in_(["waiting", "called"])).order_by(Ticket.sort_key, Ticket.id)).all()
    return HostQueue(location={"name": location.name, "timezone": location.timezone},
                     service_date=day, waiting_count=sum(t.status == "waiting" for t in tickets),
                     avg_wait_min=avg_wait_min(session, location.id, day), server_now=instant,
                     rows=[host_row(session, t, location, instant) for t in tickets])


def action_endpoint(action):
    def perform(ticket_id: int, host: HostContext = Depends(get_host),
                session: Session = Depends(get_session), instant: datetime = Depends(now),
                notifier: Notifier = Depends(get_notifier)):
        ticket = session.scalar(select(Ticket).where(
            Ticket.id == ticket_id, Ticket.location_id == host.location.id))
        if not ticket:
            raise not_found()
        ticket, changed = apply_transition(session, ticket, action, f"host_device:{host.device.id}", instant)
        if action == "call" and changed:
            notify_called(session, ticket, notifier, instant)
        return host_row(session, ticket, host.location, instant)
    perform.__name__ = action.replace("-", "_")
    return perform


for action in ("call", "seat", "no-show", "leave", "remove"):
    router.add_api_route("/tickets/{ticket_id}/" + action, action_endpoint(action),
                         methods=["POST"], response_model=HostRow)
