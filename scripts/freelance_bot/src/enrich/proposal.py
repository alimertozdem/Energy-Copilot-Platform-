"""Proposal / cover-letter draft generator (two streams).

- FREELANCE gigs  -> generate_proposal()     (uses proposal_master.md)
- JOB postings    -> generate_cover_letter()  (uses job_cover_letter.md)

Both write in Mert's voice: natural, plain, honest — never AI-sounding or salesy.
Output is plain text he can paste straight in (with minor edits if needed).
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import yaml

from ..llm import LLMError, call_llm

logger = logging.getLogger(__name__)

_NATURAL_TONE = """Write like a real, helpful person — not like an AI or a brochure.
Plain, simple English. Short sentences. Be honest and grounded (Mert is early in
his career). Never use buzzwords or AI cliches such as: "I am excited", "I would
love to", "passionate", "leverage", "robust", "seamless", "cutting-edge", "delve",
"great fit", "proven track record", "hit the ground running", "thrilled",
"I am confident that". No emojis, no markdown, no bold. Do not invent experience,
tools, numbers, or certifications that are not in the personal context."""

PROPOSAL_SYSTEM_PROMPT = (
    "You write short FREELANCE proposals on behalf of Ali Mert Ozdemir, who delivers "
    "energy & ESG analytics using his EnergyLens platform (Microsoft Fabric + Power BI).\n\n"
    + _NATURAL_TONE
    + "\n\nGoal: make the client feel understood and confident he can solve their "
    "problem. Follow the master template. LEAD with their problem, then give a clear "
    "solution roadmap (3-4 concrete steps) using the ONE closest EnergyLens capability. "
    "Do NOT quote a price or name a package; the priority is solving their problem. If "
    "money must be mentioned, only a soft minimum, briefly and last. Do NOT propose a "
    "call or meeting -- invite them to share more and let them choose the next step. "
    "Present EnergyLens as a platform he built (proof he can do the work). 150-220 words. "
    "Sign off: Best, Mert"
)

COVER_LETTER_SYSTEM_PROMPT = (
    "You write short, natural JOB cover letters on behalf of Ali Mert Ozdemir, who "
    "is applying for energy / data / sustainability roles. This is an EMPLOYMENT "
    "application — no prices, no packages, no freelance pitch language.\n\n"
    + _NATURAL_TONE
    + "\n\nCore message: he is early-career (junior) and honest about it, but genuinely "
    "driven -- he works hard, keeps learning, and is investing in himself to grow. "
    "Confident about effort and direction, humble about seniority; never inflated. "
    "Follow the template. 150-200 words. Sign off: Best regards, Ali Mert Ozdemir"
)


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
    """FREELANCE proposal. Returns (text, picked_package_id) or (None, None)."""
    personal = load_yaml(personal_yml_path)
    master = load_text(template_dir / "proposal_master.md")
    examples = _load_examples(template_dir)
    user_prompt = _build_proposal_prompt(
        personal=personal,
        master_template=master,
        examples=examples,
        job_title=job_title,
        job_description=job_description,
    )
    try:
        resp = call_llm(
            PROPOSAL_SYSTEM_PROMPT + "\n\n---\n\n" + user_prompt,
            temperature=0.5,
            max_output_tokens=900,
        )
    except LLMError as e:
        logger.error("Proposal LLM failed: %s", e)
        return None, None
    text = resp.text.strip()
    if "Mert" not in text[-200:]:
        text = text.rstrip() + "\n\nBest,\nMert"
    return text, _infer_picked_package(text, personal)


def generate_cover_letter(
    *,
    job_title: str,
    job_description: str,
    personal_yml_path: Path,
    template_dir: Path,
) -> Optional[str]:
    """JOB cover letter. Returns text or None on failure."""
    personal = load_yaml(personal_yml_path)
    template = load_text(template_dir / "job_cover_letter.md")
    user_prompt = _build_cover_letter_prompt(
        personal=personal,
        template=template,
        job_title=job_title,
        job_description=job_description,
    )
    try:
        resp = call_llm(
            COVER_LETTER_SYSTEM_PROMPT + "\n\n---\n\n" + user_prompt,
            temperature=0.5,
            max_output_tokens=700,
        )
    except LLMError as e:
        logger.error("Cover letter LLM failed: %s", e)
        return None
    text = resp.text.strip()
    if "Mert" not in text[-220:] and "Ali" not in text[-220:]:
        text = text.rstrip() + "\n\nBest regards,\nAli Mert Ozdemir"
    return text


def _load_examples(template_dir: Path) -> list[str]:
    examples = []
    for fname in ("example_csrd.md", "example_kpi.md", "example_fabric_audit.md", "example_hourly.md"):
        p = template_dir / fname
        if p.exists():
            examples.append(load_text(p))
    return examples


def _build_proposal_prompt(*, personal, master_template, examples, job_title, job_description):
    packages_block = "\n".join(
        f"- {p['id']}: {p['name']} — EUR {p['price_eur']} / {p['duration']}\n"
        f"  fits_when: {p['fits_when']}\n  summary: {p['summary'].strip()}"
        for p in personal.get("packages", [])
    )
    artifacts_block = "\n".join(
        f"- {a['id']} — {a['summary']}\n  fits_when: {a['fits_when']}"
        for a in personal.get("proof_artifacts", [])
    )
    hourly = personal.get("hourly_fallback", {})
    hourly_block = (
        f"Hourly fallback: EUR {hourly.get('hourly_eur', 60)}/hr, "
        f"EUR {hourly.get('daily_eur', 450)}/day. {hourly.get('notes', '')}"
    )
    examples_block = "\n\n---\n\n".join(examples) if examples else "(no examples)"
    return f"""## STRUCTURE & TONE

