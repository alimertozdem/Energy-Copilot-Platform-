# =============================================================================
# 09_ghg_scope_engine — FABRIC CELL 1 / 2  (DATA PREP)
# Bunu Fabric'te BİR hücreye yapıştır → çalıştır. Sonra CELL 2'yi sonraki hücreye.
# (Tek hücre ~33KB'da kesildiği için 2 parçaya bölündü. Hücreler state paylaşır.)
# Full Scope 1/2/3: refrigerant + market(contract→residual→location) + Cat 1/3/5/6/7/13.
# ÇALIŞMA SIRASI: 03_ref_factors → 04_scope3_demo_activity_generator → BU (cell1+cell2)
# =============================================================================
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, lit, when, coalesce, broadcast,
    date_trunc, year, month,
    sum as spark_sum, round as spark_round, current_timestamp,
)
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, DateType
from delta.tables import DeltaTable
import re

spark.conf.set("spark.sql.shuffle.partitions", "8")
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", str(10 * 1024 * 1024))
spark.conf.set("spark.sql.adaptive.enabled", "true")
print("✅ CELL 1 — Spark konfig tamam")


# --- Lakehouse Tables/ prefix (schema-enabled & flat uyumlu) ---
def _resolve_tables_prefix():
    for t in ["gold_kpi_daily", "silver_building_master", "gold_recommendations"]:
        try:
            sp = spark.table(t).inputFiles()[0]
            m = re.match(r"(abfss://[^/]+@[^/]+/[^/]+)", sp)
            if m:
                base = m.group(1)
                return f"{base}/Tables/dbo" if "/Tables/dbo/" in sp else f"{base}/Tables"
        except Exception:
            continue
    raise Exception("Referans tablo bulunamadı (gold_kpi_daily / silver_building_master). Ana pipeline koştu mu?")


TABLES_PREFIX = _resolve_tables_prefix()
GOLD_KPI_DAILY = f"{TABLES_PREFIX}/gold_kpi_daily"
SILVER_BUILDING = f"{TABLES_PREFIX}/silver_building_master"
OUTPUT_TABLE = f"{TABLES_PREFIX}/gold_ghg_scope"
print(f"✅ Tables prefix: {TABLES_PREFIX[:80]}...")

GAS_BOILER_EFFICIENCY = 0.85   # kazan verimi (model parametresi; faktörler ref katmanından)


# =============================================================================
# BÖLÜM 3 — KAYNAK TABLOLAR + bina master (proxy katmanı)
# =============================================================================
df_kpi = spark.read.format("delta").load(GOLD_KPI_DAILY)
df_building = spark.read.format("delta").load(SILVER_BUILDING)
_avail = set(df_building.columns)
print(f"✅ kpi {df_kpi.count():,} satır, building {df_building.count()} satır")

if "has_gas_heating" in _avail:
    _gas_expr = col("has_gas_heating").cast("boolean")
else:
    _gas_expr = (coalesce(col("has_hvac_traditional"), lit(False)).cast("boolean")
                 & ~coalesce(col("has_heat_pump"), lit(False)).cast("boolean"))
_diesel_expr = col("has_diesel_generator").cast("boolean") if "has_diesel_generator" in _avail else lit(False)

df_building_slim = df_building.select(
    "building_id",
    col("country_code").alias("country_code"),
    col("conditioned_area_m2").alias("area_m2"),
    _gas_expr.alias("has_gas"),
    _diesel_expr.alias("has_diesel"),
    (col("green_supplier_ef_kg_kwh") if "green_supplier_ef_kg_kwh" in _avail
     else lit(None).cast("double")).alias("supplier_ef"),
    (col("building_type") if "building_type" in _avail else lit("DEFAULT")).alias("building_type"),
    (col("leased_area_m2") if "leased_area_m2" in _avail else lit(None).cast("double")).alias("leased_area_m2"),
).distinct()
print(f"✅ building_slim: {df_building_slim.count()} bina")


# =============================================================================
# BÖLÜM 3b — REFERANS KATMANI + aktivite tabloları (hepsi opsiyonel/graceful)
# =============================================================================
df_ref_grid = (spark.read.format("delta").load(f"{TABLES_PREFIX}/ref_grid_emission_factors")
               .select(col("country_code").alias("ref_country"), col("year").alias("ref_year"),
                       col("emission_factor_kg_kwh").alias("ref_ef")))
