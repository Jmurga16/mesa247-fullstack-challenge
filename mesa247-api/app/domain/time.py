from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo


def now() -> datetime:
    return datetime.now(UTC)


def service_date(location, instant: datetime):
    return (instant.astimezone(ZoneInfo(location.timezone))
            - timedelta(hours=location.day_cutoff_hour)).date()
