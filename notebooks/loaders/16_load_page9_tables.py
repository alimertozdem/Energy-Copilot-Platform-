# ============================================================
# Energy Copilot Platform — Page 9 Table Loader
# Notebook : 16_load_page9_tables.py
# Layer    : Loader (CSV → Delta — schema-enabled lakehouse compatible)
# Page     : 9 (Battery Strategy)
# Date     : 2026-05-21
# ============================================================
#
# PURPOSE
# -------
# The Page 9 v56 master refactor needs 5 Delta tables that are
# currently MISSING from EnergyCopilotModel (verified via TE2 probe
# 2026-05-21 — only 'gold_battery_hourly_dispatch' and
# 'gold_battery_hourly_profile' present from the battery group).
#
# This idempotent loader writes the 5 CSVs in sample-data/ as
# Delta tables. Three previously existed (re-create them); two are new.
#
# TABLES PRODUCED
# ---------------
#   gold_battery_dispatch        (~6,000 rows — daily dispatch facts)
#   gold_battery_simulation      (~13 rows — NPV/IRR scenarios)
#   gold_battery_technologies    (15 rows — chemistry catalog, +5 new)
#   gold_country_regulations     (12 rows — EU+TR+UK regulations)
#   gold_strategy_fitness        (49 rows — bldg_type × strategy fit)
#
# IDEMPOTENT
# ----------
# Each write uses mode("overwrite") + overwriteSchema=true.
# Safe to re-run after edits to CSVs.
#
# HOW TO RUN IN FABRIC
# --------------------
#   1. Upload the 5 CSVs from local repo sample-data/ to Fabric
#      Lakehouse Files area:
#        Files/uploads/gold_battery_dispatch.csv
#        Files/uploads/gold_battery_simulation.csv
#        Files/uploads/gold_battery_technologies.csv
#        Files/uploads/gold_country_regulations.csv
#        Files/uploads/gold_strategy_fitness.csv
#   2. Open this notebook in Fabric, attach to the same Lakehouse
#      that backs EnergyCopilotModel.
#   3. Run all cells.
#   4. In Fabric workspace: open EnergyCopilotModel default semantic
#      model → "Refresh now" so the new tables appear.
#   5. Open Power BI Desktop (live to model) → External Tools → TE2 →
#      run page9_v56_master_install.cs.
# ============================================================

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType,
    DoubleType, BooleanType, DateType, TimestampType
)
from pyspark.sql import functions as F
from datetime import datetime

spark = SparkSession.builder.getOrCreate()

print("=" * 64)
print("Notebook 16 — Page 9 Table Loader")
print(f"Started: {datetime.now().isoformat()}")
print("=" * 64)

# ─────────────────────────────────────────────────────────────
# Schema-enabled lakehouse: resolve dbo. prefix dynamically
# (per feedback_fabric_schema_lakehouse.md pattern)
# ─────────────────────────────────────────────────────────────

def _resolve_tables_prefix() -> str:
    """Return 'dbo.' if the lakehouse uses schema-enabled mode, else ''."""
    try:
        schemas = [r["namespace"] for r in spark.sql("SHOW SCHEMAS").collect()]
        return "dbo." if "dbo" in schemas else ""
    except Exception:
        return ""

TBL = _resolve_tables_prefix()
print(f"Resolved table prefix: '{TBL}'")

# ─────────────────────────────────────────────────────────────
# Files area — Fabric default mount
# ─────────────────────────────────────────────────────────────
FILES_BASE = "Files/uploads"   # adjust if you uploaded to a sub-folder

CSV_TO_TABLE = [
    ("gold_battery_dispatch.csv",       "gold_battery_dispatch"),
    ("gold_battery_simulation.csv",     "gold_battery_simulation"),
    ("gold_battery_technologies.csv",   "gold_battery_technologies"),
    ("gold_country_regulations.csv",    "gold_country_regulations"),
    ("gold_strategy_fitness.csv",       "gold_strategy_fitness"),
]


# ─────────────────────────────────────────────────────────────
# Cell — Load each CSV → Delta table (idempotent overwrite)
# ─────────────────────────────────────────────────────────────

results = []

