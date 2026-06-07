"""Tier 3 — LLM semantic score.

Returns an integer 1-10 plus a 1-sentence reasoning. Called only AFTER
keyword + budget filters pass, so we burn LLM tokens only on plausibly
relevant jobs.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..llm import LLMError, call_llm, parse_json_response


SCORING_PROMPT = """You are screening freelance job postings for a specialist who builds CSRD/ESG \
reporting dashboards and energy analytics on Microsoft Fabric + Power BI.

The specialist is best-fit for jobs involving:
- CSRD / ESRS / GHG Protocol / Scope 1, 2, 3 emissions reporting
- Building energy analytics, EnPI, kWh/m², EPC compliance
- Microsoft Fabric (lakehouse, Direct Lake, OneLake, EventStream, KQL)
- Power BI semantic modeling, DAX optimization, embedded analytics
- IoT building monitoring (BACnet, Modbus, MQTT)
- Battery / energy storage ROI modeling for commercial buildings

The specialist is NOT a fit for:
- Tableau / Looker / Qlik specialist roles
- Marketing/ecommerce/social-media analytics
- Generic data entry, transcription, video editing
- Blockchain / crypto / web3 energy claims
- Pure software engineering with no analytics or sustainability angle

Score this job 1-10 on fit:
- 10 = perfect (CSRD + Fabric/PBI explicitly named)
- 8-9 = strong (energy/sustainability + MS BI tools)
- 6-7 = moderate (Power BI generic with tangential domain, or energy generic with BI tools)
- 4-5 = weak (one keyword overlap but core role is something else)
- 1-3 = poor fit

Return ONLY a JSON object: {{"score": <int 1-10>, "reasoning": "<one short sentence>"}}

Job title: {title}

Job description:
{description}
"""


@dataclass
class LLMScoreResult:
    score: int
    reasoning: str
    provider: Optional[str] = None


def score_job(title: str, description: str, *, temperature: float = 0.2) -> LLMScoreResult:
    """Score a job using the LLM. Returns score 1-10 + reasoning.

    On LLM failure, returns score=0 with reasoning='llm_unavailable'.
    Caller should treat 0 as "skip and log".
    """
    prompt = SCORING_PROMPT.format(
        title=title.strip(),
        description=description.strip()[:6000],  # truncate to keep token use small
    )

    try:
        resp = call_llm(prompt, temperature=temperature, max_output_tokens=200, json_mode=True)
    except LLMError as e:
        return LLMScoreResult(score=0, reasoning=f"llm_unavailable: {e}")

    try:
        data = parse_json_response(resp.text)
        score = int(data.get("score", 0))
        reasoning = str(data.get("reasoning", "")).strip()
        # clamp
        score = max(0, min(10, score))
        return LLMScoreResult(score=score, reasoning=reasoning, provider=resp.provider)
    except Exception as e:
        return LLMScoreResult(score=0, reasoning=f"parse_error: {e}")
