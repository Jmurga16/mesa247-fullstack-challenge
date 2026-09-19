from datetime import UTC, date, datetime

from sqlalchemy import (JSON, BigInteger, Boolean, CheckConstraint, Date, DateTime,
                        ForeignKey, Index, Integer, String, UniqueConstraint)
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from app.domain.time import now


class UTCDateTime(TypeDecorator):
    impl = DateTime
    cache_ok = True

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(DATETIME(fsp=6) if dialect.name == "mysql" else DateTime())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("Business timestamps must have a timezone")
        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(self, value, dialect):
        return value.replace(tzinfo=UTC) if value is not None else None


def opaque(length):
    return String(length).with_variant(String(length, collation="utf8mb4_bin"), "mysql")


class Base(DeclarativeBase):
    pass


class Location(Base):
    __tablename__ = "locations"
    __table_args__ = (
        CheckConstraint("day_cutoff_hour BETWEEN 0 AND 23"),
        CheckConstraint("max_party_size BETWEEN 1 AND 50"),
        CheckConstraint("minutes_per_party > 0 AND call_grace_minutes > 0"),
        CheckConstraint("waiting_ttl_minutes > 0"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    external_ref: Mapped[str | None] = mapped_column(String(64), unique=True)
    public_code: Mapped[str] = mapped_column(opaque(16), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    country_code: Mapped[str] = mapped_column(String(2))
    timezone: Mapped[str] = mapped_column(String(64))
    day_cutoff_hour: Mapped[int] = mapped_column(default=5)
    minutes_per_party: Mapped[int] = mapped_column(default=4)
    call_grace_minutes: Mapped[int] = mapped_column(default=10)
    # Tras esta espera un turno deja de bloquear al teléfono: ver queue.is_stale.
    waiting_ttl_minutes: Mapped[int] = mapped_column(default=120)
    max_party_size: Mapped[int] = mapped_column(default=20)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now)


class HostDevice(Base):
    __tablename__ = "host_devices"
    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), index=True)
    label: Mapped[str] = mapped_column(String(60))
    token_hash: Mapped[str] = mapped_column(opaque(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now)
    last_seen_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    revoked_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = (
        UniqueConstraint("location_id", "client_request_id", name="uq_ticket_request"),
        CheckConstraint("party_size BETWEEN 1 AND 50"),
        CheckConstraint("status IN ('waiting','called','seated','cancelled','no_show','removed','expired')"),
        CheckConstraint("source IN ('qr','host')"),
        Index("ix_ticket_queue", "location_id", "service_date", "status", "sort_key", "id"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_token: Mapped[str] = mapped_column(opaque(32), unique=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"))
    service_date: Mapped[date] = mapped_column(Date)
    source: Mapped[str] = mapped_column(String(8))
    customer_name: Mapped[str] = mapped_column(String(40))
    phone_e164: Mapped[str | None] = mapped_column(String(16))
    party_size: Mapped[int]
    status: Mapped[str] = mapped_column(String(12), default="waiting")
    sort_key: Mapped[int] = mapped_column(BigInteger)
    quoted_wait_min: Mapped[int]
    position_at_join: Mapped[int]
    call_count: Mapped[int] = mapped_column(default=0)
    joined_at: Mapped[datetime] = mapped_column(UTCDateTime())
    called_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    on_the_way_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    seated_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    closed_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime())
    consent_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    active_key: Mapped[str | None] = mapped_column(String(64), unique=True)
    client_request_id: Mapped[str] = mapped_column(String(36))


class TicketEvent(Base):
    __tablename__ = "ticket_events"
    __table_args__ = (
        Index("ix_event_ticket_time", "ticket_id", "created_at"),
        Index("ix_event_location_time", "location_id", "created_at"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"))
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"))
    type: Mapped[str] = mapped_column(String(32))
    actor: Mapped[str] = mapped_column(String(64))
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime())
