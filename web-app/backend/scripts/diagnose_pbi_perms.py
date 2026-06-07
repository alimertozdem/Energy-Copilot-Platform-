"""
Diagnose PowerBI 401 layer-by-layer.

Runs 4 API calls in sequence, each probing a different permission layer:
  Step 1 — GET /groups
           Workspace visibility: is the SP a member of ANY workspace?
  Step 2 — GET /groups/{ws}/datasets
           Dataset list visibility: can the SP enumerate datasets in OUR workspace?
  Step 3 — GET /groups/{ws}/datasets/{id}
           Single dataset visibility: can the SP read THIS specific dataset?
  Step 4 — POST /datasets/{id}/executeQueries
           DAX execution: can the SP actually run a query?

Each step prints HTTP status + a snippet of the response body.
The first failing step tells us which permission layer is closed.

Run:
    python -m scripts.diagnose_pbi_perms
"""

import json
import os
import sys
from pathlib import Path

import httpx
import msal
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env", override=True)

TENANT_ID = os.environ["PBI_TENANT_ID"]
CLIENT_ID = os.environ["PBI_CLIENT_ID"]
CLIENT_SECRET = os.environ["PBI_CLIENT_SECRET"]
WORKSPACE_ID = os.environ["PBI_WORKSPACE_ID"]
REPORT_ID = os.environ["PBI_REPORT_ID"]

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
PBI_SCOPE = ["https://analysis.windows.net/powerbi/api/.default"]
BASE = "https://api.powerbi.com/v1.0/myorg"


def get_token() -> str:
    app = msal.ConfidentialClientApplication(
        CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET
    )
    result = app.acquire_token_for_client(scopes=PBI_SCOPE)
    if "access_token" not in result:
        raise RuntimeError(f"MSAL failed: {result}")
    return result["access_token"]


def call(label: str, method: str, url: str, token: str, body: dict | None = None) -> None:
    headers = {"Authorization": f"Bearer {token}"}
    if body is not None:
        headers["Content-Type"] = "application/json"

    print(f"\n{'=' * 70}")
    print(f"{label}")
    print(f"  {method} {url}")

    r = httpx.request(method, url, headers=headers, json=body, timeout=30)

    print(f"  HTTP {r.status_code}")
    body_text = r.text
    if len(body_text) > 800:
        body_text = body_text[:800] + "...<truncated>"
    print(f"  body: {body_text}")

    if r.status_code < 300:
        try:
            data = r.json()
            # Pretty-print a hint of what we got back
            if "value" in data and isinstance(data["value"], list):
                print(f"  → {len(data['value'])} items returned")
                for item in data["value"][:5]:
                    name = item.get("name") or item.get("displayName") or item.get("id")
                    print(f"     - {name}")
        except (ValueError, KeyError):
            pass


def main() -> int:
    print("Acquiring service principal token...")
    token = get_token()
    print(f"  OK ({len(token)} chars)\n")

    # Step 1 — workspace visibility
    call(
        "STEP 1 — List workspaces (SP membership check)",
        "GET",
        f"{BASE}/groups",
        token,
    )

    # Step 2 — datasets in OUR workspace
    call(
        "STEP 2 — List datasets in workspace (dataset enumeration)",
        "GET",
        f"{BASE}/groups/{WORKSPACE_ID}/datasets",
        token,
    )

    # We need the dataset_id of the report's underlying semantic model
    print(f"\n{'=' * 70}")
    print("STEP 2.5 — Resolve dataset_id from report")
    r = httpx.get(
        f"{BASE}/groups/{WORKSPACE_ID}/reports/{REPORT_ID}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=20,
    )
    if r.status_code >= 300:
        print(f"  Could not resolve dataset_id (HTTP {r.status_code}): {r.text[:400]}")
        return 1
    dataset_id = r.json()["datasetId"]
    print(f"  datasetId = {dataset_id}")

    # Step 3 — read THIS specific dataset's metadata
    call(
        "STEP 3 — Read dataset metadata (single-dataset read permission)",
        "GET",
        f"{BASE}/groups/{WORKSPACE_ID}/datasets/{dataset_id}",
        token,
    )

    # Step 4 — actually execute a trivial DAX query
    call(
        "STEP 4 — Execute trivial DAX (the real test — Build permission)",
        "POST",
        f"{BASE}/groups/{WORKSPACE_ID}/datasets/{dataset_id}/executeQueries",
        token,
        body={"queries": [{"query": "EVALUATE ROW(\"test\", 1)"}]},
    )

    print(f"\n{'=' * 70}")
    print("Summary:")
    print("  - Step 1 200 → SP can see any workspace")
    print("  - Step 2 200 → SP is a Member of the target workspace")
    print("  - Step 3 200 → SP can read the dataset's metadata (Read perm OK)")
    print("  - Step 4 200 → SP has Build permission AND ExecuteQueries enabled")
    print("\nThe FIRST step that returns 401/403 is the layer that's blocked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
