# ============================================================
# Energy Copilot Platform — Page 9 MISSING table loader (focused)
# Notebook : 16b_load_only_missing_tables.py
# Date     : 2026-05-21
# ============================================================
#
# PURPOSE
# -------
# Only loads the 2 NEW tables for Page 9 v56 that aren't in the
# Lakehouse yet:
#   - gold_country_regulations  (12 rows)
#   - gold_strategy_fitness     (49 rows)
#
# The 3 battery tables (dispatch, simulation, technologies)
# are already in the Lakehouse from earlier notebooks — we
# skip them here to avoid accidentally overwriting them.
#
# FLEXIBLE PATH RESOLUTION
# ------------------------
# Tries multiple common upload locations until one matches:
#   1. Files/uploads/<csv>
#   2. Files/<csv>
#   3. Files/sample-data/<csv>
#
# PRE-FLIGHT
# ----------
# Upload these 2 CSVs to Lakehouse Files area (any subfolder above):
#   - gold_country_regulations.csv
#   - gold_strategy_fitness.csv
# ============================================================

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.builder.getOrCreate()

print("=" * 60)
print("Notebook 16b — Page 9 missing tables loader")
print("=" * 60)


# Schema-enabled lakehouse prefix
def _resolve_tables_prefix() -> str:
    try:
        schemas = [r["namespace"] for r in spark.sql("SHOW SCHEMAS").collect()]
        return "dbo." if "dbo" in schemas else ""
    except Exception:
        return ""

TBL = _resolve_tables_prefix()
print(f"Table prefix: '{TBL}'")


# Candidate paths to try for each file
CANDIDATE_DIRS = ["Files/uploads", "Files", "Files/sample-data"]

# The 2 tables we need to load
TARGETS = [
    ("gold_country_regulations.csv", "gold_country_regulations"),
    ("gold_strategy_fitness.csv",    "gold_strategy_fitness"),
]


# Helper: try to read CSV from any candidate path
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
            df.count()      # force evaluation
            print(f"  Found at: {path}")
            return df
        except Exception as e:
            last_err = e
            continue
    raise FileNotFoundError(
        f"{csv_name} not found in any of: {CANDIDATE_DIRS}. Last error: {last_err}"
    )


# Helper: cast known boolean-looking columns to actual booleans
BOOLEAN_COLUMNS = {
    "is_eu_member", "lfp_allowed", "nmc_allowed_new_2025", "nca_allowed",
    "sodium_ion_approved", "solid_state_pilot", "v2g_grid_code_ready",
    "frequency_market_eligible", "capacity_market_eligible",
    "sub_metering_required", "demand_charge_required", "thermal_management_required",
    "is_primary", "is_secondary"
}

def normalize_booleans(df):
    for c in df.columns:
        if c in BOOLEAN_COLUMNS:
            df = df.withColumn(c,
                F.when(F.lower(F.col(c).cast("string")).isin("true", "1"), True)
                 .when(F.lower(F.col(c).cast("string")).isin("false", "0"), False)
                 .otherwise(None).cast("boolean"))
    return df


# Main loop
results = []
for csv_name, tbl_name in TARGETS:
    target = f"{TBL}{tbl_name}"
    print(f"\n[{tbl_name}]")
    print(f"  Target: {target}")
    try:
        df = try_read_csv(csv_name)
        n_rows = df.count()
        n_cols = len(df.columns)
        print(f"  Read   : {n_rows:,} rows × {n_cols} cols")

        df = normalize_booleans(df)
        bool_cols = [c for c in df.columns if c in BOOLEAN_COLUMNS]
        print(f"  Boolean cast applied to: {bool_cols}")

        (
            df.write
            .format("delta")
            .mode("overwrite")
            .option("overwriteSchema", "true")
            .saveAsTable(target)
        )

        print(f"  Write  : OK ({n_rows:,} rows -> {target})")
        results.append((tbl_name, "OK", n_rows, n_cols))

    except Exception as e:
        print(f"  ERROR  : {str(e)[:300]}")
        results.append((tbl_name, "FAIL", 0, 0))


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
    print("  1. Fabric → workspace → EnergyCopilotModel → add these 2 tables to model")
    print("  2. TE2 → Ctrl+R → run probe_model_tables_v2.cs (verify [OK] PRESENT)")
    print("  3. TE2 → run page9_v56c_smart_boolean_fix.cs")
else:
    print("\nUpload missing CSVs to Lakehouse Files/uploads/ and re-run.")


# Sanity check
print("\nSanity check:")
try:
    for tbl_name in ["gold_country_regulations", "gold_strategy_fitness"]:
        full = f"{TBL}{tbl_name}"
        n = spark.table(full).count()
        print(f"  {full:<36}  {n} rows")
except Exception as e:
    print(f"  Sanity check error: {str(e)[:200]}")

print("\nNotebook 16b complete.")