_eu = df_ref_grid.filter(col("ref_country") == "EU").orderBy(col("ref_year").desc()).limit(1).collect()
EU_EF_FALLBACK = float(_eu[0]["ref_ef"]) if _eu else 0.23

_fuel = {r["factor_key"]: r["value"]
         for r in spark.read.format("delta").load(f"{TABLES_PREFIX}/ref_fuel_factors").collect()}
GAS_EF_KG_PER_KWH = _fuel.get("natural_gas_kg_per_kwh", 0.201)
DIESEL_EF_KG_PER_LITRE = _fuel.get("diesel_kg_per_litre", 2.68)
# Scope 3 Cat 3 (yakıt&enerji upstream) — WTT + T&D (DEFRA)
ELEC_WTT_KG_KWH = _fuel.get("elec_wtt_kg_per_kwh", 0.0388)
ELEC_TD_KG_KWH = _fuel.get("elec_td_kg_per_kwh", 0.0188)
GAS_WTT_KG_KWH = _fuel.get("gas_wtt_kg_per_kwh", 0.0246)
# Scope 3 Cat 5/6/7 — per-employee faktörler
try:
    _act = {r["factor_key"]: r["value"]
            for r in spark.read.format("delta").load(f"{TABLES_PREFIX}/ref_scope3_activity_factors").collect()}
except Exception:
    _act = {}
COMMUTE_KG_EMP_YR = _act.get("commute_kgco2e_per_emp_yr", 1000.0)
BIZTRAVEL_KG_EMP_YR = _act.get("biztravel_kgco2e_per_emp_yr", 400.0)
WASTE_KG_EMP_YR = _act.get("waste_kgco2e_per_emp_yr", 150.0)
print(f"✅ ref katmanı: grid {df_ref_grid.count()}, gaz {GAS_EF_KG_PER_KWH}, EU fb {EU_EF_FALLBACK}")

# WP2 residual mix (market-based fallback)
try:
    df_ref_residual = (spark.read.format("delta").load(f"{TABLES_PREFIX}/ref_residual_mix")
                       .select(col("country_code").alias("res_country"), col("year").alias("res_year"),
                               col("residual_mix_kg_kwh").alias("res_ef")))
    _has_residual = True
    print(f"✅ ref_residual_mix: {df_ref_residual.count()} satır")
except Exception as e:
    df_ref_residual, _has_residual = None, False
    print(f"ℹ️  ref_residual_mix yok ({type(e).__name__}) → market location'a düşer")

# WP3 refrigerant log → aylık tCO2
try:
    _rl = spark.read.format("delta").load(f"{TABLES_PREFIX}/silver_refrigerant_log")
    _gwp = (spark.read.format("delta").load(f"{TABLES_PREFIX}/ref_refrigerant_gwp")
            .select(col("refrigerant").alias("gwp_refrigerant"), col("gwp_100")))
    df_refrig_monthly = (_rl.withColumn("year_month", date_trunc("month", col("event_date")).cast(DateType()))
                         .join(broadcast(_gwp), col("refrigerant") == col("gwp_refrigerant"), "left")
                         .withColumn("refrig_tco2", spark_round(col("topup_kg") * coalesce(col("gwp_100"), lit(0.0)) / 1000, 4))
                         .groupBy("building_id", "year_month").agg(spark_sum("refrig_tco2").alias("scope1_refrigerant_tco2")))
    _has_refrig = True
    print(f"✅ silver_refrigerant_log: {df_refrig_monthly.count()} bina-ay")
except Exception as e:
    df_refrig_monthly, _has_refrig = None, False
    print(f"ℹ️  silver_refrigerant_log yok ({type(e).__name__}) → refrigerant=0")

# WP4 embodied benchmark (Cat 1)
try:
    df_embodied = (spark.read.format("delta").load(f"{TABLES_PREFIX}/ref_embodied_carbon")
                   .select(col("building_type").alias("emb_type"), col("embodied_kgco2e_m2"), col("amortization_years")))
    _has_embodied = True
    print(f"✅ ref_embodied_carbon: {df_embodied.count()} tip")
except Exception as e:
    df_embodied, _has_embodied = None, False
    print(f"ℹ️  ref_embodied_carbon yok ({type(e).__name__}) → Cat1 default 700")

# WP-max: supplier contracts (market), tenant energy (Cat 13), headcount (Cat 5/6/7)
try:
    df_supplier_c = (spark.read.format("delta").load(f"{TABLES_PREFIX}/silver_supplier_contracts")
                     .select(col("building_id").alias("sc_building"), col("supplier_ef_kg_kwh").alias("contract_supplier_ef")))
    _has_supplier_c = True
    print(f"✅ silver_supplier_contracts: {df_supplier_c.count()} bina")
