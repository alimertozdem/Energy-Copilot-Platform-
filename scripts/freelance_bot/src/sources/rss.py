"""RSS-based job source.

Generic RSS/Atom reader (feedparser). A browser-like User-Agent is set so
boards that block default bot agents (e.g. RemoteOK) still serve the feed.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import feedparser

from .base import RawJob, to_utc_iso

logger = logging.getLogger(__name__)

_UA = "Mozilla/5.0 (compatible; EnergyLensBot/1.0; +https://github.com/alimertozdem)"


class RSSSource:
    """A single RSS/Atom feed."""

    def __init__(self, name: str, url: str, job_id_prefix: str):
        self.name = name
        self.url = url
        self.job_id_prefix = job_id_prefix

    def fetch(self, lookback_hours: int) -> list[RawJob]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        feed = feedparser.parse(self.url, agent=_UA)

        if feed.bozo and not feed.entries:
            logger.warning("RSS feed %s parse error: %s", self.url, feed.bozo_exception)
            return []

        jobs: list[RawJob] = []
        for entry in feed.entries:
            posted = _entry_datetime(entry)
            if posted and posted < cutoff:
                continue

            job_id = self._make_job_id(entry)
            title = (entry.get("title") or "").strip()
            description = (entry.get("summary") or entry.get("description") or "").strip()
            url = entry.get("link")
            if not title or not description:
                continue

            jobs.append(RawJob(
                job_id=job_id,
                source=f"rss:{self.name}",
                title=title,
                description=description,
                url=url,
                client_name=entry.get("author"),
                posted_at=to_utc_iso(posted) if posted else None,
            ))

        logger.info("RSS %s returned %d items (lookback %dh)", self.name, len(jobs), lookback_hours)
        return jobs

    def _make_job_id(self, entry) -> str:
        seed = entry.get("id") or entry.get("guid") or (entry.get("link") or "") + (entry.get("title") or "")
        h = hashlib.sha1(seed.encode("utf-8", errors="ignore")).hexdigest()[:14]
        return f"{self.job_id_prefix}{h}"


def _entry_datetime(entry) -> Optional[datetime]:
    for key in ("published_parsed", "updated_parsed", "created_parsed"):
        t = entry.get(key)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return None
