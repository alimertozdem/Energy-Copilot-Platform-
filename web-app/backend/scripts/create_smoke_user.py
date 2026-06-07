"""One-shot script: register a dedicated smoke-test user.

Run once before smoke_copilot.py. Idempotent — if the user already exists
the script logs that and exits cleanly so it can be re-run safely.

Default credentials:
    email    : smoke@energylens.eu
    password : SmokeTest1234

After this script runs, smoke_copilot.py can be invoked with:
    python scripts/smoke_copilot.py --email smoke@energylens.eu --pw SmokeTest1234
"""
import argparse
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env", override=True)

DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_EMAIL = "smoke@energylens.eu"
DEFAULT_PASSWORD = "SmokeTest1234"
DEFAULT_NAME = "Smoke Test"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--email", default=DEFAULT_EMAIL)
    parser.add_argument("--pw", default=DEFAULT_PASSWORD)
    parser.add_argument("--name", default=DEFAULT_NAME)
    args = parser.parse_args()

    internal_key = os.environ.get("INTERNAL_API_KEY")
    if not internal_key:
        print("FAIL: INTERNAL_API_KEY not set in .env")
        sys.exit(1)

    r = httpx.post(
        f"{args.base_url}/auth/register",
        json={
            "email": args.email,
            "password": args.pw,
            "display_name": args.name,
        },
        headers={"X-Internal-Api-Key": internal_key},
        timeout=30.0,
    )

    if r.status_code == 201:
        data = r.json()
        print(f"OK   Registered new user")
        print(f"     email     : {args.email}")
        print(f"     password  : {args.pw}")
        print(f"     user_id   : {data.get('user_id')}")
        print(f"     org_id    : {data.get('organization_id')}")
        print()
        print(f"Now run:")
        print(f"  python scripts/smoke_copilot.py --email {args.email} --pw {args.pw}")
        return

    if r.status_code == 409:
        print(f"OK   User '{args.email}' already exists (409 conflict).")
        print(f"     If you still get 401 on login, the password may be different.")
        print(f"     Try a different --email to create a fresh smoke user.")
        return

    print(f"FAIL Register returned {r.status_code}: {r.text}")
    sys.exit(1)


if __name__ == "__main__":
    main()
