# =============================================================================
# 09_ghg — CELL 3 / 3  (BREAKDOWN LONG — scope×category boyutu, drill için)
# cell1 + cell2'den SONRA çalıştır (ayrı bir hücreye yapıştır).
# gold_ghg_scope'u "uzun format"a çevirir → category GERÇEK bir kolon olur
# (DirectLake'te calc-column gerekmez). Tek ölçü + drill + temiz görsel sağlar.
# =============================================================================
from pyspark.sql.functions import col, lit
from functools import reduce
import re


def _prefix():
    for t in ["gold_ghg_scope", "gold_kpi_daily", "silver_building_master"]:
        try:
            sp = spark.table(t).inputFiles()[0]
            m = re.match(r"(abfss://[^/]+@[^/]+/[^/]+)", sp)
            if m:
                base = m.group(1)
                return f"{base}/Tables/dbo" if "/Tables/dbo/" in sp else f"{base}/Tables"
        except Exception:
            continue
    raise Exception("gold_ghg_scope bulunamadı — önce cell1 + cell2 çalıştır.")


P = _prefix()
df = spark.read.format("delta").load(f"{P}/gold_ghg_scope")

# (scope, category, kolon, data_grade) — additive bileşenler (Scope 2 = location headline)
pairs = [
    ("Scope 1", "Gas",                    "scope1_gas_tco2",            "core"),
    ("Scope 1", "Diesel",                 "scope1_diesel_tco2",         "core"),
    ("Scope 1", "Refrigerant",            "scope1_refrigerant_tco2",    "estimated"),
    ("Scope 2", "Electricity (location)", "scope2_location_tco2",       "core"),
    ("Scope 3", "Cat 1 Embodied",         "scope3_cat1_embodied_tco2",  "estimated"),
    ("Scope 3", "Cat 3 Fuel & Energy",    "scope3_cat3_fuelenergy_tco2","estimated"),
    ("Scope 3", "Cat 5 Waste",            "scope3_cat5_waste_tco2",     "estimated"),
    ("Scope 3", "Cat 6 Travel",           "scope3_cat6_travel_tco2",    "estimated"),
    ("Scope 3", "Cat 7 Commute",          "scope3_cat7_commute_tco2",   "estimated"),
    ("Scope 3", "Cat 13 Leased",          "scope3_cat13_leased_tco2",   "estimated"),
]
parts = [
    df.select(
        "building_id", "year_month", "reporting_year", "reporting_month",
        lit(s).alias("scope"), lit(c).alias("category"),
        lit(g).alias("data_grade"), col(cn).alias("value_tco2"),
    )
    for s, c, cn, g in pairs
]
df_long = reduce(lambda a, b: a.unionByName(b), parts)

_tbl = "gold_ghg_breakdown_long"
df_long.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(_tbl)
try:
    spark.catalog.refreshTable(_tbl)
except Exception:
    pass

print(f"✅ {_tbl}: {df_long.count()} satır (scope × category long format).")
print("   Modele ekle → tek ölçü [Emissions tCO2e]=SUM(value_tco2) → drill/slicer ile temiz görsel.")
df_long.groupBy("scope", "category").count().orderBy("scope", "category").show(20, truncate=False)
