"""Freelance bot orchestrator — one cron invocation = one run of this script.

Flow:
  1. Load configs (filters, sources, personal)
  2. Start a run row
  3. For each source: fetch raw jobs
  4. For each new job: keyword → budget → LLM score
  5. If matched: generate proposal + brief
  6. Push to Telegram (respecting quiet hours + daily cap)
  7. Finish run row

Designed to be safe to invoke many times — dedup happens in storage.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, time as dtime, timedelta, timezone
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

import yaml

# Make absolute imports work when run as a script
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.enrich import generate_client_brief, generate_cover_letter, generate_proposal  # noqa: E402
from src.filter import check_budget, check_keywords, score_job  # noqa: E402
from src.notify import (  # noqa: E402
    TelegramNotifier,
    format_daily_digest,
    format_daily_summary,
    format_match_message,
    format_weekly_digest,
)
from src.sources import EmailIMAPSource, RSSSource  # noqa: E402
from src.sources.base import RawJob  # noqa: E402
from src.storage import JobRecord, JobsDB, ProposalRecord  # noqa: E402


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
)
logger = logging.getLogger("freelance_bot")


CONFIG_DIR = ROOT / "config"
TEMPLATE_DIR = CONFIG_DIR / "templates"
DEFAULT_DB = ROOT / "data" / "jobs.db"


def main() -> int:
    parser = argparse.ArgumentParser(description="Freelance bot cron entrypoint")
    parser.add_argument("--dry-run", action="store_true", help="Score jobs, skip Telegram push, skip writes that would change status")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="Path to SQLite DB")
    parser.add_argument("--mode", choices=["scan", "daily_summary", "weekly_digest", "daily_digest"], default="scan")
    args = parser.parse_args()

    filters_cfg = _load_yaml(CONFIG_DIR / "filters.yml")
    sources_cfg = _load_yaml(CONFIG_DIR / "sources.yml")
    personal_path = CONFIG_DIR / "personal.yml"

    db = JobsDB(Path(args.db))
    notifier = TelegramNotifier()

    if args.mode == "daily_digest":
        return _send_daily_digest(db, notifier, filters_cfg, dry_run=args.dry_run)
    if args.mode == "daily_summary":
        return _send_daily_summary(db, notifier, filters_cfg, dry_run=args.dry_run)
    if args.mode == "weekly_digest":
        return _send_weekly_digest(db, notifier, filters_cfg, dry_run=args.dry_run)

    return _run_scan(
        db=db,
        notifier=notifier,
        filters_cfg=filters_cfg,
        sources_cfg=sources_cfg,
        personal_path=personal_path,
        dry_run=args.dry_run,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Main scan loop
# ─────────────────────────────────────────────────────────────────────────────


def _run_scan(
    *,
    db: JobsDB,
    notifier: TelegramNotifier,
    filters_cfg: dict,
    sources_cfg: dict,
    personal_path: Path,
    dry_run: bool,
) -> int:
    run_id = db.start_run()
    errors: list[str] = []

    raw_jobs: list[RawJob] = []
    try:
        raw_jobs.extend(_collect_rss(sources_cfg, filters_cfg))
        raw_jobs.extend(_collect_email(sources_cfg, filters_cfg))
    except Exception as e:
        logger.exception("Source collection error")
        errors.append(str(e))

    seen = len(raw_jobs)
    new = 0
    matched = 0
    drafted = 0
    pushed = 0

    tz = ZoneInfo(filters_cfg["notifications"].get("timezone", "Europe/Berlin"))
    daily_cap = int(filters_cfg["notifications"].get("max_per_day", 10))
    already_today = db.count_notifications_today("match")
    remaining_today = max(0, daily_cap - already_today)

    in_quiet = _in_quiet_hours(filters_cfg["notifications"], tz)
    digest_mode = bool(filters_cfg["notifications"].get("digest_mode", False))

    for raw in raw_jobs:
        if db.has_job(raw.job_id):
            continue
        new += 1

        # Tier 1 — keyword
        kw = check_keywords(
            raw.title,
            raw.description,
            include=filters_cfg["include_keywords"],
            exclude=filters_cfg["exclude_keywords"],
        )

        # Tier 2 — budget (run regardless so we store info)
        bud = check_budget(
            raw.description,
            fixed_min_eur=float(filters_cfg["budget"]["fixed_min_eur"]),
            hourly_min_eur=float(filters_cfg["budget"]["hourly_min_eur"]),
            allow_no_budget=bool(filters_cfg["budget"]["allow_no_budget"]),
            fx_to_eur=filters_cfg["fx_to_eur"],
        )

        job_record = JobRecord(
            job_id=raw.job_id,
            source=raw.source,
            title=raw.title,
            description=raw.description,
            url=raw.url,
            client_name=raw.client_name,
            budget_raw=bud.raw_match,
            budget_min_eur=bud.min_eur,
            budget_max_eur=bud.max_eur,
            budget_type=bud.type,
            posted_at=raw.posted_at,
            keyword_pass=kw.passed,
            budget_pass=bud.passed,
        )
        db.insert_job(job_record)

        if not (kw.passed and bud.passed):
            logger.info(
                "SKIP %s — keyword:%s budget:%s",
                raw.job_id, kw.passed, bud.passed,
            )
            continue

        # Tier 3 — LLM score (costs tokens, do only after Tier 1+2 pass)
        score = score_job(raw.title, raw.description, temperature=float(filters_cfg["llm_score"]["prompt_temperature"]))
        is_match = score.score >= int(filters_cfg["llm_score"]["min_score_to_push"])
        db.update_job_scoring(
            raw.job_id, kw.passed, bud.passed,
            score.score, score.reasoning, is_match,
        )

        if not is_match:
            logger.info("SKIP %s — score %d (%s)", raw.job_id, score.score, score.reasoning)
            continue

        matched += 1
        logger.info("MATCH %s — score %d", raw.job_id, score.score)

        # Enrich — route by stream (LinkedIn = job cover letter, else freelance proposal)
        stream = _stream_for(raw.job_id)
        if stream == "job":
            proposal_text = generate_cover_letter(
                job_title=raw.title,
                job_description=raw.description,
                personal_yml_path=personal_path,
                template_dir=TEMPLATE_DIR,
            )
            package_id = None
        else:
            proposal_text, package_id = generate_proposal(
                job_title=raw.title,
                job_description=raw.description,
                personal_yml_path=personal_path,
                template_dir=TEMPLATE_DIR,
            )
        if proposal_text:
            drafted += 1
            brief = generate_client_brief(
                job_title=raw.title,
                job_description=raw.description,
                client_name=raw.client_name,
                template_dir=TEMPLATE_DIR,
                fetch_web=True,
            )
            if not dry_run:
                db.insert_proposal(ProposalRecord(
                    job_id=raw.job_id,
                    package_id=package_id,
                    draft_text=proposal_text,
                    client_brief=brief,
                    status="drafted",
                ))
        else:
            brief = None

        # Digest mode: collect + draft only; the noon daily_digest run sends one
        # grouped message. No live per-match push here.
        if digest_mode:
            logger.info("DIGEST queued %s (stream=%s, score=%d)", raw.job_id, stream, score.score)
            continue

        # Push (legacy live mode — only runs when digest_mode is off)
        if dry_run:
            logger.info("[dry-run] would push job %s", raw.job_id)
            continue
        if in_quiet:
            logger.info("Quiet hours — queueing %s (not pushed live)", raw.job_id)
            continue
        if remaining_today <= 0:
            logger.info("Daily cap hit — %s queued for next morning", raw.job_id)
            continue

        msg = format_match_message(
            title=raw.title,
            source=raw.source,
            url=raw.url,
            budget_raw=bud.raw_match,
            score=score.score,
            score_reason=score.reasoning,
            package_id=package_id,
            proposal_text=proposal_text or "(proposal generation failed — write manually)",
            client_brief=brief,
        )
        ok = notifier.send(msg)
        db.log_notification("match", raw.job_id, success=ok, error=None if ok else "send_failed")
        if ok:
            pushed += 1
            remaining_today -= 1

    db.finish_run(run_id, seen, new, matched, drafted, pushed, errors or None)
    logger.info(
        "Run finished — seen=%d new=%d matched=%d drafted=%d pushed=%d",
        seen, new, matched, drafted, pushed,
    )
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# Source collection
# ─────────────────────────────────────────────────────────────────────────────


def _collect_rss(sources_cfg: dict, filters_cfg: dict) -> list[RawJob]:
    lookback = int(sources_cfg["poll"]["rss_lookback_hours"])
    out: list[RawJob] = []
    for entry in sources_cfg.get("rss_sources", []):
        if not entry.get("enabled", True):
            continue
        src = RSSSource(entry["name"], entry["url"], entry["job_id_prefix"])
        try:
            out.extend(src.fetch(lookback))
        except Exception as e:
            logger.exception("RSS source %s failed: %s", entry["name"], e)
    return out


def _collect_email(sources_cfg: dict, filters_cfg: dict) -> list[RawJob]:
    lookback = int(sources_cfg["poll"]["email_lookback_hours"])
    out: list[RawJob] = []
    for entry in sources_cfg.get("email_sources", []):
        if not entry.get("enabled", True):
            continue
        src = EmailIMAPSource(
            name=entry["name"],
            imap_host=entry["imap_host"],
            imap_port=int(entry["imap_port"]),
            username_env=entry["username_env"],
            password_env=entry["password_env"],
            folders=entry["folders"],
        )
        try:
            out.extend(src.fetch(lookback))
        except Exception as e:
            logger.exception("Email source %s failed: %s", entry["name"], e)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Summary modes
# ─────────────────────────────────────────────────────────────────────────────


def _send_daily_summary(db: JobsDB, notifier: TelegramNotifier, filters_cfg: dict, dry_run: bool) -> int:
    tz = ZoneInfo(filters_cfg["notifications"].get("timezone", "Europe/Berlin"))
    since = (datetime.now(tz) - timedelta(hours=24)).astimezone(timezone.utc).isoformat(timespec="seconds")
    stats = db.stats_since(since)
    msg = format_daily_summary(stats)
    if dry_run:
        logger.info("[dry-run] daily summary: %s", json.dumps(stats))
        return 0
    notifier.send(msg)
    db.log_notification("daily_summary", None, success=True)
    return 0


def _send_weekly_digest(db: JobsDB, notifier: TelegramNotifier, filters_cfg: dict, dry_run: bool) -> int:
    tz = ZoneInfo(filters_cfg["notifications"].get("timezone", "Europe/Berlin"))
    since = (datetime.now(tz) - timedelta(days=7)).astimezone(timezone.utc).isoformat(timespec="seconds")
    stats = db.stats_since(since)
    msg = format_weekly_digest(stats)
    if dry_run:
        logger.info("[dry-run] weekly digest: %s", json.dumps(stats))
        return 0
    notifier.send(msg)
    db.log_notification("weekly_digest", None, success=True)
    return 0


def _stream_for(job_id: str) -> str:
    """LinkedIn alerts are employment jobs; everything else is freelance."""
    return "job" if (job_id or "").startswith("li_") else "freelance"


def _send_daily_digest(db: JobsDB, notifier: TelegramNotifier, filters_cfg: dict, dry_run: bool) -> int:
    """Once a day: gather drafted matches, group into Jobs + Freelance, send ONE message."""
    notif = filters_cfg["notifications"]
    tz = ZoneInfo(notif.get("timezone", "Europe/Berlin"))
    per_stream = int(notif.get("digest_per_stream", 6))
    # Look back 26h so we never miss the tail of yesterday's matches.
    since = (datetime.now(tz) - timedelta(hours=26)).astimezone(timezone.utc).isoformat(timespec="seconds")
    rows = db.get_pending_digest(since)

    by_stream: dict[str, list[dict]] = {"job": [], "freelance": []}
    for r in rows:
        s = _stream_for(r["job_id"])
        if len(by_stream[s]) >= per_stream:
            continue
        by_stream[s].append({
            "job_id": r["job_id"],
            "title": r.get("title"),
            "url": r.get("url"),
            "source": r.get("source"),
            "score": r.get("llm_score"),
            "budget_raw": r.get("budget_raw"),
            "draft": r.get("draft_text"),
        })

    date_str = datetime.now(tz).strftime("%a %d %b %Y")
    msg = format_daily_digest(by_stream, date_str)

    if dry_run:
        logger.info("[dry-run] daily digest — job=%d freelance=%d",
                    len(by_stream["job"]), len(by_stream["freelance"]))
        return 0

    ok = notifier.send(msg)
    if ok:
        for s in ("job", "freelance"):
            for it in by_stream[s]:
                db.log_notification("digest", it["job_id"], success=True)
    db.log_notification("daily_digest", None, success=ok, error=None if ok else "send_failed")
    logger.info("Daily digest sent=%s — job=%d freelance=%d",
                ok, len(by_stream["job"]), len(by_stream["freelance"]))
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _load_yaml(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _in_quiet_hours(notif_cfg: dict, tz: ZoneInfo) -> bool:
    start = int(notif_cfg.get("quiet_hours_start", 22))
    end = int(notif_cfg.get("quiet_hours_end", 7))
    now_h = datetime.now(tz).hour
    if start <= end:
        return start <= now_h < end
    return now_h >= start or now_h < end


if __name__ == "__main__":
    raise SystemExit(main())
