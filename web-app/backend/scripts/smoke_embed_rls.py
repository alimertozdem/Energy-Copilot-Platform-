"""CP-2 smoke test: does the DirectLake semantic model accept a *dynamic* RLS
embed token (effectiveIdentity + customData)?

This is the decisive de-risk for CP-2's embedded-report isolation. Memory
`feedback_pbi_directlake_rls.md` records that DirectLake once REJECTED the V2
GenerateToken `identities[]` block — so before we wire server-side RLS into the
logged-in /embed/token, we prove the mechanism live here.

It is READ-ONLY: it acquires the service-principal token, GETs the report
metadata, and POSTs GenerateToken with an effectiveIdentity carrying a
`customData` building-id list. It mutates nothing.

Run from web-app/backend with your .env loaded:

    RLS_CUSTOMDATA="B001"        python scripts/smoke_embed_rls.py
    RLS_CUSTOMDATA="B001|B004"   python scripts/smoke_embed_rls.py

Reads the same env the app uses:
    PBI_TENANT_ID  PBI_CLIENT_ID  PBI_CLIENT_SECRET  PBI_WORKSPACE_ID  PBI_REPORT_ID
Optional:
    RLS_ROLE        (default "CustomerRLS" — must match the role you created in the model)
    RLS_CUSTOMDATA  (default "B001" — the |-delimited building-id list to test)

Interpreting the result:
    STATUS 200  -> DirectLake ACCEPTS dynamic RLS. Proceed to wire it (doc §3).
    STATUS 400  -> still blocked (read the message). Use a fallback (doc §4).
"""
from __future__ import annotations

import os
import sys

import httpx
import msal

try:
    # Best-effort: load .env so the script works standalone, like the app does.
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv is optional for this script
    pass

PBI_SCOPE = ["https://analysis.windows.net/powerbi/api/.default"]
PBI_API_BASE = "https://api.powerbi.com/v1.0/myorg"


def _require(key: str) -> str:
    val = os.getenv(key)
    if not val:
        sys.exit(f"❌ Missing required env var: {key}")
    return val


def acquire_sp_token(tenant_id: str, client_id: str, client_secret: str) -> str:
    app = msal.ConfidentialClientApplication(
        client_id=client_id,
        client_credential=client_secret,
        authority=f"https://login.microsoftonline.com/{tenant_id}",
    )
    result = app.acquire_token_for_client(scopes=PBI_SCOPE)
    if "access_token" not in result:
        err = result.get("error_description") or result.get("error") or "unknown"
        sys.exit(f"❌ Azure AD auth failed: {err}")
    return result["access_token"]


def main() -> None:
    tenant_id = _require("PBI_TENANT_ID")
    client_id = _require("PBI_CLIENT_ID")
    client_secret = _require("PBI_CLIENT_SECRET")
    workspace_id = _require("PBI_WORKSPACE_ID")
    report_id = _require("PBI_REPORT_ID")
    role = os.getenv("RLS_ROLE", "CustomerRLS")
    custom_data = os.getenv("RLS_CUSTOMDATA", "B001")

    print(f"→ role={role!r}  customData={custom_data!r}")

    token = acquire_sp_token(tenant_id, client_id, client_secret)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # 1) Report metadata — datasetId is required in the V2 body for DirectLake.
    report_url = f"{PBI_API_BASE}/groups/{workspace_id}/reports/{report_id}"
    rep = httpx.get(report_url, headers=headers, timeout=30)
    if rep.status_code != 200:
        sys.exit(f"❌ get-report failed ({rep.status_code}): {rep.text}")
    report = rep.json()
    dataset_id = report["datasetId"]
    embed_url = report.get("embedUrl")

    # 2) V2 GenerateToken WITH a dynamic effectiveIdentity (the thing under test).
    body = {
        "datasets": [{"id": dataset_id}],
        "reports": [{"id": report_id}],
        "targetWorkspaces": [{"id": workspace_id}],
        "identities": [
            {
                "username": "rls-smoke@energylens.app",
                "roles": [role],
                "datasets": [dataset_id],
                "customData": custom_data,
            }
        ],
    }
    resp = httpx.post(f"{PBI_API_BASE}/GenerateToken", headers=headers, json=body, timeout=30)

    print(f"\nSTATUS {resp.status_code}")
    print(resp.text[:1000])

    if resp.status_code == 200:
        print(
            "\n✅ DirectLake ACCEPTED effectiveIdentity + customData."
            "\n   The historical identities[] block is gone — proceed to wire it (doc §3)."
            f"\n   embed_url: {embed_url}"
            "\n   (Optional: render this token in a scratch viewer and confirm only the"
            "\n    customData buildings appear. Step A already proved the DAX cascade.)"
        )
        sys.exit(0)
    else:
        print(
            "\n❌ Rejected. This is likely the historical DirectLake identities[] block."
            "\n   Do NOT wire server-side RLS yet — use a fallback (doc §4, recommended B1)."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
