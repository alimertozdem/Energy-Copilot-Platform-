"""Transactional email via Resend (https://resend.com).

A single helper used by the password-reset flow. Config from env:
  RESEND_API_KEY -- Resend API key (required to actually send mail)
  RESEND_FROM    -- From address, e.g. "EnergyLens <no-reply@energylens.eu>"
                    (the domain must be verified in Resend)

If RESEND_API_KEY is unset, send_email logs a warning and returns False -- the
caller still responds 200 so the flow never reveals whether an account exists.
send_email never raises: a mail failure must not break the HTTP request.
"""
import logging
import os

import httpx

logger = logging.getLogger(__name__)

_RESEND_ENDPOINT = "https://api.resend.com/emails"
_DEFAULT_FROM = "EnergyLens <no-reply@energylens.eu>"


def send_email(*, to: str, subject: str, html: str) -> bool:
    """Send one transactional email. Returns True on success, False otherwise."""
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        logger.warning(
            "[email] RESEND_API_KEY not set -- email to %s not sent", to
        )
        return False
    sender = os.getenv("RESEND_FROM", _DEFAULT_FROM)
    try:
        resp = httpx.post(
            _RESEND_ENDPOINT,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"from": sender, "to": [to], "subject": subject, "html": html},
            timeout=10.0,
        )
    except httpx.HTTPError as exc:
        logger.error("[email] Resend request failed: %s", exc)
        return False
    if resp.status_code >= 400:
        logger.error("[email] Resend %s: %s", resp.status_code, resp.text[:300])
        return False
    return True
