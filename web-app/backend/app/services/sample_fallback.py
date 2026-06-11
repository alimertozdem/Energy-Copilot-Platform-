"""Offline sample-data fallback for the logged-in data pages.

When the Fabric SQL endpoint is unreachable (e.g. Azure Container Apps egress
can't complete the SQL Redirect), the data routers fall back to a snapshot of
REAL query results captured from a machine WITH Fabric access (see
scripts/capture_sample_data.py). The fallback is gated to the captured building
scope (set equality) so ONLY the demo/sample org sees it — any other org keeps
its real (often empty) state. The public /demo page is unaffected (it has its
own fallback in demo_data.py). fabric_sql is NOT touched here.

A short circuit breaker remembers when Fabric last failed and (for the demo
scope, which has a snapshot) skips the slow Fabric probe entirely, so page-to-
page navigation is instant after the first miss. Per-process state; persists
across requests with min-replicas=1.
"""
import json
import logging
import os
import time
from typing import Any, Callable

import pyodbc

logger = logging.getLogger(__name__)

_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "sample_fallback.json")

try:
    with open(_PATH, encoding="utf-8") as _f:
        _DATA: dict[str, Any] = json.load(_f)
    _SCOPE: set[str] = set(_DATA.get("scope", []))
    logger.info(
        "Sample fallback loaded: %d page(s), %d-building scope",
        max(len(_DATA) - 1, 0), len(_SCOPE),
    )
except FileNotFoundError:
    _DATA, _SCOPE = {}, set()
except Exception as _e:  # corrupt file -> behave as if absent
    logger.warning("Sample fallback load failed: %s", _e)
    _DATA, _SCOPE = {}, set()

_BREAKER_WINDOW = float(os.getenv("FABRIC_BREAKER_WINDOW", "600") or 600)
_down_until = 0.0


def scope_matches(fabric_ids) -> bool:
    """True only when the request's visible scope equals the captured demo scope."""
    return bool(_SCOPE) and set(fabric_ids) == _SCOPE


def _snapshot(page_key: str, schema):
    data = _DATA.get(page_key)
    return schema.model_validate(data) if data is not None else None


def serve(page_key: str, schema, fabric_ids, fetch: Callable[[], Any]):
    """Run fetch(); if Fabric is unreachable AND this is the demo scope, return
    the captured sample response. The circuit breaker skips the slow probe once
    Fabric is known down. Non-demo scopes always re-raise (graceful 503).
    """
    global _down_until
    # Fast path: Fabric recently down + demo scope + snapshot present -> serve now.
    if time.time() < _down_until and scope_matches(fabric_ids):
        snap = _snapshot(page_key, schema)
        if snap is not None:
            return snap
    try:
        return fetch()
    except pyodbc.Error:
        _down_until = time.time() + _BREAKER_WINDOW
        if scope_matches(fabric_ids):
            snap = _snapshot(page_key, schema)
            if snap is not None:
                logger.warning(
                    "Fabric unavailable; serving sample fallback for '%s'.", page_key
                )
                return snap
        raise
