"""
Smoke test for Fabric Power BI DAX ExecuteQueries endpoint.

Validates that:
  1. The service principal can acquire a Power BI token (MSAL client credentials).
  2. We can resolve the dataset_id dynamically from the report (same pattern
     as /embed/token endpoint).
  3. We can POST a DAX query to /datasets/{id}/executeQueries and receive a
     tabular JSON response.

Run:
    cd web-app/backend
    .\\venv\\Scripts\\Activate.ps1   # Windows
    # source venv/bin/activate        # macOS/Linux
    python -m scripts.smoke_dax

Expected: a JSON response containing one row with max_date, total_kwh_30d,
total_cost_30d, total_co2_30d, buildings_count keys.
"""

import json
import os
import sys
from pathlib import Path

import httpx
import msal
from dotenv import load_dotenv

# Load .env from the backend root (one level up from scripts/)
BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env", override=True)

TENANT_ID = os.environ["PBI_TENANT_ID"]
CLIENT_ID = os.environ["PBI_CLIENT_ID"]
CLIENT_SECRET = os.environ["PBI_CLIENT_SECRET"]
WORKSPACE_ID = os.environ["PBI_WORKSPACE_ID"]
REPORT_ID = os.environ["PBI_REPORT_ID"]

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
PBI_SCOPE = ["https://analysis.windows.net/powerbi/api/.default"]

# Sample DAX — verifies we can read the date table, call existing measures,
# and use a rolling-30-day window pattern. Mirrors what /portfolio/kpis will do.
DAX_QUERY = """
EVALUATE
VAR _maxDate = MAX(gold_kpi_daily[date])
RETURN
ROW(
    "max_date",        _maxDate,
    "total_kwh_30d",   CALCULATE([Total Consumption kWh],   DATESINPERIOD(gold_kpi_daily[date], _maxDate, -30, DAY)),
    "total_cost_30d",  CALCULATE([Total Energy Cost EUR],   DATESINPERIOD(gold_kpi_daily[date], _maxDate, -30, DAY)),
    "total_co2_30d",   CALCULATE([Total CO2 Emissions kg],  DATESINPERIOD(gold_kpi_daily[date], _maxDate, -30, DAY)),
    "buildings_count", [Buildings Count]
)
""".strip()


def get_sp_token() -> str:
    """Acquire a service principal access token for the Power BI API."""
    app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET,
    )
    result = app.acquire_token_for_client(scopes=PBI_SCOPE)
    if "access_token" not in result:
        raise RuntimeError(
            f"MSAL token acquisition failed: "
            f"{result.get('error')} - {result.get('error_description')}"
        )
    return result["access_token"]


def get_dataset_id(token: str) -> str:
    """Resolve the dataset_id behind the report (DirectLake semantic model)."""
    url = (
        f"https://api.powerbi.com/v1.0/myorg/groups/{WORKSPACE_ID}"
        f"/reports/{REPORT_ID}"
    )
    r = httpx.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()["datasetId"]


def execute_dax(token: str, dataset_id: str, query: str) -> dict:
    """POST a DAX query to ExecuteQueries and return parsed JSON."""
    url = (
        f"https://api.powerbi.com/v1.0/myorg/groups/{WORKSPACE_ID}"
        f"/datasets/{dataset_id}/executeQueries"
    )
    body = {
        "queries": [{"query": query}],
        "serializerSettings": {"includeNulls": True},
    }
    r = httpx.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=30,
    )
    # Print body on error so we can read the DAX validation message
    if r.status_code >= 400:
        print(f"\n[ERROR] HTTP {r.status_code}", file=sys.stderr)
        print(r.text, file=sys.stderr)
        r.raise_for_status()
    return r.json()


def main() -> int:
    print("[1/3] Acquiring service principal token...")
    token = get_sp_token()
    print(f"      OK ({len(token)} chars)")

    print("[2/3] Resolving datasetId from report...")
    dataset_id = get_dataset_id(token)
    print(f"      datasetId = {dataset_id}")

    print("[3/3] Executing DAX query...")
    result = execute_dax(token, dataset_id, DAX_QUERY)

    print("\n--- Raw response ---")
    print(json.dumps(result, indent=2, default=str))

    # Pretty-print the first row if the shape is what we expect
    try:
        rows = result["results"][0]["tables"][0]["rows"]
        print("\n--- Parsed first row ---")
        for k, v in rows[0].items():
            print(f"  {k:25s} = {v}")
    except (KeyError, IndexError):
        print("\n[WARN] Response shape did not match expected layout — see raw above.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
