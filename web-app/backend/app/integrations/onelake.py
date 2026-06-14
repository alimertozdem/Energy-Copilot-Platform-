"""OneLake bronze writer for self-serve Fabric bridging (Layer 3, Phase 3.2).

Lands a building's baseline consumption as a CSV file in the gold Lakehouse's
OneLake `Files/bridge_inbox/{building_uuid}/consumption.csv`. The parameterised
bridge notebook (notebooks/bridge/40_bridge_baseline.py) reads it from there.

Why CSV + raw DFS REST (not parquet, not an Azure SDK):
  * CSV needs no pyarrow/pandas — these monthly tables are tiny (≤ a few hundred
    rows), so format efficiency is irrelevant.
  * The ADLS Gen2 DFS REST API (create → append → flush) is reachable with the
    httpx client already in the backend, so no new dependency.

OneLake speaks the ADLS Gen2 DFS dialect at onelake.dfs.fabric.microsoft.com with
path `/{workspaceId}/{lakehouseId}/Files/...`. Auth = storage-scope SP token.
All failures raise OneLakeError so the orchestrator can surface a clean message.
"""
from __future__ import annotations

import csv
import io
import logging
import os
from urllib.parse import quote

import httpx

from app.integrations.azure_auth import STORAGE_SCOPE, AzureAuthError, acquire_token

logger = logging.getLogger(__name__)


class OneLakeError(RuntimeError):
    """Raised when a OneLake write fails."""


def _host() -> str:
    return os.getenv("FABRIC_ONELAKE_HOST", "onelake.dfs.fabric.microsoft.com")


def _require(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise OneLakeError(f"Server misconfigured: missing {name}")
    return val


def build_bronze_path(building_uuid: str) -> str:
    """The abfss-style HTTPS path the notebook will read.

    Mirrors what `write_bronze_csv` uploads. Returned so the orchestrator can pass
    it to the notebook as the `bronze_path` parameter.
    """
    host = _host()
    workspace = _require("FABRIC_WORKSPACE_ID")
    lakehouse = _require("FABRIC_LAKEHOUSE_ID")
    rel = f"Files/bridge_inbox/{building_uuid}/consumption.csv"
    # Spark reads OneLake via the abfss:// scheme. The https:// form is the DFS
    # REST endpoint used to WRITE the file (write_bronze_csv) — it is NOT a
    # Spark-readable filesystem path, so the notebook must get the abfss form.
    return f"abfss://{workspace}@{host}/{lakehouse}/{rel}"


def rows_to_csv_bytes(rows: list[dict]) -> bytes:
    """Serialise [{period_month, kwh, cost_eur}] to CSV bytes with a header.

    `cost_eur` may be None -> emitted as an empty field (notebook coerces null).
    """
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["period_month", "kwh", "cost_eur"])
    for r in rows:
        writer.writerow(
            [
                r.get("period_month", ""),
                r.get("kwh", ""),
                "" if r.get("cost_eur") in (None, "") else r.get("cost_eur"),
            ]
        )
    return buf.getvalue().encode("utf-8")


def _dfs_url(building_uuid: str) -> str:
    """The DFS REST endpoint for the building's CSV (path-encoded)."""
    host = _host()
    workspace = _require("FABRIC_WORKSPACE_ID")
    lakehouse = _require("FABRIC_LAKEHOUSE_ID")
    rel = quote(f"Files/bridge_inbox/{building_uuid}/consumption.csv")
    return f"https://{host}/{workspace}/{lakehouse}/{rel}"


def write_bronze_csv(building_uuid: str, rows: list[dict]) -> str:
    """Create → append → flush the building's bronze CSV in OneLake.

    Returns the HTTPS path the notebook should read (build_bronze_path).
    Raises OneLakeError on any failure.
    """
    if not rows:
        raise OneLakeError("Refusing to land an empty bronze file (no rows).")

    try:
        token = acquire_token(STORAGE_SCOPE)
    except AzureAuthError as e:
        raise OneLakeError(str(e)) from e

    data = rows_to_csv_bytes(rows)
    url = _dfs_url(building_uuid)
    headers = {"Authorization": f"Bearer {token}", "x-ms-version": "2023-11-03"}

    try:
        with httpx.Client(timeout=60) as client:
            # 1) create (truncates any prior file -> idempotent re-bridge)
            r = client.put(f"{url}?resource=file", headers=headers)
            if r.status_code not in (201, 202):
                raise OneLakeError(
                    f"OneLake create failed ({r.status_code}): {r.text[:300]}"
                )
            # 2) append the bytes at offset 0
            r = client.patch(
                f"{url}?action=append&position=0",
                headers={**headers, "Content-Type": "application/octet-stream"},
                content=data,
            )
            if r.status_code not in (200, 202):
                raise OneLakeError(
                    f"OneLake append failed ({r.status_code}): {r.text[:300]}"
                )
            # 3) flush to commit the file at its full length
            r = client.patch(
                f"{url}?action=flush&position={len(data)}", headers=headers
            )
            if r.status_code not in (200, 202):
                raise OneLakeError(
                    f"OneLake flush failed ({r.status_code}): {r.text[:300]}"
                )
    except httpx.HTTPError as e:
        raise OneLakeError(f"OneLake request error: {e}") from e

    logger.info("Landed bronze CSV for %s (%d bytes)", building_uuid, len(data))
    return build_bronze_path(building_uuid)
