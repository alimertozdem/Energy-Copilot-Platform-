"""JSON-API job source — for boards that expose JSON instead of RSS.

Config-driven (data_path + field_map) so new JSON APIs are added in
sources.yml without code changes. Currently used for Arbeitnow
(Germany/EU job board, English-friendly).
"""
from __future__ import annotations

import hashlib
import html
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx

from .base import RawJob, to_utc_iso

logger = logging.getLogger(__name__)

_TAG_RE = re.compile(r"<[^>]+>")
_UA = "Mozilla/5.0 (compatible; EnergyLensBot/1.0; +https://github.com/alimertozdem)"


def _strip_html(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(_TAG_RE.sub(" ", s or ""))).strip()


def _dig(obj, path: str):
    cur = obj
    for part in path.split("."):
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur


class JSONAPISource:
    """Fetch a JSON job feed and map records to RawJob via a config field map."""

    def __init__(self, name: str, url: str, job_id_prefix: str,
                 data_path: str = "data", field_map: Optional[dict] = None):
        self.name = name
        self.url = url
        self.job_id_prefix = job_id_prefix
        self.data_path = data_path
        self.field_map = field_map or {}

    def fetch(self, lookback_hours: int) -> list[RawJob]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        fm = self.field_map
        try:
            resp = httpx.get(self.url, timeout=30, follow_redirects=True,
                             headers={"User-Agent": _UA, "Accept": "application/json"})
            resp.raise_for_status()
            payload = resp.json()
        except Exception as e:
            logger.warning("JSON source %s fetch/parse error: %s", self.name, e)
            return []

        records = _dig(payload, self.data_path) if self.data_path else payload
        if not isinstance(records, list):
            logger.warning("JSON source %s: data_path '%s' not a list", self.name, self.data_path)
            return []

        jobs: list[RawJob] = []
        for rec in records:
            if not isinstance(rec, dict):
                continue
            title = str(rec.get(fm.get("title", "title"), "") or "").strip()
            description = _strip_html(str(rec.get(fm.get("description", "description"), "") or ""))
            url = rec.get(fm.get("url", "url"))
            client = rec.get(fm.get("client_name", "company_name"))

            posted = None
            uk = fm.get("posted_unix")
            if uk and rec.get(uk) is not None:
                try:
                    posted = datetime.fromtimestamp(int(rec[uk]), tz=timezone.utc)
                except Exception:
                    posted = None
            if posted and posted < cutoff:
                continue
            if not title or not description:
                continue

            seed = str(url or rec.get("slug") or (title + str(client or "")))
            jid = f"{self.job_id_prefix}{hashlib.sha1(seed.encode('utf-8', errors='ignore')).hexdigest()[:14]}"
            jobs.append(RawJob(
                job_id=jid,
                source=f"json:{self.name}",
                title=title[:250],
                description=description[:6000],
                url=url,
                client_name=str(client)[:120] if client else None,
                posted_at=to_utc_iso(posted) if posted else None,
            ))

        logger.info("JSON %s returned %d items (lookback %dh)", self.name, len(jobs), lookback_hours)
        return jobs
