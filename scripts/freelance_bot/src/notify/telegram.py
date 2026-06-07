"""Telegram bot push — sends one message per matched job.

We use the raw HTTP API instead of python-telegram-bot to keep deps tiny.
Bot token + chat ID come from env vars.

Setup (Mert does this once):
1. Open Telegram, talk to @BotFather, /newbot, choose a name. Copy the token.
2. Send your bot a /start message.
3. Visit https://api.telegram.org/bot<TOKEN>/getUpdates to find your chat ID.
4. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID env vars (locally and in GH Secrets).
"""
from __future__ import annotations

import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
MAX_MSG_LEN = 4000  # Telegram limit is 4096; leave headroom


class TelegramNotifier:
    """Sends formatted messages to a single Telegram chat."""

    def __init__(self, token: Optional[str] = None, chat_id: Optional[str] = None):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        if not self.token or not self.chat_id:
            logger.warning("Telegram credentials missing; notifications will be no-ops")

    def is_configured(self) -> bool:
        return bool(self.token and self.chat_id)

    def send(self, text: str, *, parse_mode: str = "Markdown", disable_preview: bool = True) -> bool:
        if not self.is_configured():
            return False
        url = TELEGRAM_API.format(token=self.token)
        for chunk in _chunk_message(text, MAX_MSG_LEN):
            payload = {
                "chat_id": self.chat_id,
                "text": chunk,
                "parse_mode": parse_mode,
                "disable_web_page_preview": disable_preview,
            }
            try:
                resp = httpx.post(url, json=payload, timeout=15)
                resp.raise_for_status()
            except Exception as e:
                # Markdown parse errors are common (e.g. unbalanced *); retry plain
                logger.warning("Telegram send failed (%s); retrying plain", e)
                payload.pop("parse_mode", None)
                try:
                    resp = httpx.post(url, json=payload, timeout=15)
                    resp.raise_for_status()
                except Exception as e2:
                    logger.error("Telegram send failed (plain too): %s", e2)
                    return False
        return True


# ─────────────────────────────────────────────────────────────────────────────
# Message formatters
# ─────────────────────────────────────────────────────────────────────────────


def format_match_message(
    *,
    title: str,
    source: str,
    url: Optional[str],
    budget_raw: Optional[str],
    score: int,
    score_reason: str,
    package_id: Optional[str],
    proposal_text: str,
    client_brief: Optional[str],
) -> str:
    """Render one matched job as a single Telegram message (Markdown)."""
    parts = [
        f"🎯 *NEW MATCH — Score {score}/10*",
        f"_{score_reason}_",
        "",
        f"*{_escape_md(title)}*",
        f"Source: `{source}`",
    ]
    if budget_raw:
        parts.append(f"Budget: {_escape_md(budget_raw)}")
    if package_id:
        parts.append(f"Suggested package: *{package_id}*")
    if url:
        parts.append(f"[Open posting]({url})")
    parts.append("")
    parts.append("📝 *Proposal Draft*")
    parts.append("```")
    parts.append(proposal_text[:1800])
    parts.append("```")
    if client_brief:
        parts.append("")
        parts.append("📋 *Client Brief*")
        parts.append("```")
        parts.append(client_brief[:1200])
        parts.append("```")
    return "\n".join(parts)


def format_daily_summary(stats: dict) -> str:
    return (
        f"🌅 *Daily Summary*\n"
        f"Jobs seen: {stats.get('jobs_seen', 0)}\n"
        f"Matched: {stats.get('jobs_matched', 0)}\n"
        f"Submitted: {stats.get('proposals_submitted', 0)}\n"
        f"Replies: {stats.get('proposals_replied', 0)}\n"
        f"Wins: {stats.get('proposals_won', 0)}"
    )


def format_weekly_digest(stats: dict) -> str:
    return (
        f"📊 *Weekly Digest*\n"
        f"Jobs seen this week: {stats.get('jobs_seen', 0)}\n"
        f"Matched (≥7): {stats.get('jobs_matched', 0)}\n"
        f"Submitted: {stats.get('proposals_submitted', 0)}\n"
        f"Replies: {stats.get('proposals_replied', 0)}\n"
        f"Wins: {stats.get('proposals_won', 0)}\n\n"
        f"Reply rate: {_pct(stats.get('proposals_replied', 0), stats.get('proposals_submitted', 0))}"
    )


def _chunk_message(text: str, limit: int) -> list[str]:
    if len(text) <= limit:
        return [text]
    out, buf = [], []
    size = 0
    for line in text.split("\n"):
        if size + len(line) + 1 > limit:
            out.append("\n".join(buf))
            buf, size = [line], len(line)
        else:
            buf.append(line)
            size += len(line) + 1
    if buf:
        out.append("\n".join(buf))
    return out


def _escape_md(s: str) -> str:
    # Telegram Markdown (legacy) requires escaping these
    for ch in ("_", "*", "`", "["):
        s = s.replace(ch, "\\" + ch)
    return s


def _pct(num: int, denom: int) -> str:
    if denom == 0:
        return "n/a"
    return f"{(num / denom * 100):.0f}%"
