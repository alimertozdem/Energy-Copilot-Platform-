"""High-level DB operations — wraps SQLite for the rest of the code.

Keep all SQL in this file. The rest of the codebase talks to JobRecord and
ProposalRecord dataclasses, not raw rows.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Optional

from .models import get_connection, init_db


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class JobRecord:
    job_id: str
    source: str
    title: str
    description: str
    url: Optional[str] = None
    client_name: Optional[str] = None
    budget_raw: Optional[str] = None
    budget_min_eur: Optional[float] = None
    budget_max_eur: Optional[float] = None
    budget_type: Optional[str] = None  # 'fixed' | 'hourly' | 'unknown'
    posted_at: Optional[str] = None
    seen_at: str = field(default_factory=utcnow)
    keyword_pass: bool = False
    budget_pass: bool = False
    llm_score: Optional[int] = None
    llm_reason: Optional[str] = None
    matched: bool = False


@dataclass
class ProposalRecord:
    job_id: str
    package_id: Optional[str]
    draft_text: str
    client_brief: Optional[str] = None
    status: str = "drafted"
    proposal_id: Optional[int] = None
    drafted_at: str = field(default_factory=utcnow)
    last_status_at: str = field(default_factory=utcnow)
    notes: Optional[str] = None


class JobsDB:
    """All DB operations the rest of the bot needs."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        init_db(self.db_path)

    # ────────────────────────── Jobs ──────────────────────────

    def has_job(self, job_id: str) -> bool:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                "SELECT 1 FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
        return row is not None

    def insert_job(self, job: JobRecord) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO jobs (
                    job_id, source, title, description, url, client_name,
                    budget_raw, budget_min_eur, budget_max_eur, budget_type,
                    posted_at, seen_at, keyword_pass, budget_pass,
                    llm_score, llm_reason, matched
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.job_id, job.source, job.title, job.description, job.url,
                    job.client_name, job.budget_raw, job.budget_min_eur,
                    job.budget_max_eur, job.budget_type, job.posted_at,
                    job.seen_at, int(job.keyword_pass), int(job.budget_pass),
                    job.llm_score, job.llm_reason, int(job.matched),
                ),
            )
            conn.commit()

    def update_job_scoring(
        self,
        job_id: str,
        keyword_pass: bool,
        budget_pass: bool,
        llm_score: Optional[int],
        llm_reason: Optional[str],
        matched: bool,
    ) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                UPDATE jobs
                   SET keyword_pass = ?, budget_pass = ?,
                       llm_score = ?, llm_reason = ?, matched = ?
                 WHERE job_id = ?
                """,
                (
                    int(keyword_pass), int(budget_pass),
                    llm_score, llm_reason, int(matched), job_id,
                ),
            )
            conn.commit()

    def get_job(self, job_id: str) -> Optional[JobRecord]:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
        return _row_to_job(row) if row else None

    # ────────────────────────── Proposals ──────────────────────

    def insert_proposal(self, proposal: ProposalRecord) -> int:
        with get_connection(self.db_path) as conn:
            cur = conn.execute(
                """
                INSERT INTO proposals (
                    job_id, package_id, draft_text, client_brief,
                    status, drafted_at, last_status_at, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    proposal.job_id, proposal.package_id, proposal.draft_text,
                    proposal.client_brief, proposal.status,
                    proposal.drafted_at, proposal.last_status_at, proposal.notes,
                ),
            )
            conn.commit()
            return int(cur.lastrowid)

    def update_proposal_status(self, proposal_id: int, status: str, notes: Optional[str] = None) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                UPDATE proposals
                   SET status = ?, last_status_at = ?, notes = COALESCE(?, notes)
                 WHERE proposal_id = ?
                """,
                (status, utcnow(), notes, proposal_id),
            )
            conn.commit()

    def get_pending_digest(self, since_iso: str) -> list[dict]:
        """Matched, drafted proposals not yet sent in a daily digest.

        Returns dicts (job + proposal fields) for the digest builder to group
        by stream and cap. Excludes anything already logged with kind='digest'.
        """
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT j.job_id, j.source, j.title, j.url, j.budget_raw,
                       j.llm_score, p.draft_text, p.package_id
                  FROM proposals p
                  JOIN jobs j ON j.job_id = p.job_id
                 WHERE p.status = 'drafted'
                   AND p.drafted_at >= ?
                   AND j.matched = 1
                   AND j.job_id NOT IN (
                         SELECT job_id FROM notification_log
                          WHERE kind = 'digest' AND job_id IS NOT NULL
                       )
                 ORDER BY j.llm_score DESC, p.drafted_at DESC
                """,
                (since_iso,),
            ).fetchall()
        return [dict(r) for r in rows]

    def funnel_since(self, since_iso: str) -> dict:
        """Funnel counts over a window: how many jobs were seen, passed each
        filter tier, and finally matched. Powers the digest's self-diagnosing
        line so a '0' is never ambiguous (no emails vs all filtered)."""
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) AS seen,
                       COALESCE(SUM(keyword_pass), 0) AS keyword_ok,
                       COALESCE(SUM(budget_pass), 0) AS budget_ok,
                       COALESCE(SUM(matched), 0) AS matched
                  FROM jobs
                 WHERE seen_at >= ?
                """,
                (since_iso,),
            ).fetchone()
        return {
            "seen": int(row["seen"] or 0),
            "keyword_ok": int(row["keyword_ok"] or 0),
            "budget_ok": int(row["budget_ok"] or 0),
            "matched": int(row["matched"] or 0),
        }

    # ────────────────────────── Runs ──────────────────────────

    def start_run(self) -> int:
        with get_connection(self.db_path) as conn:
            cur = conn.execute(
                "INSERT INTO runs (started_at) VALUES (?)", (utcnow(),)
            )
            conn.commit()
            return int(cur.lastrowid)

    def finish_run(
        self,
        run_id: int,
        jobs_seen: int,
        jobs_new: int,
        jobs_matched: int,
        proposals_drafted: int,
        pushed: int,
        errors: Optional[list[str]] = None,
    ) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                UPDATE runs
                   SET finished_at = ?,
                       jobs_seen = ?, jobs_new = ?, jobs_matched = ?,
                       proposals_drafted = ?, pushed_to_telegram = ?,
                       errors = ?
                 WHERE run_id = ?
                """,
                (
                    utcnow(), jobs_seen, jobs_new, jobs_matched,
                    proposals_drafted, pushed,
                    json.dumps(errors) if errors else None,
                    run_id,
                ),
            )
            conn.commit()

    # ────────────────────────── Notifications ─────────────────

    def count_notifications_today(self, kind: str = "match") -> int:
        # Counts UTC-day; the orchestrator should be aware of timezone.
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        ).isoformat(timespec="seconds")
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) AS n
                  FROM notification_log
                 WHERE kind = ? AND sent_at >= ? AND success = 1
                """,
                (kind, today_start),
            ).fetchone()
        return int(row["n"]) if row else 0

    def log_notification(self, kind: str, job_id: Optional[str], success: bool, error: Optional[str] = None) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO notification_log (sent_at, kind, job_id, success, error)
                VALUES (?, ?, ?, ?, ?)
                """,
                (utcnow(), kind, job_id, int(success), error),
            )
            conn.commit()

    # ────────────────────────── Stats ──────────────────────────

    def stats_since(self, since_iso: str) -> dict:
        with get_connection(self.db_path) as conn:
            stats = {}
            stats["jobs_seen"] = conn.execute(
                "SELECT COUNT(*) FROM jobs WHERE seen_at >= ?", (since_iso,)
            ).fetchone()[0]
            stats["jobs_matched"] = conn.execute(
                "SELECT COUNT(*) FROM jobs WHERE seen_at >= ? AND matched = 1",
                (since_iso,),
            ).fetchone()[0]
            stats["proposals_submitted"] = conn.execute(
                "SELECT COUNT(*) FROM proposals WHERE drafted_at >= ? AND status = 'submitted'",
                (since_iso,),
            ).fetchone()[0]
            stats["proposals_replied"] = conn.execute(
                "SELECT COUNT(*) FROM proposals WHERE drafted_at >= ? AND status IN ('replied','won','lost')",
                (since_iso,),
            ).fetchone()[0]
            stats["proposals_won"] = conn.execute(
                "SELECT COUNT(*) FROM proposals WHERE drafted_at >= ? AND status = 'won'",
                (since_iso,),
            ).fetchone()[0]
        return stats


def _row_to_job(row: sqlite3.Row) -> JobRecord:
    return JobRecord(
        job_id=row["job_id"],
        source=row["source"],
        title=row["title"],
        description=row["description"],
        url=row["url"],
        client_name=row["client_name"],
        budget_raw=row["budget_raw"],
        budget_min_eur=row["budget_min_eur"],
        budget_max_eur=row["budget_max_eur"],
        budget_type=row["budget_type"],
        posted_at=row["posted_at"],
        seen_at=row["seen_at"],
        keyword_pass=bool(row["keyword_pass"]),
        budget_pass=bool(row["budget_pass"]),
        llm_score=row["llm_score"],
        llm_reason=row["llm_reason"],
        matched=bool(row["matched"]),
    )
