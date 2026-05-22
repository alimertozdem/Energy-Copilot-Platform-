# ============================================================
# Energy Copilot Platform — Reload battery tables with FULL schema
# Notebook : 16c_reload_battery_tables.py
# Date     : 2026-05-21
# ============================================================
#
# WHY
#   The existing gold_battery_dispatch and gold_battery_simulation
#   Delta tables in the Lakehouse were written by an older version
#   of Notebook 12, BEFORE columns like battery_tech, battery_health_percent,
#   cumulative_cycles, round_trip_efficiency_percent were added.
#
#   The CURRENT CSVs in Files/ already have all these columns, but the
#   model is loaded from the old Delta tables, so DAX measures fail with
#   "column X cannot be found".
#
# WHAT THIS DOES
#   1. Reads the current CSVs from Files/  (3 candidate paths)
#   2. Overwrites the Delta tables with full schema (overwriteSchema=true)
#   3. Adds boolean casting for is_simulated, eu_compliant, is_active_strategy
#
# AFTER RUNNING
#   - Fabric → workspace → EnergyCopilotModel → REFRESH (so it picks up the
#     new schema). You may need to remove + re-add the table if columns
#     don't auto-update.
#   - TE2 → Ctrl+R → run page9_v56c_smart_boolean_fix.cs again
# ============================================================

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.builder.getOrCreate()

print("=" * 60)
print("Notebook 16c — Reload battery tables")
print("=" * 60)


def _resolve_tables_prefix() -> str:
    try:
        schemas = [r["namespace"] for r in spark.sql("SHOW SCHEMAS").collect()]
        return "dbo." if "dbo" in schemas else ""
    except Exception:
        return ""

TBL = _resolve_tables_prefix()
print(f"Table prefix: '{TBL}'")

CANDIDATE_DIRS = ["Files/uploads", "Files", "Files/sample-data"]
TARGETS = [
    ("gold_battery_dispatch.csv",   "gold_battery_dispatch"),
    ("gold_battery_simulation.csv", "gold_battery_simulation"),
]

BOOLEAN_COLUMNS = {
    "is_simulated", "is_active_strategy", "eu_compliant"
}


def try_read_csv(csv_name):
    last_err = None
    for d in CANDIDATE_DIRS:
        path = f"{d}/{csv_name}"
        try:
            df = (
                spark.read
                .option("header", "true")
                .option("inferSchema", "true")
                .option("multiLine", "true")
                .option("escape", '"')
                .csv(path)
            )
            df.count()
            print(f"  Found at: {path}")
            return df
        except Exception as e:
            last_err = e
            continue
    raise FileNotFoundError(
        f"{csv_name} not found in {CANDIDATE_DIRS}. Last error: {last_err}"
    )


def normalize_booleans(df):
    for c in df.columns:
        if c in BOOLEAN_COLUMNS:
            df = df.withColumn(c,
                F.when(F.lower(F.col(c).cast("string")).isin("true", "1"), True)
                 .when(F.lower(F.col(c).cast("string")).isin("false", "0"), False)
                 .otherwise(None).cast("boolean"))
    return df


results = []

# BEFORE: log existing columns for diff visibility
print("\n----- BEFORE: existing tables -----")
for csv_name, tbl_name in TARGETS:
    target = f"{TBL}{tbl_name}"
    try:
        cols = spark.table(target).columns
        print(f"  {tbl_name}: {len(cols)} cols  →  {cols}")
    except Exception as e:
        print(f"  {tbl_name}: NOT FOUND ({str(e)[:80]})")

print("\n----- LOADING -----")
for csv_name, tbl_name in TARGETS:
    target = f"{TBL}{tbl_name}"
    print(f"\n[{tbl_name}]")
    print(f"  Target: {target}")
    try:
        df = try_read_csv(csv_name)
        n_rows = df.count()
        n_cols = len(df.columns)
        print(f"  Read: {n_rows:,} rows × {n_cols} cols")
        print(f"  New columns: {df.columns}")

        df = normalize_booleans(df)
        cast_cols = [c for c in df.columns if c in BOOLEAN_COLUMNS]
        print(f"  Boolean cast applied to: {cast_cols}")

        (
            df.write
            .format("delta")
            .mode("overwrite")
            .option("overwriteSchema", "true")
            .saveAsTable(target)
        )
        print(f"  Write: OK ({n_rows:,} rows → {target}) [schema overwritten]")
        results.append((tbl_name, "OK", n_rows, n_cols))

    except Exception as e:
        print(f"  ERROR: {str(e)[:300]}")
        results.append((tbl_name, "FAIL", 0, 0))


# AFTER: verify new schema
print("\n----- AFTER: new schema -----")
for csv_name, tbl_name in TARGETS:
    target = f"{TBL}{tbl_name}"
    try:
        cols = spark.table(target).columns
        print(f"  {tbl_name}: {len(cols)} cols  →  {cols}")
    except Exception as e:
        print(f"  {tbl_name}: error {str(e)[:80]}")


# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
for name, status, rows, cols in results:
    print(f"  {name:<32} {status:<6}  {rows:>5} rows × {cols} cols")

ok = sum(1 for r in results if r[1] == "OK")
fail = sum(1 for r in results if r[1] == "FAIL")
print(f"\nOK: {ok}/{len(results)}    FAIL: {fail}")

if fail == 0:
    print("\nSUCCESS. Next steps:")
    print("  1. Fabric portal → workspace → EnergyCopilotModel:")
    print("     - Open the semantic model")
    print("     - Refresh (top bar) so it picks up the new column schema")
    print("     - If columns still don't appear: REMOVE these 2 tables from")
    print("       the model and ADD them back (this forces schema re-detect)")
    print("  2. TE2 → Ctrl+R → run page9_v56c_smart_boolean_fix.cs")
    print("  3. Power BI Desktop → Refresh → Page 9 should be error-free")

print("\nNotebook 16c complete.")