for csv_name, tbl_name in CSV_TO_TABLE:
    full_path = f"{FILES_BASE}/{csv_name}"
    target = f"{TBL}{tbl_name}"

    print(f"\n[{tbl_name}]")
    print(f"  Source : {full_path}")
    print(f"  Target : {target}")

    try:
        # Read CSV
        df = (
            spark.read
            .option("header", "true")
            .option("inferSchema", "true")
            .option("multiLine", "true")        # battery_technologies notes have commas in quotes
            .option("escape", '"')
            .csv(full_path)
        )

        row_count = df.count()
        col_count = len(df.columns)
        print(f"  Read   : {row_count:,} rows × {col_count} cols")

        # Normalize boolean columns (CSV reads them as string)
        for c in df.columns:
            sample = df.select(c).limit(20).collect()
            vals = {str(r[0]).lower() for r in sample if r[0] is not None}
            if vals and vals.issubset({"true", "false", "1", "0"}):
                df = df.withColumn(c,
                    F.when(F.lower(F.col(c)).isin("true", "1"), True)
                     .when(F.lower(F.col(c)).isin("false", "0"), False)
                     .otherwise(None).cast("boolean"))

        # Write Delta (overwrite)
        (
            df.write
            .format("delta")
            .mode("overwrite")
            .option("overwriteSchema", "true")
            .saveAsTable(target)
        )

        print(f"  Write  : OK ({row_count:,} rows written to {target})")
        results.append((tbl_name, "OK", row_count, col_count))

    except Exception as e:
        msg = str(e)[:280]
        print(f"  ERROR  : {msg}")
        results.append((tbl_name, "FAIL", 0, 0))

# ─────────────────────────────────────────────────────────────
# Cell — Summary report
# ─────────────────────────────────────────────────────────────

print("\n" + "=" * 64)
print("LOADER SUMMARY")
print("=" * 64)
print(f"{'TABLE':<32} {'STATUS':<8} {'ROWS':>10} {'COLS':>6}")
print("-" * 64)
for name, status, rows, cols in results:
    print(f"{name:<32} {status:<8} {rows:>10,} {cols:>6}")
print("=" * 64)

ok_count = sum(1 for r in results if r[1] == "OK")
fail_count = sum(1 for r in results if r[1] == "FAIL")
print(f"OK: {ok_count}/{len(results)}    FAIL: {fail_count}")

if fail_count > 0:
    print("\nIf a FAIL line shows 'Path does not exist', verify the CSV was uploaded to:")
    print(f"  Lakehouse → Files → {FILES_BASE}/")
    print("If a FAIL line shows column-cast errors, open the CSV in the loader cell and inspect.")
else:
    print("\nAll 5 tables written. Next steps:")
    print("  1. Fabric → Workspace → EnergyCopilotModel → 'Refresh now'")
    print("     (or: Open in Power BI → 'Refresh' to pick up new tables)")
    print("  2. Verify via TE2 probe_model_tables_v2.cs — all 7 should show [OK] PRESENT")
    print("  3. Run page9_v56_master_install.cs")


# ─────────────────────────────────────────────────────────────
# Cell — Quick sanity check (3 sample queries)
# ─────────────────────────────────────────────────────────────

print("\n" + "=" * 64)
print("SANITY CHECK")
print("=" * 64)

try:
    n_dispatch = spark.table(f"{TBL}gold_battery_dispatch").count()
    n_sim      = spark.table(f"{TBL}gold_battery_simulation").count()
    n_tech     = spark.table(f"{TBL}gold_battery_technologies").count()
    n_country  = spark.table(f"{TBL}gold_country_regulations").count()
    n_fitness  = spark.table(f"{TBL}gold_strategy_fitness").count()

    print(f"gold_battery_dispatch       : {n_dispatch:,} rows")
    print(f"gold_battery_simulation     : {n_sim:,} rows")
    print(f"gold_battery_technologies   : {n_tech:,} rows  (expected 15: 10 original + 5 new)")
    print(f"gold_country_regulations    : {n_country:,} rows (expected 12)")
    print(f"gold_strategy_fitness       : {n_fitness:,} rows (expected 49)")

    # Spot-check: are the new chemistries present?
    print("\nNew chemistries check:")
    new_ids = ["CATL_NAXTRA_100", "QUANTUMSCAPE_SS_150", "BYD_HVS_V2G_120",
               "CONNECTED_2L_NMC_250", "SKELETON_SKELGRID_80"]
    df_tech = spark.table(f"{TBL}gold_battery_technologies")
    found = [r["battery_id"] for r in df_tech.filter(F.col("battery_id").isin(new_ids)).collect()]
    for nid in new_ids:
        flag = "✓" if nid in found else "✗"
        print(f"  {flag}  {nid}")

except Exception as e:
    print(f"Sanity check error: {str(e)[:280]}")

print("\nNotebook 16 complete.")
