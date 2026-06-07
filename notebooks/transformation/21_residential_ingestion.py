# =============================================================================
# 21_residential_ingestion.py — Residential P2 (FLAT, top-level, paste-safe)
# Seed (B011 + 24 daire) + bill (building grain) + heatcost (unit grain)
#   -> silver_residential_consumption.
# Tek hücreye yapıştır + çalıştır. Fonksiyon-yok (ne() hariç), main()-yok.
# Ön koşul: 02_silver çalışmış olmalı (silver_building_master). CSV: Files kökünde.
# =============================================================================
from pyspark.sql import Row
from pyspark.sql.types import (StructType, StructField, StringType, DoubleType,
                               BooleanType, TimestampType)
from pyspark.sql.functions import col, lit, lower, trim, to_date, when, current_timestamp
from delta.tables import DeltaTable

BID = "B011"
BILL = "Files/sample_bills_B011.csv"
HEAT = "Files/sample_heatcost_B011.csv"
COLS = ["building_id", "unit_id", "grain", "period_start", "period_end",
        "energy_type", "consumption_kwh", "cost_eur", "source", "ingested_at"]
USCH = StructType([
    StructField("unit_id", StringType()), StructField("building_id", StringType()),
    StructField("floor", StringType()), StructField("area_m2", DoubleType()),
    StructField("unit_type", StringType()), StructField("is_heated", BooleanType()),
    StructField("updated_at", TimestampType())])


def ne(c):
    e = lower(trim(c))
    return (when(e.isin("districtheat", "fernwaerme", "fernwärme"), lit("district_heat"))
            .when(e.isin("warmwasser", "ww", "hot_water"), lit("dhw"))
            .when(e.isin("strom", "power"), lit("electricity"))
            .when(e.isin("heizung", "heat"), lit("heating"))
            .when(e.isin("erdgas", "natural_gas"), lit("gas"))
            .when(e.isin("heizoel", "heizöl", "fuel_oil"), lit("oil")).otherwise(e))


# --- SEED: B011 + 24 daire (insert-if-absent) ---
if spark.catalog.tableExists("silver_building_master"):
    tgt = spark.table("silver_building_master").schema
    nm = [f.name for f in tgt]
    kn = {k: v for k, v in {"building_id": BID, "building_type": "Residential_MF",
          "country_code": "DE", "city": "Berlin", "name": "Musterstraße 12 (MFH)",
          "conditioned_area_m2": 2400.0, "unit_count": 24, "common_area_m2": 180.0}.items() if k in nm}
    d = spark.createDataFrame([tuple(kn.values())], list(kn.keys()))
    for f in tgt:
        if f.name not in kn:
            d = d.withColumn(f.name, lit(None).cast(f.dataType))
    d = d.select([col(f.name).cast(f.dataType).alias(f.name) for f in tgt])
    DeltaTable.forName(spark, "silver_building_master").alias("t").merge(
        d.alias("s"), "t.building_id = s.building_id").whenNotMatchedInsertAll().execute()
    if not spark.catalog.tableExists("silver_unit_master"):
        spark.createDataFrame([], USCH).write.format("delta").mode("overwrite").option(
            "overwriteSchema", "true").saveAsTable("silver_unit_master")
    rows = [Row(unit_id=f"{BID}-U{fl:02d}{u:02d}", building_id=BID, floor=str(fl),
                area_m2=round(58.0 + u * 5.5 + fl * 1.5, 1), unit_type="apartment",
                is_heated=True, updated_at=None) for fl in range(1, 5) for u in range(1, 7)]
    du = spark.createDataFrame(rows, USCH).withColumn("updated_at", current_timestamp())
    DeltaTable.forName(spark, "silver_unit_master").alias("t").merge(
        du.alias("s"), "t.unit_id = s.unit_id").whenNotMatchedInsertAll().execute()
    print(f"🏢 seed: {BID} + {len(rows)} daire OK.")

# --- BILL (building grain) ---
bills = spark.read.option("header", "true").option("inferSchema", "true").csv(BILL)
print("BILL satır:", bills.count())
b = (bills.withColumn("building_id", trim(col("fabric_building_id"))).withColumn("unit_id", lit(None).cast("string"))
     .withColumn("grain", lit("building")).withColumn("period_start", to_date("period_start")).withColumn("period_end", to_date("period_end"))
     .withColumn("energy_type", ne(col("energy_type"))).withColumn("consumption_kwh", col("consumption_kwh").cast("double"))
     .withColumn("cost_eur", col("cost_eur").cast("double")).withColumn("source", lit("utility_bill")).withColumn("ingested_at", current_timestamp()).select(*COLS))

# --- HEATCOST (unit grain) ---
heat = spark.read.option("header", "true").option("inferSchema", "true").csv(HEAT)
print("HEATCOST satır:", heat.count())
h = (heat.withColumn("building_id", trim(col("fabric_building_id"))).withColumn("unit_id", trim(col("fabric_unit_id")))
     .withColumn("grain", lit("unit")).withColumn("period_start", to_date("period_start")).withColumn("period_end", to_date("period_end"))
     .withColumn("energy_type", ne(col("energy_type"))).withColumn("consumption_kwh", col("consumption_kwh").cast("double"))
     .withColumn("cost_eur", col("cost_eur").cast("double")).withColumn("source", lit("heatcost")).withColumn("ingested_at", current_timestamp()).select(*COLS))

out = b.unionByName(h)
out.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("silver_residential_consumption")
print("✅ silver_residential_consumption:", out.count(), "satır")
out.groupBy("grain", "energy_type").count().orderBy("grain", "energy_type").show()
