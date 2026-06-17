# =============================================================================
# 90_optimize_gold.py  —  OPTIMIZE + V-ORDER all gold_* Delta tables
# -----------------------------------------------------------------------------
# WHY: gold notebooks write incrementally (MERGE) -> many small Parquet files ->
# slow DirectLake scans + higher DirectQuery-fallback risk on F4. OPTIMIZE compacts
# files and V-ORDER lays them out for fast DirectLake reads. This is the #1
# DirectLake speed lever.
#
# RUN: as the LAST stage of the batch pipeline (after all gold writes). Idempotent —
# safe to run anytime. Also sets the session flag so NEW writes stay V-ordered.
# =============================================================================
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

# make future writes V-ordered automatically (defensive; many Fabric runtimes default on)
try:
    spark.conf.set("spark.sql.parquet.vorder.enabled", "true")
except Exception as e:
    print("note: could not set vorder flag:", str(e)[:120])

# discover gold_* tables in the current lakehouse (schema-tolerant)
rows = spark.sql("SHOW TABLES").collect()
tables = sorted({r["tableName"] for r in rows if r["tableName"].lower().startswith("gold_")})
print(f"Found {len(tables)} gold_* tables to optimize.\n")

ok, fail = [], []
for t in tables:
    try:
        spark.sql(f"OPTIMIZE {t} VORDER")
        ok.append(t)
        print(f"  OK    {t}")
    except Exception as e:
        fail.append((t, str(e)[:140]))
        print(f"  FAIL  {t}: {str(e)[:140]}")

print(f"\nDone. optimized={len(ok)}  failed={len(fail)}")
for t, e in fail:
    print(f"   {t} -> {e}")
