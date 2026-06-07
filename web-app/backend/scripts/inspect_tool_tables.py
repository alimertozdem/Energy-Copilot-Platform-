"""Dump column lists for the 3 gold tables that hit schema mismatches in Day 16
smoke testing. Run this and paste the output to Claude — he'll patch tools.py
with the real column names.

Run:
    python scripts/inspect_tool_tables.py
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
# Make backend/ importable so `from app...` works regardless of CWD.
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env", override=True)

from app.integrations import fabric_sql  # noqa: E402

TABLES = [
    "gold_anomaly_log",
    "gold_recommendations",
    "gold_battery_simulation",
]


def main() -> None:
    for table in TABLES:
        print(f"\n=== dbo.{table} ===")
        try:
            rows = fabric_sql.execute_query(
                "SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE "
                "FROM INFORMATION_SCHEMA.COLUMNS "
                "WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = ? "
                "ORDER BY ORDINAL_POSITION",
                (table,),
            )
        except Exception as exc:  # noqa: BLE001
            print(f"  ERROR: {type(exc).__name__}: {exc}")
            continue

        if not rows:
            print(f"  (table not found in dbo schema — check the name)")
            continue

        for r in rows:
            col = r["COLUMN_NAME"]
            typ = r["DATA_TYPE"]
            nul = "NULL" if r["IS_NULLABLE"] == "YES" else "NOT NULL"
            print(f"  {col:40s} {typ:20s} {nul}")

        # Bonus: sample one row to see the shape of data
        try:
            sample = fabric_sql.execute_query(
                f"SELECT TOP 1 * FROM [dbo].[{table}]"
            )
            if sample:
                print(f"\n  sample row keys: {list(sample[0].keys())}")
        except Exception:
            pass

    print("\nDone. Copy this output to Claude.")


if __name__ == "__main__":
    main()
