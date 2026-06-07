"""Diagnose why /residence shows 'Live data temporarily unavailable'.

Checks whether the residential Gold tables are queryable through the Fabric SQL
Analytics Endpoint (the read path the backend uses). A notebook can create a Delta
table in the lakehouse while the SQL endpoint hasn't synced its metadata yet — then
SELECT raises "Invalid object name", which the API turns into a 503.

Run (from web-app/backend, venv + .env active):
    python scripts/check_residential_sql.py
"""
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND_DIR / ".env", override=True)

from app.integrations import fabric_sql  # noqa: E402

TABLES = [
    "gold_residential_unit_kpi",
    "gold_residential_common_split",
    "gold_residential_uvi_monthly",
]


def main() -> int:
    print(f"FABRIC_SQL_DATABASE (lakehouse) = {os.getenv('FABRIC_SQL_DATABASE')}")
    print(f"FABRIC_SQL_SERVER              = {os.getenv('FABRIC_SQL_SERVER')}\n")

    # 1. What residential tables does the SQL endpoint actually see?
    try:
        rows = fabric_sql.execute_query(
            "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_NAME LIKE 'gold_residential%' ORDER BY TABLE_NAME"
        )
        visible = [f"{r['TABLE_SCHEMA']}.{r['TABLE_NAME']}" for r in rows]
        print("Visible residential tables in SQL endpoint:", visible or "NONE")
    except Exception as e:  # noqa: BLE001
        print(f"  INFORMATION_SCHEMA query failed: {type(e).__name__}: {str(e)[:200]}")
    print()

    # 2. Try the exact reads the API does.
    ok = True
    for t in TABLES:
        try:
            rows = fabric_sql.execute_query(f"SELECT COUNT(*) AS n FROM [dbo].[{t}]")
            print(f"  OK   [dbo].[{t}]: {rows[0]['n']} rows")
        except Exception as e:  # noqa: BLE001
            ok = False
            print(f"  ERR  [dbo].[{t}]: {type(e).__name__}: {str(e)[:200]}")

    print()
    if ok:
        print("All residential gold tables are queryable → /residence should show data.")
        print("If the page still shows the notice, check that the seeded unit_id "
              "(e.g. B011-U0101) actually has rows in gold_residential_unit_kpi.")
    else:
        print("At least one table is NOT visible to the SQL endpoint. Fix on Fabric side:")
        print("  • Open the Lakehouse SQL Analytics Endpoint → confirm the 3 tables list;")
        print("    if missing, refresh the endpoint metadata (or wait for sync).")
        print("  • Confirm the notebook wrote to the SAME lakehouse as FABRIC_SQL_DATABASE.")
        print("  • The API read path uses the [dbo] schema (as other gold tables do).")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
