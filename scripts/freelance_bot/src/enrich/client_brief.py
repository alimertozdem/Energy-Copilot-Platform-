"""Client briefing generator — short meeting-prep doc.

Optional enrichment: if the job posting has a client website URL, fetch the
landing page and feed it to the LLM along with the job description. The LLM
produces a ≤250-word internal briefing.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from ..llm import LLMError, call_llm
from .proposal import load_text

logger = logging.getLogger(__name__)


def generate_client_brief(
    *,
    job_title: str,
    job_description: str,
    client_name: Optional[str],
    template_dir: Path,
    fetch_web: bool = True,
) -> Optional[str]:
    """Return a short briefing text, or None if LLM/fetch fails.

    Args:
        fetch_web: If True, try to fetch the client website (when discoverable)
                   and include a short summary in the LLM prompt.
    """
    template = load_text(template_dir / "client_brief.md")

    web_snippet = ""
    if fetch_web:
        web_snippet = _try_fetch_client_site(job_description, client_name)

    prompt = f"""You are preparing a senior-level internal briefing for Ali Mert Özdemir \
before a freelance discovery call. Follow this template exactly:

{template}

## JOB POSTING

Client name (if known): {client_name or '(anonymous / not stated)'}

Title: {job_title}

Description:
{job_description[:4000]}

## OPTIONAL CLIENT WEB CONTEXT

{web_snippet or '(no public web context available — base inferences only on the job posting)'}

## YOUR TASK

Write the briefing. ≤ 250 words. Plain text. Number the 5 sections.
"""

    try:
        resp = call_llm(prompt, temperature=0.3, max_output_tokens=600)
    except LLMError as e:
        logger.warning("Client brief LLM failed: %s", e)
        return None

    return resp.text.strip()


# ─────────────────────────────────────────────────────────────────────────────
# Web fetching helpers — best-effort, never blocks pipeline if they fail.
# ─────────────────────────────────────────────────────────────────────────────

def _try_fetch_client_site(description: str, client_name: Optional[str]) -> str:
    """Look for a URL in the description; if found, fetch and return excerpt."""
    url = _extract_first_external_url(description)
    if not url:
        return ""

    try:
        with httpx.Client(timeout=8, follow_redirects=True) as client:
            resp = client.get(url, headers={"User-Agent": "Mozilla/5.0 (FreelanceBot)"})
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            # remove script/style
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            text = " ".join(soup.get_text(separator=" ").split())
            return f"Source: {url}\n\nExcerpt:\n{text[:2500]}"
    except Exception as e:
        logger.info("Could not fetch %s: %s", url, e)
        return ""


URL_REGEX = re.compile(r"https?://[^\s\"'<>)\]]+", re.I)
BLOCKED_DOMAINS = {
    "malt.com", "malt.fr", "malt.de",
    "freelance.de", "freelancermap.de",
    "contra.com",
    "upwork.com",
    "linkedin.com",
    "indeed.com",
    "google.com",
}


def _extract_first_external_url(text: str) -> Optional[str]:
    for m in URL_REGEX.finditer(text):
        url = m.group(0).rstrip(".,;:)")
        host = re.sub(r"^https?://(www\.)?", "", url).split("/")[0].lower()
        if any(host == d or host.endswith("." + d) for d in BLOCKED_DOMAINS):
            continue
        return url
    return None
