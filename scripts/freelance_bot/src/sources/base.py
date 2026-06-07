"""Common types for job sources."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Protocol


@dataclass
class RawJob:
    """What a source returns. Storage layer normalizes into JobRecord."""
    job_id: str
    source: str            # 'rss:freelance.de' | 'email:malt' | ...
    title: str
    description: str
    url: Optional[str] = None
    client_name: Optional[str] = None
    posted_at: Optional[str] = None  # ISO 8601


class JobSource(Protocol):
    """Anything that can yield jobs implements this interface."""

    name: str

    def fetch(self, lookback_hours: int) -> list[RawJob]:
        ...


def to_utc_iso(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")
