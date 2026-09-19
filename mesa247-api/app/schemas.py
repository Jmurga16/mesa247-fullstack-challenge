from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, UUID4

Status = Literal["waiting", "called", "seated", "cancelled", "no_show", "removed", "expired"]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)]
Phone = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)]


class JoinRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: UUID4
    name: Name
    phone: Phone
    party_size: int = Field(ge=1, le=50, strict=True)


class LookupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    phone: Phone


class LocationPublic(BaseModel):
    code: str
    name: str
    country: str
    phone_prefix: str
    max_party_size: int


class TicketPublic(BaseModel):
    token: str
    location_name: str
    name: str
    party_size: int
    status: Status
    groups_ahead: int | None
    eta_min: int | None
    joined_at: datetime
    called_at: datetime | None
    deadline_at: datetime | None
    server_now: datetime


class HostRow(BaseModel):
    id: int
    name: str
    party_size: int
    status: Status
    waiting_min: int
    called_at: datetime | None
    deadline_at: datetime | None
    on_the_way: bool
    overdue: bool
    notify_state: Literal["none", "sent", "failed"]


class HostLocation(BaseModel):
    name: str
    timezone: str


class HostQueue(BaseModel):
    location: HostLocation
    service_date: date
    waiting_count: int
    avg_wait_min: float | None
    server_now: datetime
    rows: list[HostRow]


class ErrorResponse(BaseModel):
    error: str
    message: str