except Exception as e:
    df_supplier_c, _has_supplier_c = None, False
    print(f"ℹ️  silver_supplier_contracts yok ({type(e).__name__})")

try:
    df_tenant = (spark.read.format("delta").load(f"{TABLES_PREFIX}/silver_tenant_energy")
                 .select("building_id", "year_month", "tenant_kwh"))
    _has_tenant = True
    print(f"✅ silver_tenant_energy: {df_tenant.count()} bina-ay")
except Exception as e:
    df_tenant, _has_tenant = None, False
    print(f"ℹ️  silver_tenant_energy yok ({type(e).__name__}) → Cat13=0")

try:
    df_org = (spark.read.format("delta").load(f"{TABLES_PREFIX}/silver_org_activity")
              .select(col("building_id").alias("org_building"), col("headcount")))
    _has_org = True
    print(f"✅ silver_org_activity: {df_org.count()} bina")
except Exception as e:
    df_org, _has_org = None, False
    print(f"ℹ️  silver_org_activity yok ({type(e).__name__}) → Cat5/6/7=0")


# =============================================================================
# BÖLÜM 4 — AYLIK AGREGASYON
# =============================================================================
df_monthly = (df_kpi.withColumn("year_month", date_trunc("month", col("date")).cast(DateType()))
              .groupBy("building_id", "year_month")
              .agg(spark_sum("total_consumption_kwh").alias("monthly_consumption_kwh"),
                   spark_sum("net_grid_consumption_kwh").alias("monthly_grid_kwh"))
              .withColumn("reporting_year", year(col("year_month")))
              .withColumn("reporting_month", month(col("year_month"))))
print(f"✅ Aylık agregasyon: {df_monthly.count()} satır")


# =============================================================================
# BÖLÜM 5 — JOIN'LER (bina + grid + residual + refrigerant + embodied + supplier + tenant + org)
# =============================================================================
df_joined = df_monthly.join(broadcast(df_building_slim), on="building_id", how="left")

df_with_ef = (df_joined
    .join(broadcast(df_ref_grid),
          (col("country_code") == col("ref_country")) & (col("reporting_year") == col("ref_year")), "left")
    .withColumn("emission_factor_grid", coalesce(col("ref_ef"), lit(EU_EF_FALLBACK)))
    .withColumn("emission_factor_source",
                when(col("ref_ef").isNotNull(), lit("ref_grid_emission_factors")).otherwise(lit("EU_fallback")))
    .drop("ref_country", "ref_year", "ref_ef"))

if _has_residual:
    df_with_ef = (df_with_ef.join(broadcast(df_ref_residual),
        (col("country_code") == col("res_country")) & (col("reporting_year") == col("res_year")), "left")
        .drop("res_country", "res_year"))
else:
    df_with_ef = df_with_ef.withColumn("res_ef", lit(None).cast("double"))

if _has_refrig:
    df_with_ef = df_with_ef.join(df_refrig_monthly, on=["building_id", "year_month"], how="left")
else:
    df_with_ef = df_with_ef.withColumn("scope1_refrigerant_tco2", lit(None).cast("double"))
df_with_ef = df_with_ef.withColumn("scope1_refrigerant_tco2", coalesce(col("scope1_refrigerant_tco2"), lit(0.0)))

if _has_embodied:
    df_with_ef = df_with_ef.join(broadcast(df_embodied), col("building_type") == col("emb_type"), "left").drop("emb_type")
else:
    df_with_ef = (df_with_ef.withColumn("embodied_kgco2e_m2", lit(None).cast("double"))
                  .withColumn("amortization_years", lit(None).cast("int")))

if _has_supplier_c:
    df_with_ef = df_with_ef.join(broadcast(df_supplier_c), col("building_id") == col("sc_building"), "left").drop("sc_building")
else:
    df_with_ef = df_with_ef.withColumn("contract_supplier_ef", lit(None).cast("double"))

if _has_tenant:
    df_with_ef = df_with_ef.join(df_tenant, on=["building_id", "year_month"], how="left")
else:
    df_with_ef = df_with_ef.withColumn("tenant_kwh", lit(None).cast("double"))

if _has_org:
    df_with_ef = df_with_ef.join(broadcast(df_org), col("building_id") == col("