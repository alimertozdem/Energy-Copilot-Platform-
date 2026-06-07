"""SQLite storage round-trip tests."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.storage import JobRecord, JobsDB, ProposalRecord  # noqa: E402


@pytest.fixture
def db(tmp_path: Path) -> JobsDB:
    return JobsDB(tmp_path / "test.db")


def test_insert_and_has_job(db: JobsDB):
    job = JobRecord(
        job_id="test_001",
        source="rss:test",
        title="Test job",
        description="A CSRD dashboard project",
        url="https://example.com/job/1",
    )
    db.insert_job(job)
    assert db.has_job("test_001")
    assert not db.has_job("test_002")


def test_insert_dedup(db: JobsDB):
    job = JobRecord(job_id="dup", source="rss:t", title="T", description="D")
    db.insert_job(job)
    db.insert_job(job)  # second insert should be ignored
    fetched = db.get_job("dup")
    assert fetched is not None
    assert fetched.title == "T"


def test_update_scoring(db: JobsDB):
    db.insert_job(JobRecord(job_id="j1", source="rss:t", title="T", description="D"))
    db.update_job_scoring("j1", True, True, 8, "good fit", True)
    j = db.get_job("j1")
    assert j and j.llm_score == 8 and j.matched is True


def test_proposal_lifecycle(db: JobsDB):
    db.insert_job(JobRecord(job_id="j1", source="rss:t", title="T", description="D"))
    pid = db.insert_proposal(ProposalRecord(
        job_id="j1", package_id="P1", draft_text="Hello world",
    ))
    assert pid > 0
    db.update_proposal_status(pid, "submitted")
    # No public getter for a single proposal — verify via stats
    stats = db.stats_since("2000-01-01T00:00:00+00:00")
    assert stats["proposals_submitted"] >= 1


def test_run_lifecycle(db: JobsDB):
    rid = db.start_run()
    db.finish_run(rid, jobs_seen=5, jobs_new=3, jobs_matched=2, proposals_drafted=2, pushed=2)


def test_stats_since(db: JobsDB):
    db.insert_job(JobRecord(job_id="j1", source="rss:t", title="T", description="D"))
    db.update_job_scoring("j1", True, True, 9, "ok", True)
    s = db.stats_since("2000-01-01T00:00:00+00:00")
    assert s["jobs_seen"] >= 1
    assert s["jobs_matched"] >= 1
