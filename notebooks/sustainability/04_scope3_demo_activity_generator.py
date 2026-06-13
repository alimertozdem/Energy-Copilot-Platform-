# =============================================================================
# ENERGY COPILOT PLATFORM
# Notebook: 04_scope3_demo_activity_generator.py
# Layer: SILVER — synthetic activity data for FULL Scope 1/2/3 (demo)
# Created: 2026-06-08
# =============================================================================
#
# GÖREV (Purpose):
#   Page 6 (GHG) için tam Scope 1/2/3 demosunu çalıştıracak SİLVER aktivite
#   tablolarını üretir. Platformun geri kalanı gibi SENTETİK ama gerçekçi —
#   her satır data_source="synthetic_demo" taşır. Pilot/müşteri gerçek verisi
#   gelince AYNI ŞEMAYLA bu tablolar değiştirilir → 09_ghg_scope motoru DEĞİŞMEZ.
#
#   ÜRETİLEN TABLOLAR (hepsi swappable, gerçek-veri uyumlu şema):
#     silver_refrigerant_log   — Scope 1 fugitive (F-Gas logbook karşılığı)
#     silver_supplier_contracts— market-based Scope 2 (yeşil sözleşme / GoO)
#     silver_tenant_energy     — Scope 3 Cat 13 (downstream leased / kiracı)
#     silver_org_activity      — Scope 3 Cat 5/6/7 sürücüsü (headcount)
#
# DÜRÜSTLÜK: Bu SENTETİK demo verisidir; gerçek bir binanın açıklaması DEĞİL.
#   Metodoloji ve faktörler gerçek (referans katmanı). disclosure_grade görsel
#   etiketleri "estimated/synthetic" kalır. Gerçekle değişince motor aynı çalışır.
#
# VARSAYIMLAR (gerçekçi, kaynaklı aralıklar — CLAUDE.md kuralı):
#   Refrigerant: şarj ≈ soğutma_kW × 0.4 kg; soğutma_kW ≈ alan/30; yıllık kaçak %8.
#   Yeşil sözleşme: binaların ~%35'i (GoO), supplier_ef ≈ 0.020 kg/kWh.
#   Kiracı: binaların ~%40'ı çok-kiracılı, kiraya verilen pay %50.
#   Headcount: alan / yoğunluk (Office 12, Retail 30, Hotel 50, Logistics 200,
#              Healthcare 25, Lab 40, DataCenter 500, default 20 m²/kişi).
#
# ÇALIŞMA SIRASI: ana pipeline → 03_ref_factors_tariffs_loader → BU → 09_ghg_scope
# =============================================================================

from pyspark.sql import functions as F
from pyspark.sql.functions import col, lit, when
from pyspark.sql.types import DateType
import re

spark.conf.set("spark.sql.shuffle.partitions", "8")
print("✅ Scope 3 demo activity generator başlatıldı")


# -----------------------------------------------------------------------------
# Tables/ prefix dinamik tespiti (schema-enabled & flat lakehouse) — 09 ile aynı pattern
# -----------------------------------------------------------------------------
def _resolve_tables_prefix() -> str:
    for t in ["silver_building_master", "gold_kpi_daily", "gold_ghg_scope"]:
        try:
            sample = spark.table(t).inputFiles()[0]
            m = re.match(r"(abfss://[^/]+@[^/]+/[^/]+)", sample)
            if m:
                base = m.group(1)
                return f"{base}/Tables/dbo" if "/Tables/dbo/" in sample else f"{base}/Tables"
        except Exception:
            continue
    raise Exception("Referans tablo bulunamadı (silver_building_master / gold_kpi_daily). Ana pipeline koştu mu?")


TABLES = _resolve_tables_prefix()
print(f"✅ Tables prefix: {TABLES[:80]}...")

df_build = spark.read.format("delta").load(f"{TABLES}/silver_building_master")
df_kpi = spark.read.format("delta").load(f"{TABLES}/gold_kpi_daily")
_av = set(df_build.columns)

# Graceful kolonlar
_area = col("conditioned_area_m2") if "conditioned_area_m2" in _av else lit(5000.0)
_btype = col("building_type") if "building_type" in _av else lit("DEFAULT")
_hp = col("has_heat_pump").cast("boolean") if "has_heat_pump" in _av else lit(False)
_hvac = col("has_hvac_traditional").cast("boolean") if "has_hvac_traditional" in _av else lit(True)

df_b = df_build.select(
    "building_id",
    _area.alias("area_m2"),
    _btype.alias("building_type"),
    _hp.alias("has_heat_pump"),
    _hvac.alias("has_hvac_traditional"),
).distinct()
print(f"✅ {df_b.count()} bina okundu")


