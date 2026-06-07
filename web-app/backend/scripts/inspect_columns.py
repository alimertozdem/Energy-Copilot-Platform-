"""
List columns + types + nullability for the tables /portfolio will read.

Use this output to write the exact SQL queries and Pydantic schemas without
guessing column names or assuming the wrong type. Runs against the live
Fabric Lakehouse SQL endpoint via the new fabric_sql client.

Run:
    python -m scripts.inspect_columns
"""

import sys
from pathlib import Path

# Ensure 'app' package is importable when running as a script
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env", override=True)

from app.integrations import fabric_sql

TABLES = [
    "silver_building_master",
    "gold_kpi_daily",
    "gold_ghg_scope",
    "gold_anomaly_log",
    "gold_recommendations",
    "gold_iot_daily_summary",
]


def describe_table(table_name: str) -> None:
    print(f"\n{'=' * 78}")
    print(f"TABLE: dbo.{table_name}")
    print('=' * 78)
    rows = fabric_sql.execute_query(
        """
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION
        """,
        (table_name,),
    )
    if not rows:
        print(f"  (no columns — table not found in dbo schema)")
        return

    print(f"  {'COLUMN':<35} {'TYPE':<15} {'NULL?':<6} {'LEN'}")
    print(f"  {'-' * 35} {'-' * 15} {'-' * 6} {'-' * 6}")
    for r in rows:
        col = r["COLUMN_NAME"]
        dtype = r["DATA_TYPE"]
        nullable = r["IS_NULLABLE"]
        max_len = r["CHARACTER_MAXIMUM_LENGTH"]
        max_len_str = str(max_len) if max_len is not None else ""
        print(f"  {col:<35} {dtype:<15} {nullable:<6} {max_len_str}")

    # Bonus: a peek at the first row to see real values
    print(f"\n  -- first row sample --")
    sample = fabric_sql.execute_query(
        f"SELECT TOP 1 * FROM [dbo].[{table_name}]"
    )
    if sample:
        for k, v in sample[0].items():
            v_short = str(v)
            if len(v_short) > 60:
                v_short = v_short[:57] + "..."
            print(f"  {k:<35} = {v_short}")
    else:
        print("  (table is empty)")

    # Row count
    count = fabric_sql.execute_scalar(
        f"SELECT COUNT(*) FROM [dbo].[{table_name}]"
    )
    print(f"\n  Row count: {count:,}" if count is not None else "  Row count: ?")


def main() -> int:
    for table in TABLES:
        try:
            describe_table(table)
        except Exception as e:
            print(f"\n[ERROR] {table}: {e}")
    print(f"\n{'=' * 78}")
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
