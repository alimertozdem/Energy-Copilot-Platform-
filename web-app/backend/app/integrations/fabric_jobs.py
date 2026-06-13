"""Fabric REST client — trigger + poll the parameterised bridge notebook.

Phase 3.2 of self-serve bridging. Uses the "run on-demand item job" API:
  POST /v1/workspaces/{ws}/items/{notebookId}/jobs/instances?jobType=RunNotebook
  -> 202 Accepted, Location header points at the job instance to poll
  GET  {location}  -> { "status": "NotStarted|InProgress|Completed|Failed|..." }

Requires an ACTIVE Fabric capacity attached to the workspace (see
docs/architecture/fabric-bridge-setup.md §6). Without capacity the trigger returns
an error, which the orchestrator maps to a clean "capacity unavailable" message —
it does NOT crash the request.

All public functions raise FabricJobError on failure.
"""
from __future__ import annotations

import logging
import os
import time

import httpx

from app.integrations.azure_auth import FABRIC_API_SCOPE, AzureAuthError, acquire_token

logger = logging.getLogger(__name__)

FABRIC_API_BASE = "https://api.fabric.microsoft.com/v1"

# Terminal job states per the Fabric Job Scheduler API.
_TERMINAL_OK = {"Completed"}
_TERMINAL_FAIL = {"Failed", "Cancelled", "Deduped"}


class FabricJobError(RuntimeError):
    """Raised when triggering or polling a Fabric job fails."""


def _require(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise FabricJobError(f"Server misconfigured: missing {name}")
    return val


def _headers() -> dict:
    try:
        token = acquire_token(FABRIC_API_SCOPE)
    except AzureAuthError as e:
        raise FabricJobError(str(e)) from e
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def trigger_notebook(notebook_id: str, parameters: dict) -> str:
    """Start a RunNotebook job for an EXPLICIT notebook id with parameters.

    `parameters` is a flat {name: value} dict passed as strings via the notebook's
    parameter cell. Returns the job-instance polling URL (the Location header).
    Raises FabricJobError (e.g. bad id, or no capacity attached). This is the
    generic primitive the orchestrator uses to chain baseline + report notebooks.
    """
    workspace = _require("FABRIC_WORKSPACE_ID")
    if not notebook_id:
        raise FabricJobError("trigger_notebook: empty notebook_id")
    url = (
        f"{FABRIC_API_BASE}/workspaces/{workspace}"
        f"/items/{notebook_id}/jobs/instances?jobType=RunNotebook"
    )
    # Fabric expects parameters as {name: {value, type}}.
    body = {
        "executionData": {
            "parameters": {
                k: {"value": "" if v is None else str(v), "type": "string"}
                for k, v in parameters.items()
            }
        }
    }
    try:
        with httpx.Client(timeout=60) as client:
            r = client.post(url, headers=_headers(), json=body)
    except httpx.HTTPError as e:
        raise FabricJobError(f"Fabric trigger request error: {e}") from e

    if r.status_code not in (200, 202):
        raise FabricJobError(
            f"Fabric job trigger failed ({r.status_code}): {r.text[:300]}"
        )
    location = r.headers.get("Location")
    if not location:
        raise FabricJobError("Fabric job trigger returned no Location header.")
    logger.info("Triggered notebook %s job: %s", notebook_id, location)
    return location


def trigger_bridge_notebook(parameters: dict) -> str:
    """Start the baseline bridge notebook (env FABRIC_BRIDGE_NOTEBOOK_ID)."""
    return trigger_notebook(_require("FABRIC_BRIDGE_NOTEBOOK_ID"), parameters)


def get_job_status(location: str) -> dict:
    """GET the job instance; returns the parsed JSON ({'status': ...})."""
    try:
        with httpx.Client(timeout=30) as client:
            r = client.get(location, headers=_headers())
    except httpx.HTTPError as e:
        raise FabricJobError(f"Fabric status request error: {e}") from e
    if r.status_code != 200:
        raise FabricJobError(
            f"Fabric job status failed ({r.status_code}): {r.text[:300]}"
        )
    return r.json()


def poll_until_done(
    location: str, *, timeout_s: int = 900, interval_s: int = 10
) -> dict:
    """Poll the job until it reaches a terminal state or timeout.

    Returns the final status dict on success. Raises FabricJobError on a failed
    terminal state or timeout, so the orchestrator records the bridge as failed.
    """
    deadline = time.time() + timeout_s
    last: dict = {}
    while time.time() < deadline:
        last = get_job_status(location)
        status = last.get("status", "")
        if status in _TERMINAL_OK:
            logger.info("Bridge job completed: %s", location)
            return last
        if status in _TERMINAL_FAIL:
            raise FabricJobError(
                f"Bridge job ended in {status}: "
                f"{last.get('failureReason') or last}"
            )
        time.sleep(interval_s)
    raise FabricJobError(
        f"Bridge job did not finish within {timeout_s}s (last status: "
        f"{last.get('status', 'unknown')})"
    )
