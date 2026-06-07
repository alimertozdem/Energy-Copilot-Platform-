"""Email IMAP job source — for Malt / Contra / LinkedIn / freelancermap alert emails.

Polls a Gmail (or any IMAP) inbox. Each platform has its own parser that
turns an email body into a RawJob. We add new parsers by registering them
in PARSER_REGISTRY.

Auth: pass username + Gmail app password via env. Never hardcode.
"""
from __future__ import annotations

import hashlib
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

from .base import RawJob, to_utc_iso

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Parsers — one per platform. Take (subject, body) -> Optional[RawJob fields].
# Each returns dict with {title, description, url, client_name} or None to skip.
# ─────────────────────────────────────────────────────────────────────────────

def parse_malt(subject: str, body: str) -> Optional[dict]:
    """Malt project alert emails."""
    # Malt subject usually: "New project for you: <title>" or "Nouveau projet pour vous : ..."
    title_m = re.search(r"(?:project for you|new project|nouveau projet)[:\-]\s*(.+)", subject, re.I)
    title = (title_m.group(1) if title_m else subject).strip()

    # Find a project URL
    url_m = re.search(r"https?://(?:www\.)?malt\.[a-z]+/[^\s\"'<>]+", body, re.I)

    # Best-effort: client name is sometimes in the body before "is looking for"
    client_m = re.search(r"([A-Z][\w&\.\- ]{2,40})\s+(?:is looking|cherche|recherche)", body)
    client = client_m.group(1).strip() if client_m else None

    return {
        "title": title,
        "description": body[:6000],
        "url": url_m.group(0) if url_m else None,
        "client_name": client,
    }


def parse_contra(subject: str, body: str) -> Optional[dict]:
    """Contra opportunity / digest emails."""
    title = subject.replace("New opportunity:", "").strip()
    url_m = re.search(r"https?://(?:www\.)?contra\.com/[^\s\"'<>]+", body, re.I)
    return {
        "title": title,
        "description": body[:6000],
        "url": url_m.group(0) if url_m else None,
        "client_name": None,
    }


def parse_linkedin(subject: str, body: str) -> Optional[dict]:
    """LinkedIn 'X new jobs in your saved search' emails.

    LinkedIn aggregates multiple jobs per email — we extract the first one
    with a meaningful title. Multi-job parsing is a future improvement.
    """
    # Try to grab the first job card title
    title_m = re.search(r"([\w&\.\- ]{8,100})\s*\n\s*(?:at|·)\s*([\w&\.\- ]{2,80})", body)
    if title_m:
        title = title_m.group(1).strip()
        client = title_m.group(2).strip()
    else:
        title = subject.replace("LinkedIn", "").strip()
        client = None

    url_m = re.search(r"https?://(?:www\.)?linkedin\.com/jobs/view/[^\s\"'<>]+", body, re.I)
    return {
        "title": title,
        "description": body[:6000],
        "url": url_m.group(0) if url_m else None,
        "client_name": client,
    }


def parse_freelancermap(subject: str, body: str) -> Optional[dict]:
    """freelancermap 'project agent' daily digest emails.

    The digest aggregates multiple projects. Like LinkedIn, we surface the
    first project link with the digest subject as title; the full body (all
    projects' text) is passed as description so the LLM still scores on the
    complete content. Multi-job splitting is a future improvement.
    """
    title = re.sub(r"(?i)freelancermap|project ?agent|projektagent|:|\|", " ", subject).strip()
    if not title:
        title = "freelancermap project alert"
    # freelancermap project URLs: /project/<slug>-<id> or /projekt/<...>
    url_m = re.search(r"https?://(?:www\.)?freelancermap\.com/(?:project|projekt)[^\s\"'<>]+", body, re.I)
    return {
        "title": title,
        "description": body[:6000],
        "url": url_m.group(0) if url_m else "https://www.freelancermap.com/project/",
        "client_name": None,
    }


PARSER_REGISTRY: dict[str, Callable[[str, str], Optional[dict]]] = {
    "malt": parse_malt,
    "contra": parse_contra,
    "linkedin": parse_linkedin,
    "freelancermap": parse_freelancermap,
}


# ─────────────────────────────────────────────────────────────────────────────
# Source
# ─────────────────────────────────────────────────────────────────────────────


class EmailIMAPSource:
    """Polls one IMAP account; each configured folder uses its named parser."""

    def __init__(
        self,
        name: str,
        imap_host: str,
        imap_port: int,
        username_env: str,
        password_env: str,
        folders: list[dict],
    ):
        self.name = name
        self.imap_host = imap_host
        self.imap_port = imap_port
        self.username = os.getenv(username_env)
        self.password = os.getenv(password_env)
        self.folders = folders  # [{name, parser, job_id_prefix}, ...]

    def fetch(self, lookback_hours: int) -> list[RawJob]:
        if not self.username or not self.password:
            logger.warning("IMAP source %s missing credentials; skipping", self.name)
            return []

        # Lazy import so this file is importable without the dep installed
        try:
            from imap_tools import AND, MailBox
        except ImportError:
            logger.error("imap_tools not installed; cannot fetch emails")
            return []

        cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        jobs: list[RawJob] = []

        with MailBox(self.imap_host, self.imap_port).login(self.username, self.password) as mb:
            for folder in self.folders:
                fname = folder["name"]
                parser_name = folder["parser"]
                prefix = folder["job_id_prefix"]
                parser = PARSER_REGISTRY.get(parser_name)
                if not parser:
                    logger.warning("No parser '%s' for folder %s", parser_name, fname)
                    continue

                try:
                    mb.folder.set(fname)
                except Exception as e:
                    logger.warning("Cannot open IMAP folder %s: %s", fname, e)
                    continue

                # Gmail labels appear as folders; fetch recent
                criteria = AND(date_gte=cutoff.date())
                for msg in mb.fetch(criteria, limit=100, reverse=True):
                    msg_dt = msg.date
                    if msg_dt and msg_dt.replace(tzinfo=timezone.utc) < cutoff:
                        continue
                    subj = msg.subject or ""
                    body = msg.text or msg.html or ""
                    parsed = parser(subj, body)
                    if not parsed or not parsed.get("title"):
                        continue

                    seed = f"{msg.uid}-{parser_name}"
                    jid = f"{prefix}{hashlib.sha1(seed.encode()).hexdigest()[:14]}"

                    jobs.append(RawJob(
                        job_id=jid,
                        source=f"email:{parser_name}",
                        title=parsed["title"][:250],
                        description=parsed["description"],
                        url=parsed.get("url"),
                        client_name=parsed.get("client_name"),
                        posted_at=to_utc_iso(msg_dt) if msg_dt else None,
                    ))

        logger.info("Email %s returned %d items", self.name, len(jobs))
        return jobs
