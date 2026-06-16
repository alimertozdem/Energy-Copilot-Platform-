"""Tier 3 — LLM semantic score (EnergyLens-fit).

Returns an integer 1-10 + one-sentence reasoning. Scores ONLY how directly the
job can be delivered using Mert's EnergyLens platform. Called after keyword +
budget pass, so tokens are spent only on plausibly relevant jobs.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..llm import LLMError, call_llm, parse_json_response


SCORING_PROMPT = """You screen job/gig postings for Ali Mert, who delivers work using his own platform \
"EnergyLens" — a Microsoft Fabric + Power BI system for energy & ESG analytics in commercial buildings. \
Score ONLY how directly he could deliver THIS posting using EnergyLens's existing capabilities.

EnergyLens already does (deliverable now):
- Energy KPI dashboards: kWh/m2 (EUI), EnPI, peak demand, cost, baseline-vs-actual, weather/occupancy normalization
- ESG / sustainability reporting: GHG Protocol Scope 1/2/3, CSRD / ESRS-E1-aligned views, EU Taxonomy
- EU building compliance: EPC ratings, MEPS / EPBD renovation risk, CRREM stranding pathways
- Power BI / Microsoft Fabric: semantic modeling, DAX, Row-Level Security, embedded, medallion lakehouse (Python/PySpark)
- Building energy & IoT monitoring: BACnet / Modbus / MQTT, anomaly detection with cost impact, demand forecasting
- On-site solar PV and battery dispatch economics

Score 1-10 by how directly EnergyLens solves the posting:
- 9-10: squarely in the list above (e.g. CSRD/ESG reporting dashboard, building energy KPIs in Power BI, EPC/CRREM analysis) — fast to deliver.
- 7-8: strongly adjacent — energy/sustainability data + Power BI/Fabric, where EnergyLens is a clear head start.
- 4-6: partial overlap only (generic Power BI / data work with weak or no energy/ESG/building angle).
- 1-3: outside EnergyLens (generic software/data/marketing/sales or unrelated domains), OR the posting looks like spam / a ghost listing / MLM.

Be strict: if energy, sustainability, or buildings is NOT central to the work, it is at most a 5.

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
    """Score a job on EnergyLens fit (1-10). On LLM failure returns score=0
    with reasoning='llm_unavailable'. Caller treats 0 as skip-and-log."""
    prompt = SCORING_PROMPT.format(
        title=title.strip(),
        description=description.strip()[:6000],
    )
    try:
        resp = call_llm(prompt, temperature=temperature, max_output_tokens=200, json_mode=True)
    except LLMError as e:
        return LLMScoreResult(score=0, reasoning=f"llm_unavailable: {e}")
    try:
        data = parse_json_response(resp.text)
        score = int(data.get("score", 0))
        reasoning = str(data.get("reasoning", "")).strip()
        score = max(0, min(10, score))
        return LLMScoreResult(score=score, reasoning=reasoning, provider=resp.provider)
    except Exception as e:
        return LLMScoreResult(score=0, reasoning=f"parse_error: {e}")
