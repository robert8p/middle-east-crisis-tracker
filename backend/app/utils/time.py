from __future__ import annotations

from datetime import datetime, timedelta, timezone, UTC

from dateutil import parser


def utcnow_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = parser.parse(value)
        if dt.tzinfo:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt.replace(tzinfo=None)
    except Exception:
        return None


def hours_ago(hours: int) -> datetime:
    return utcnow_naive() - timedelta(hours=hours)