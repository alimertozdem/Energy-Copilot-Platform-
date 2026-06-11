"""Email IMAP job source — for Malt / Contra / LinkedIn / freelancermap alert emails.

Polls a Gmail (or any IMAP) inbox. Each platform has its own parser that turns
an email body into ONE OR MORE RawJobs.

Alert emails from LinkedIn and freelancermap bundle MANY postings into a single
email. Older versions collapsed the whole email into one useless item whose link
pointed at the saved-search page, not a real posting. Parsers now return a LIST
of jobs — each with its own title and a direct link — so the digest shows real,
clickable jobs.

Auth: pass username + Gmail app password via env. Never hardcode.
"""
from __future__ import annotations

import hashlib
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Callable
from urllib.parse import urlparse, urlunparse

from .base import RawJob, to_utc_iso

logger = logging.getLogger(__name__)

try:
    from bs4 import BeautifulSoup
except ImportError:  # bs4 is a declared dependency; degrade gracefully if absent
    BeautifulSoup = None


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _soup(body: str):
    if BeautifulSoup is None or not body:
        return None
    try:
        return BeautifulSoup(body, "html.parser")
    except Exception:
        return None


def _clean_url(href: str) -> str:
    """Drop query/fragment (tracking params) to get a canonical, dedup-able URL."""
    try:
        p = urlparse(href)
        return urlunparse((p.scheme, p.netloc, p.path, "", "", ""))
    except Exception:
        return href


def _ws(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def _plain(soup, body: str) -> str:
    return (soup.get_text(" ") if soup is not None else body)[:6000]


# ─────────────────────────────────────────────────────────────────────────────
# Parsers — each returns list[dict]; dict = {title, description, url, client_name}
# ─────────────────────────────────────────────────────────────────────────────

def parse_linkedin(subject: str, body: str) -> list[dict]:
    """LinkedIn 'N new jobs in your saved search' emails bundle many postings.

    Extract each job card: anchor text = title, /jobs/view/<id> = direct link.
    Falls back to a single email-level item if no cards are found.
    """
    jobs: list[dict] = []
    seen: set[str] = set()
    soup = _soup(body)
    if soup is not None:
        for a in soup.find_all("a", href=True):
            m = re.search(r"/jobs/view/(\d+)", a["href"])
            if not m:
                continue
            jid = m.group(1)
            if jid in seen:
                continue
            title = _ws(a.get_text())
            if len(title) < 3:
                continue
            seen.add(jid)
            context = title
            container = a.find_parent(["td", "tr", "div", "table"])
            if container is not None:
                ctx = _ws(container.get_text(" "))
                if len(ctx) > len(title):
                    context = ctx[:400]
            jobs.append({
                "title": title[:200],
                "description": context[:6000],
                "url": f"https://www.linkedin.com/jobs/view/{jid}/",
                "client_name": None,
            })
    if jobs:
        return jobs
    return [{
        "title": _ws(subject.replace("LinkedIn", "")) or "LinkedIn job alert",
        "description": _plain(soup, body),
        "url": None,
        "client_name": None,
    }]


def parse_freelancermap(subject: str, body: str) -> list[dict]:
    """freelancermap 'project agent' digests bundle many projects."""
    jobs: list[dict] = []
    seen: set[str] = set()
    soup = _soup(body)
    if soup is not None:
        for a in soup.find_all("a", href=True):
            if not re.search(r"freelancermap\.[a-z]+/(?:project|projekt)", a["href"], re.I):
                continue
            clean = _clean_url(a["href"])
            title = _ws(a.get_text())
            if clean in seen or len(title) < 5:
                continue
            seen.add(clean)
            jobs.append({
                "title": title[:200],
                "description": title[:6000],
                "url": clean,
                "client_name": None,
            })
    if jobs:
        return jobs
    return [{
        "title": _ws(re.sub(r"(?i)freelancermap|project ?agent|projektagent|[:|]", " ", subject)) or "freelancermap project alert",
        "description": _plain(soup, body),
        "url": "https://www.freelancermap.com/project/",
        "client_name": None,
    }]


def parse_malt(subject: str, body: str) -> list[dict]:
    """Malt project alert — usually one project per email."""
    title_m = re.search(r"(?:project for you|new project|nouveau projet)[:\-]\s*(.+)", subject, re.I)
    title = _ws(title_m.group(1) if title_m else subject)
    url_m = re.search(r"https?://(?:www\.)?malt\.[a-z]+/[^\s\"'<>]+", body, re.I)
    client_m = re.search(r"([A-Z][\w&\.\- ]{2,40})\s+(?:is looking|cherche|recherche)", body)
    soup = _soup(body)
    return [{
        "title": title or "Malt project",
        "description": _plain(soup, body),
        "url": _clean_url(url_m.group(0)) if url_m else None,
        "client_name": client_m.group(1).strip() if client_m else None,
    }]


def parse_contra(subject: str, body: str) -> list[dict]:
    """Contra opportunity / digest emails (may list several opportunities)."""
    jobs: list[dict] = []
    seen: set[str] = set()
    soup = _soup(body)
    if soup is not None:
        for a in soup.find_all("a", href=True):
            if not re.search(r"contra\.com/(?:opportunities|jobs|p)/", a["href"], re.I):
                continue
            clean = _clean_url(a["href"])
            title = _ws(a.get_text())
            if clean in seen or len(title) < 5:
                continue
            seen.add(clean)
            jobs.append({"title": title[:200], "description": title[:6000], "url": clean, "client_name": None})
    if jobs:
        return jobs
    url_m = re.search(r"https?://(?:www\.)?contra\.com/[^\s\"'<>]+", body, re.I)
    return [{
        "title": _ws(subject.replace("New opportunity:", "")) or "Contra opportunity",
        "description": _plain(soup, body),
        "url": _clean_url(url_m.group(0)) if url_m else None,
        "client_name": None,
    }]


PARSER_REGISTRY: dict[str, Callable[[str, str], list[dict]]] = {
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

                folder_jobs = 0
                criteria = AND(date_gte=cutoff.date())
                for msg in mb.fetch(criteria, limit=100, reverse=True):
                    msg_dt = msg.date
                    if msg_dt and msg_dt.replace(tzinfo=timezone.utc) < cutoff:
                        continue
                    subj = msg.subject or ""
                    body = msg.html or msg.text or ""
                    try:
                        parsed_list = parser(subj, body) or []
                    except Exception as e:
                        logger.warning("Parser %s failed on a message: %s", parser_name, e)
                        continue

                    for parsed in parsed_list:
                        if not parsed or not parsed.get("title"):
                            continue
                        # Stable per-job id: prefer the job's own URL so the same
                        # posting across multiple daily emails dedups to one id.
                        basis = parsed.get("url") or f"{msg.uid}-{parsed['title']}"
                        jid = f"{prefix}{hashlib.sha1(basis.encode()).hexdigest()[:14]}"
                        jobs.append(RawJob(
                            job_id=jid,
                            source=f"email:{parser_name}",
                            title=parsed["title"][:250],
                            description=parsed["description"],
                            url=parsed.get("url"),
                            client_name=parsed.get("client_name"),
                            posted_at=to_utc_iso(msg_dt) if msg_dt else None,
                        ))
                        folder_jobs += 1

                logger.info("Email folder %s (%s) -> %d job(s)", fname, parser_name, folder_jobs)

        logger.info("Email %s returned %d items", self.name, len(jobs))
        return jobs