# =============================================================================
# 1 — silver_refrigerant_log  (Scope 1 fugitive)
# =============================================================================
# HVAC'ı olan her bina: yılda bir servis kaydı. topup_kg ≈ alan×0.00107 (şarj×%8 kaçak).
# refrigerant: ısı pompası → R-32, değilse → R-410A.
years = sorted([r["y"] for r in df_kpi.select(F.year("date").alias("y")).distinct().collect()])
print(f"   Veri yılları: {years}")

df_refrig = (
    df_b.filter(col("has_hvac_traditional") | col("has_heat_pump"))
    .withColumn("year", F.explode(F.array(*[lit(y) for y in years])))
    .withColumn("event_date", F.make_date(col("year"), lit(7), lit(1)))
    .withColumn("refrigerant", when(col("has_heat_pump"), lit("R-32")).otherwise(lit("R-410A")))
    .withColumn("topup_kg", F.round(col("area_m2") * 0.00107, 2))
    .withColumn("data_source", lit("synthetic_demo"))
    .select("building_id", "event_date", "refrigerant", "topup_kg", "data_source")
)
df_refrig.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable("silver_refrigerant_log")
print(f"✅ silver_refrigerant_log: {df_refrig.count()} kayıt (Scope 1 refrigerant)")


# =============================================================================
# 2 — silver_supplier_contracts  (market-based Scope 2)
# =============================================================================
# Binaların ~%35'i yeşil sözleşmeli (GoO) → supplier_ef 0.020; gerisi NULL → residual mix.
df_supplier = (
    df_b
    .withColumn("_h", F.abs(F.hash(F.concat(col("building_id"), lit("green")))) % 100)
    .withColumn("has_green_contract", col("_h") < 35)
    .withColumn(
        "supplier_ef_kg_kwh",
        when(col("has_green_contract"), lit(0.020)).otherwise(lit(None).cast("double")),
    )
    .withColumn("data_source", lit("synthetic_demo"))
    .select("building_id", "has_green_contract", "supplier_ef_kg_kwh", "data_source")
)
df_supplier.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable("silver_supplier_contracts")
_green = df_supplier.filter(col("has_green_contract")).count()
print(f"✅ silver_supplier_contracts: {df_supplier.count()} bina ({_green} yeşil sözleşme)")


# =============================================================================
# 3 — silver_tenant_energy  (Scope 3 Cat 13 — downstream leased)
# =============================================================================
# Binaların ~%40'ı çok-kiracılı; kiraya verilen pay %50 → tenant_kwh = aylık tüketim×0.5.
df_month = (
    df_kpi.withColumn("year_month", F.date_trunc("month", col("date")).cast(DateType()))
    .groupBy("building_id", "year_month")
    .agg(F.sum("total_consumption_kwh").alias("m_kwh"))
)
df_multi = (
    df_b.withColumn("_h", F.abs(F.hash(F.concat(col("building_id"), lit("tenant")))) % 100)
    .withColumn("leased_fraction", when(col("_h") < 40, lit(0.5)).otherwise(lit(0.0)))
    .select("building_id", "leased_fraction")
)
df_tenant = (
    df_month.join(df_multi, "building_id", "left")
    .withColumn("tenant_kwh", F.round(col("m_kwh") * F.coalesce(col("leased_fraction"), lit(0.0)), 1))
    .filter(col("tenant_kwh") > 0)
    .withColumn("data_source", lit("synthetic_demo"))
    .select("building_id", "year_month", "tenant_kwh", "data_source")
)
df_tenant.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable("silver_tenant_energy")
print(f"✅ silver_tenant_energy: {df_tenant.count()} bina-ay (Scope 3 Cat 13)")


# =============================================================================
# 4 — silver_org_activity  (Scope 3 Cat 5/6/7 sürücüsü — headcount)
# =============================================================================
# headcount = alan / yoğunluk (bina tipi). Cat 5/6/7 motorda headcount × ref faktör.
_dens = (
    when(col("building_type") == "Office", lit(12.0))
    .when(col("building_type") == "Retail", lit(30.0))
    .when(col("building_type") == "Hotel", lit(50.0))
    .when(col("building_type") == "Logistics", lit(200.0))
    .when(col("building_type") == "Healthcare", lit(25.0))
    .when(col("building_type") == "Lab", lit(40.0))
    .when(col("building_type") == "DataCenter", lit(500.0))
    .otherwise(lit(20.0))
)
df_org = (
    df_b.withColumn("m2_per_person", _dens)
    .withColumn("headcount", F.greatest(F.round(col("area_m2") / col("m2_per_person")).cast("int"), lit(1)))
    .withColumn("data_source", lit("synthetic_demo"))
    .select("building_id", "headcount", "data_source")
)
df_org.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable("silver_org_activity")
print(f"✅ silver_org_activity: {df_org.count()} bina (headcount → Cat 5/6/7)")

print("""
📋 SONRAKI ADIM:
   → 09_ghg_scope_engine.py çalıştır. Bu 4 tabloyu okuyup tam Scope 1/2/3 üretir.
   → Gerçek pilot verisi gelince: bu 4 tabl