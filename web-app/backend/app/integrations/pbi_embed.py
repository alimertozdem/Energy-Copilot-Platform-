"""Power BI embed token helpers (V2 API, DirectLake-compatible).

This module isolates the two Power BI REST calls needed to render an embedded
report:
  1. `acquire_service_principal_token()` -- MSAL client-credentials flow to
     get a bearer token for the Power BI REST API.
  2. `generate_embed_token()` -- POST /v1.0/myorg/GenerateToken (V2 form) to
     get a short-lived embed token bound to a report + dataset + optional
     RLS effectiveIdentity.

Why a dedicated module?
  main.py has the original `/embed/token` endpoint inline. Refactoring it is
  V1.5 work. For Day 17 we need a parallel public endpoint with RLS
  effectiveIdentity support -- this module is the clean wrapper used by
  /demo/embed/token. main.py keeps working unchanged.

Why V2 GenerateToken?
  DirectLake semantic models (the kind our 9-page report uses) reject the V1
  embed token endpoint with "Embedding a DirectLake dataset is not supported".
  V2 GenerateToken at /v1.0/myorg/GenerateToken with body datasets/reports
  works correctly. See memory `day_15_completion.md` for the original
  diagnosis.
"""
from __future__ import annotations

import os
import threading
from typing import Iterable

import httpx
import msal
from fastapi import HTTPException


PBI_SCOPE: list[str] = ["https://analysis.windows.net/powerbi/api/.default"]
PBI_API_BASE = "https://api.powerbi.com/v1.0/myorg"


def _require_env(key: str) -> str:
    """Read a required env var or raise a 500 with a useful message."""
    val = os.getenv(key)
    if not val:
        raise HTTPException(
            status_code=500, detail=f"Server misconfigured: missing {key}"
        )
    return val


# Module-level singletons (perf). Building a fresh ConfidentialClientApplication
# on every call threw away MSAL's in-memory token cache -> a full Azure AD round
# trip per embed token. A shared app reuses the cached SP token until ~5 min
# before expiry, then refreshes automatically. Report embedUrl/datasetId never
# change either, so they are cached per (workspace, report).
_MSAL_APP: msal.ConfidentialClientApplication | None = None
_MSAL_LOCK = threading.Lock()
_REPORT_META_CACHE: dict[tuple[str, str], tuple[str, str]] = {}


def _get_msal_app() -> msal.ConfidentialClientApplication:
    global _MSAL_APP
    if _MSAL_APP is None:
        with _MSAL_LOCK:
            if _MSAL_APP is None:
                tenant_id = _require_env("PBI_TENANT_ID")
                client_id = _require_env("PBI_CLIENT_ID")
                client_secret = _require_env("PBI_CLIENT_SECRET")
                _MSAL_APP = msal.ConfidentialClientApplication(
                    client_id=client_id,
                    client_credential=client_secret,
                    authority=f"https://login.microsoftonline.com/{tenant_id}",
                )
    return _MSAL_APP


def acquire_service_principal_token() -> str:
    """Bearer token for the Power BI REST API (cached SP token via shared MSAL app)."""
    result = _get_msal_app().acquire_token_for_client(scopes=PBI_SCOPE)

    if "access_token" not in result:
        err = (
            result.get("error_description")
            or result.get("error")
            or "Unknown auth error"
        )
        raise HTTPException(status_code=500, detail=f"Azure auth failed: {err}")
    return result["access_token"]


def _fetch_report_metadata(
    client: httpx.AsyncClient,
    workspace_id: str,
    report_id: str,
    azure_token: str,
) -> dict:
    """GET the report's embedUrl + datasetId. DirectLake needs datasetId in V2 body."""
    url = f"{PBI_API_BASE}/groups/{workspace_id}/reports/{report_id}"
    headers = {"Authorization": f"Bearer {azure_token}"}
    resp = httpx.get(url, headers=headers, timeout=30)
    if resp.status_code != 200:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Power BI get-report failed: {resp.text}",
        )
    return resp.json()


async def generate_embed_token(
    *,
    workspace_id: str,
    report_id: str,
    rls_username: str | None = None,
    rls_roles: Iterable[str] | None = None,
    rls_custom_data: str | None = None,
) -> dict:
    """Generate a V2 embed token for a report, optionally with RLS identity.

    Returns:
        dict with keys: embed_token, embed_url, expiration, report_id

    When rls_username + rls_roles are supplied, the embed token carries an
    `effectiveIdentity` block. Power BI applies the named RLS roles on the
    dataset to the supplied username. For our use case (public /demo), the
    `Demo` role on the dataset restricts visibility to B001-B006 via a DAX
    filter on silver_building_master.

    Raises HTTPException on Power BI API errors (auth, missing role, etc.).
    """
    azure_token = acquire_service_principal_token()
    headers = {
        "Authorization": f"Bearer {azure_token}",
        "Content-Type": "application/json",
    }

    # embedUrl + datasetId never change for a report -> serve from module cache
    # and skip the GET /reports/{id} round-trip on every token request.
    meta_key = (workspace_id, report_id)
    cached_meta = _REPORT_META_CACHE.get(meta_key)

    async with httpx.AsyncClient(timeout=30) as client:
        if cached_meta is not None:
            embed_url, dataset_id = cached_meta
        else:
            # 1) Get report metadata (datasetId + embedUrl)
            report_url = f"{PBI_API_BASE}/groups/{workspace_id}/reports/{report_id}"
            report_resp = await client.get(report_url, headers=headers)
            if report_resp.status_code != 200:
                raise HTTPException(
                    status_code=report_resp.status_code,
                    detail=f"Power BI get-report failed: {report_resp.text}",
                )
            report_data = report_resp.json()
            embed_url = report_data["embedUrl"]
            dataset_id = report_data["datasetId"]
            _REPORT_META_CACHE[meta_key] = (embed_url, dataset_id)

        # 2) Build V2 GenerateToken body. Prefer NO effectiveIdentity (no RLS =
        # full data -- what the public demo wants). Only if the dataset ENFORCES
        # an RLS role (non-200 without an identity) AND the caller supplied one
        # do we retry WITH it as a fallback. (The authed /embed/token path in
        # main.py has its own copy of this logic.)
        base_body: dict = {
            "datasets": [{"id": dataset_id}],
            "reports": [{"id": report_id}],
            "targetWorkspaces": [{"id": workspace_id}],
        }
        identity: dict | None = None
        if rls_username and rls_roles:
            identity = {
                "username": rls_username,
                "roles": list(rls_roles),
                "datasets": [dataset_id],
            }
            if rls_custom_data is not None:
                identity["customData"] = rls_custom_data

        token_url = f"{PBI_API_BASE}/GenerateToken"
        token_resp = await client.post(token_url, headers=headers, json=base_body)
        if token_resp.status_code != 200 and identity is not None:
            token_resp = await client.post(
                token_url, headers=headers,
                json={**base_body, "identities": [identity]},
            )
        if token_resp.status_code != 200:
            raise HTTPException(
                status_code=token_resp.status_code,
                detail=f"Power BI GenerateToken failed: {token_resp.text}",
            )
        token_data = token_resp.json()

    return {
        "embed_token": token_data["token"],
        "embed_url": embed_url,
        "expiration": token_data["expiration"],
        "report_id": report_id,
    }