{master_template}

## PERSONAL CONTEXT

Positioning:
{personal.get('positioning', '').strip()}

Credentials:
{chr(10).join('- ' + c for c in personal.get('credentials', []))}

Productized packages:
{packages_block}

{hourly_block}

Proof artifacts (pick ONE that best matches this gig):
{artifacts_block}


## FEW-SHOT EXAMPLES (style reference for naturalness only)

{examples_block}

## GIG TO RESPOND TO

Title: {job_title}

Description:
{job_description[:5000]}

## YOUR TASK

Write the proposal now. Plain text only. 150-230 words.
"""


def _build_cover_letter_prompt(*, personal, template, job_title, job_description):
    return f"""## STRUCTURE & TONE

{template}

## PERSONAL CONTEXT (use only what is true here)

Positioning:
{personal.get('positioning', '').strip()}

Credentials:
{chr(10).join('- ' + c for c in personal.get('credentials', []))}

Real background to draw on:
- B.Sc. Energy Systems Engineering (Yasar University, Izmir, 2022)
- M.Sc. Energy Management student in Berlin (BSBI)
- Microsoft Certified: Fabric Analytics Engineer (DP-600); Google Business Intelligence Certificate
- Energy engineer on solar PV design at Elegant Enerji (2022-2023)
- Wind turbine O&M internship at Enercon
- EnergyLens: a personal end-to-end Microsoft Fabric + Power BI project (energy KPIs, Scope 1/2/3, anomaly detection, solar and battery) built to go deep on the stack

## JOB TO APPLY FOR

Title: {job_title}

Description:
{job_description[:5000]}

## YOUR TASK

Write the cover letter now. Plain text only. 150-210 words.
"""


def _infer_picked_package(proposal_text: str, personal: dict) -> Optional[str]:
    for p in personal.get("packages", []):
        pid = p["id"]
        if pid.lower() in proposal_text.lower() or p["name"].lower() in proposal_text.lower():
            return pid
    if "hourly" in proposal_text.lower():
        return "hourly"
    return None
