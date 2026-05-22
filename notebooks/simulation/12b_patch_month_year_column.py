# =============================================================================
# NOTEBOOK: 12b — Patch gold_battery_dispatch — Add month_year_en column
# Run in  : Microsoft Fabric — PySpark (Python) Notebook
# Lakehouse: EnergyCopilotLakehouse (must be attached to this notebook)
# Error fix: Uses spark.table() instead of file path — correct for Fabric
# =============================================================================

# ── CELL 1: Verify lakehouse attachment ──────────────────────────────────────
# Before running, make sure EnergyCopilotLakehouse is attached:
#   Left panel → Data items → Add data items → add EnergyCopilotLakehouse
#   Then set it as default lakehouse (right-click → Set as default)

# Quick check — should list your tables including gold_battery_dispatch
spark.sql("SHOW TABLES").show(truncate=False)

# ── CELL 2: Read table via Spark catalog (correct Fabric approach) ────────────
df = spark.table("gold_battery_dispatch")
print(f"Rows loaded: {df.count()}")
print("Columns:", df.columns)

# ── CELL 3: Add month_year_en and month_year_sort columns ────────────────────
from pyspark.sql import functions as F

# Hardcoded English month names — locale-safe, never Turkish
month_abbr = (
    F.when(F.month("date") == 1,  F.lit("Jan"))
     .when(F.month("date") == 2,  F.lit("Feb"))
     .when(F.month("date") == 3,  F.lit("Mar"))
     .when(F.month("date") == 4,  F.lit("Apr"))
     .when(F.month("date") == 5,  F.lit("May"))
     .when(F.month("date") == 6,  F.lit("Jun"))
     .when(F.month("date") == 7,  F.lit("Jul"))
     .when(F.month("date") == 8,  F.lit("Aug"))
     .when(F.month("date") == 9,  F.lit("Sep"))
     .when(F.month("date") == 10, F.lit("Oct"))
     .when(F.month("date") == 11, F.lit("Nov"))
     .otherwise(F.lit("Dec"))
)

df_patched = df \
    .withColumn(
        "month_year_en",
        F.concat(month_abbr, F.lit(" "), F.year("date").cast("string"))
    ) \
    .withColumn(
        "month_year_sort",
        (F.year("date") * 100 + F.month("date")).cast("int")
    )

# Preview result
print("Sample dates after patch:")
df_patched.select("date", "month_year_en", "month_year_sort") \
          .distinct() \
          .orderBy("month_year_sort") \
          .show(15, truncate=False)

# ── CELL 4: Overwrite table back to Lakehouse ─────────────────────────────────
df_patched.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("gold_battery_dispatch")

print("✅ Done — gold_battery_dispatch updated with month_year_en + month_year_sort")

# ── CELL 5: Verify ────────────────────────────────────────────────────────────
df_check = spark.table("gold_battery_dispatch")
print(f"Row count after patch: {df_check.count()}")
month_cols = [c for c in df_check.columns if "month" in c.lower()]
print(f"New columns: {month_cols}")

df_check.select("month_year_en", "month_year_sort") \
        .distinct() \
        .orderBy("month_year_sort") \
        .show(50, truncate=False)

# =============================================================================
# AFTER RUNNING THIS NOTEBOOK:
# 1. Power BI Desktop → Home → Refresh  (or Semantic model → Refresh in Service)
# 2. V1 chart: X-axis → remove [date], add [gold_battery_dispatch].[month_year_en]
# 3. V2 chart: X-axis → remove [date], add [gold_battery_dispatch].[month_year_en]
# 4. Format → X-axis → Type = Categorical
# 5. No DAX measure changes needed — V1/V2 measures aggregate automatically
# =============================================================================
