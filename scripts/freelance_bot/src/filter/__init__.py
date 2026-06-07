"""Three-tier filter engine.

LLM-based scoring is imported lazily so the rest of the package works even
when optional deps (httpx) are missing — useful for tests.
"""
from .budget import BudgetResult, check_budget
from .keyword import KeywordResult, check_keywords


def score_job(*args, **kwargs):
    """Lazy proxy — imports LLM client only when actually called."""
    from .llm_score import score_job as _score_job
    return _score_job(*args, **kwargs)


__all__ = [
    "BudgetResult", "check_budget",
    "KeywordResult", "check_keywords",
    "score_job",
]
