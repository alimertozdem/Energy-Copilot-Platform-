"""SQLite schema for the freelance bot.

Single-file DB at data/jobs.db. Three tables:
- jobs        : every job we have ever seen (dedup source of truth)
- proposals   : drafts we generated, with status lifecycle
- runs        : audit log of each cron invocation

Status lifecycle for proposals:
    drafted → submitted → replied → won | lost | ghosted
A proposal can be skipped (status=skipped) if Mert decides not to apply.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS jobs (
    job_id          TEXT PRIMARY KEY,         -- prefixed: fdde_123, malt_456, ...
    source          TEXT NOT NULL,            -- 'rss:freelance.de', 'email:malt', ...
    title           TEXT NOT NULL,
    description     TEXT NOT NULL,
    url             TEXT,
    client_name     TEXT,
    budget_raw      TEXT,                     -- as posted ("€2,000-3,000" or "$40-80/hr")
    budget_min_eur  REAL,                     -- normalized
    budget_max_eur  REAL,
    budget_type     TEXT,                     -- 'fixed' | 'hourly' | 'unknown'
    posted_at       TEXT,                     -- ISO 8601 UTC
    seen_at         TEXT NOT NULL,            -- ISO 8601 UTC, when our cron first saw it
    keyword_pass    INTEGER NOT NULL DEFAULT 0,   -- 0/1, Tier 1
    budget_pass     INTEGER NOT NULL DEFAULT 0,   -- 0/1, Tier 2
    llm_score       INTEGER,                  -- 1-10, NULL if not scored
    llm_reason      TEXT,
    matched         INTEGER NOT NULL DEFAULT 0    -- 0/1, final yes/no
);

CREATE INDEX IF NOT EXISTS idx_jobs_seen_at ON jobs(seen_at);
CREATE INDEX IF NOT EXISTS idx_jobs_matched ON jobs(matched);

CREATE TABLE IF NOT EXISTS proposals (
    proposal_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id          TEXT NOT NULL REFERENCES jobs(job_id),
    package_id      TEXT,                     -- 'P1' | 'P2' | 'P3' | 'P4' | 'hourly'
    draft_text      TEXT NOT NULL,
    client_brief    TEXT,
    status          TEXT NOT NULL DEFAULT 'drafted',  -- drafted|submitted|replied|won|lost|ghosted|skipped
    drafted_at      TEXT NOT NULL,
    last_status_at  TEXT NOT NULL,
    notes           TEXT
);

CREATE INDEX IF NOT EXISTS idx_proposals_status ON proposals(status);
CREATE INDEX IF NOT EXISTS idx_proposals_job ON proposals(job_id);

CREATE TABLE IF NOT EXISTS runs (
    run_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at      TEXT NOT NULL,
    finished_at     TEXT,
    jobs_seen       INTEGER NOT NULL DEFAULT 0,
    jobs_new        INTEGER NOT NULL DEFAULT 0,
    jobs_matched    INTEGER NOT NULL DEFAULT 0,
    proposals_drafted INTEGER NOT NULL DEFAULT 0,
    pushed_to_telegram INTEGER NOT NULL DEFAULT 0,
    errors          TEXT
);

CREATE TABLE IF NOT EXISTS notification_log (
    notif_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    sent_at         TEXT NOT NULL,
    kind            TEXT NOT NULL,            -- 'match' | 'daily_summary' | 'weekly_digest'
    job_id          TEXT REFERENCES jobs(job_id),
    success         INTEGER NOT NULL DEFAULT 1,
    error           TEXT
);

CREATE INDEX IF NOT EXISTS idx_notif_sent_at ON notification_log(sent_at);
"""


def get_connection(db_path: Path) -> sqlite3.Connection:
    """Return a connection with foreign keys + row factory enabled."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path) -> None:
    """Create tables if they don't exist. Safe to call repeatedly."""
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()
