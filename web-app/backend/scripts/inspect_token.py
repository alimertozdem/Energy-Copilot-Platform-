"""
Decode the service principal's access token and print its claims.

This is the ground truth for what Azure Entra has actually granted the SP —
if Dataset.Read.All was granted + admin-consented, it MUST appear in the
`roles` claim. If it's missing, the grant didn't take effect.

Run:
    python -m scripts.inspect_token
"""

import base64
import json
import os
from pathlib import Path

import msal
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env", override=True)

TENANT_ID = os.environ["PBI_TENANT_ID"]
CLIENT_ID = os.environ["PBI_CLIENT_ID"]
CLIENT_SECRET = os.environ["PBI_CLIENT_SECRET"]

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
PBI_SCOPE = ["https://analysis.windows.net/powerbi/api/.default"]


def decode_jwt_body(token: str) -> dict:
    """Decode the middle (payload) section of a JWT without verification."""
    _, body, _ = token.split(".")
    # Pad base64 to a multiple of 4
    body += "=" * (-len(body) % 4)
    return json.loads(base64.urlsafe_b64decode(body))


def main() -> int:
    print("Acquiring token with Power BI scope...")
    app = msal.ConfidentialClientApplication(
        CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET
    )
    result = app.acquire_token_for_client(scopes=PBI_SCOPE)
    if "access_token" not in result:
        print(f"MSAL failed: {result}")
        return 1

    token = result["access_token"]
    claims = decode_jwt_body(token)

    print("\n--- Token claims (key fields) ---")
    interesting_keys = [
        "aud", "iss", "appid", "appidacr", "oid", "tid", "sub",
        "idtyp", "roles", "scp", "wids", "groups", "ver",
    ]
    for k in interesting_keys:
        v = claims.get(k, "<not present>")
        print(f"  {k:12s} = {v}")

    print("\n--- Full claims dump ---")
    print(json.dumps(claims, indent=2, default=str))

    print("\n--- Verdict ---")
    roles = claims.get("roles", [])
    if not roles:
        print("  ❌ 'roles' claim is EMPTY.")
        print("     → Power BI Service Application permissions have NOT been")
        print("       granted + admin-consented for this SP.")
        print("     → Re-check Azure Portal → App Registration → API permissions:")
        print("       Power BI Service > Dataset.Read.All (Application) must show")
        print("       'Granted for Default Directory' with a green check.")
    else:
        print(f"  ✅ Roles granted: {roles}")
        if any("Dataset" in r for r in roles):
            print("  ✅ Dataset.* role present — ExecuteQueries should work.")
            print("     If 401 still occurs, the issue is on the dataset side")
            print("     (explicit Build permission missing).")
        else:
            print("  ⚠️  No Dataset.* role found in token.")
    return 0


if __name__ == "__main__":
    main()
