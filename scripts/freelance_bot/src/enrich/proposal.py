"""Proposal draft generator.

Builds a prompt from personal.yml + proposal_master.md + matched job description,
then calls the LLM. Output is a 220-320 word proposal Mert can copy-paste
straight into the platform (with minor edits if needed).
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import yaml

from ..llm import LLMError, call_llm

logger = logging.getLogger(__name__)

PROPOSAL_SYSTEM_PROMPT = """You write freelance proposals on behalf of a senior \
Microsoft Fabric & Power BI specialist named Ali Mert Özdemir. You write in his \
voice: direct, technically credible, no apology language, no buzzwords.

Follow the master template structure exactly. Pick the productized package that \
best matches the job. If multiple packages fit, offer TWO options (forces the \
client to choose between A and B, not yes/no).

Pick exactly ONE proof artifact from the list — the one most relevant to the job's \
domain. Reference it concretely.

Hard constraints:
- 220-320 words TOTAL
- 5 ingredients in order: pain mirror → proof artifact → specific question → \
  package match → domain jargon
- No emojis. No bold/italic. No markdown.
- Use "will" not "would". No "I think I might".
- Sign off with "Best, Mert"
- Do not invent capabilities or numbers not in the personal context
"""


def load_yaml(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_text(path: Path) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def generate_proposal(
    *,
    job_title: str,
    job_description: str,
    personal_yml_path: Path,
    template_dir: Path,
) -> tuple[Optional[str], Optional[str]]:
    """Return (proposal_text, picked_package_id).

    On LLM failure, returns (None, None). Caller decides how to handle.
    """
    personal = load_yaml(personal_yml_path)
    master = load_text(template_dir / "proposal_master.md")
    examples = _load_examples(template_dir)

    user_prompt = _build_prompt(
        personal=personal,
        master_template=master,
        examples=examples,
        job_title=job_title,
        job_description=job_description,
    )

    try:
        resp = call_llm(
            PROPOSAL_SYSTEM_PROMPT + "\n\n---\n\n" + user_prompt,
            temperature=0.45,
            max_output_tokens=900,
        )
    except LLMError as e:
        logger.error("Proposal LLM failed: %s", e)
        return None, None

    text = resp.text.strip()
    # quick sanity: must end with sign-off
    if "Mert" not in text[-200:]:
        text = text.rstrip() + "\n\nBest,\nMert"

    package_id = _infer_picked_package(text, personal)
    return text, package_id


def _load_examples(template_dir: Path) -> list[str]:
    """Load few-shot examples to ground the LLM."""
    examples = []
    for fname in ("example_csrd.md", "example_kpi.md", "example_fabric_audit.md", "example_hourly.md"):
        p = template_dir / fname
        if p.exists():
            examples.append(load_text(p))
    return examples


def _build_prompt(
    *,
    personal: dict,
    master_template: str,
    examples: list[str],
    job_title: str,
    job_description: str,
) -> str:
    """Construct the user prompt with all context the LLM needs."""
    packages_block = "\n".join(
        f"- {p['id']}: {p['name']} — €{p['price_eur']} / {p['duration']}\n"
        f"  fits_when: {p['fits_when']}\n"
        f"  summary: {p['summary'].strip()}"
        for p in personal.get("packages", [])
    )

    artifacts_block = "\n".join(
        f"- {a['id']} — {a['summary']}\n  fits_when: {a['fits_when']}"
        for a in personal.get("proof_artifacts", [])
    )

    hourly = personal.get("hourly_fallback", {})
    hourly_block = (
        f"Hourly fallback: €{hourly.get('hourly_eur', 60)}/hr, "
        f"€{hourly.get('daily_eur', 450)}/day. {hourly.get('notes', '')}"
    )

    examples_block = "\n\n---\n\n".join(examples) if examples else "(no examples)"

    return f"""## MASTER TEMPLATE STRUCTURE

{master_template}

## PERSONAL CONTEXT

Positioning:
{personal.get('positioning', '').strip()}

Credentials:
{chr(10).join('- ' + c for c in personal.get('credentials', []))}

Productized packages:
{packages_block}

{hourly_block}

Proof artifacts (pick ONE that best matches this job):
{artifacts_block}

Sign-off CTA: {personal.get('call_signoff', {}).get('cta', '')}

## FEW-SHOT EXAMPLES

{examples_block}

## JOB TO RESPOND TO

Title: {job_title}

Description:
{job_description[:5000]}

## YOUR TASK

Write the proposal now. Output ONLY the proposal text. No preamble, no JSON, no \
headers, no markdown formatting. Plain text only. 220-320 words.
"""


def _infer_picked_package(proposal_text: str, personal: dict) -> Optional[str]:
    """Best-effort: which package id did the LLM mention?"""
    for p in personal.get("packages", []):
        pid = p["id"]
        if pid.lower() in proposal_text.lower() or p["name"].lower() in proposal_text.lower():
            return pid
    if "€60/hour" in proposal_text or "€450/day" in proposal_text or "hourly" in proposal_text.lower():
        return "hourly"
    return None
