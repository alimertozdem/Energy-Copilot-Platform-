# =============================================================================
# ENERGY COPILOT PLATFORM
# Notebook: 20_residential_model_p1.py
# Layer: SILVER (transformation) — Residential Segment · P1 schema scaffold
# =============================================================================
#
# GÖREV (P1 · 8a):
#   Konut segmenti için BİRİM (unit) grain'ini açan şema iskelesini kur.
#   Bu notebook SADECE boş dimension + şema oluşturur — veri P2 ingestion'da
#   (bina fatura CSV + ısı-maliyet API) gelir. Tamamen additive; ticari pipeline'a
#   DOKUNMAZ.
#
#   NOT: silver_building_master.unit_count + common_area_m2 kolonları burada DEĞİL —
#   onlar üretici şema sahibinde (02_silver_transformation.py) tanımlı.
#
# OUTPUT:
#   silver_unit_master → konut birimi boyutu
#                        (org_id → building_id → UNIT_id zincirinin son halkası)
#
# REFERANS:
#   docs/architecture/residential-data-model.md  §2.3
#   docs/architecture/unified-access-model.md    (erişim omurgası)
#
# IDEMPOTENT: tablo zaten varsa DOKUNMAZ (gelecekteki veriyi korur).
# =============================================================================

from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, BooleanType, TimestampType
)

# -----------------------------------------------------------------------------
# silver_unit_master şeması
# Resident PII İÇERMEZ — kimlik (email/ad) yalnızca Postgres'te durur.
# unit_id = iş anahtarı; Postgres units.fabric_unit_id ile birebir eşleşir (köprü),
# tıpkı bugünkü buildings.fabric_building_id ↔ silver_building_master.building_id gibi.
# -----------------------------------------------------------------------------
unit_schema = StructType([
    StructField("unit_id",     StringType(),    False),  # PK / iş anahtarı  == units.fabric_unit_id
    StructField("building_id", StringType(),    False),  # FK -> silver_building_master.building_id
    StructField("floor",       StringType(),    True),   # DE kat etiketi: 'EG','1','2'…
    StructField("area_m2",     DoubleType(),    True),   # birim ısıtılan yaşam alanı — Wohnfläche/WoFlV (E1)
    StructField("unit_type",   StringType(),    True),   # enum: apartment | maisonette | commercial_unit | common_area (E4)
    StructField("is_heated",   BooleanType(),   True),   # ısıtılmayan bodrum/garaj → KPI paydasından düşer
    StructField("updated_at",  TimestampType(), True),
])

TABLE = "silver_unit_master"

# -----------------------------------------------------------------------------
# Idempotent oluşturma — varsa atla, yoksa boş şemayla yarat.
# saveAsTable: Fabric metastore kaydı zorunlu (02'deki 2026-05-18 FIX ile aynı sebep).
# -----------------------------------------------------------------------------
if spark.catalog.tableExists(TABLE):
    n = spark.table(TABLE).count()
    print(f"ℹ️  {TABLE} zaten var ({n} satır) — idempotent, dokunulmadı.")
else:
    (spark.createDataFrame([], unit_schema).write
        .format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(TABLE))
    print(f"✅ {TABLE} oluşturuldu (boş şema). Veri P2 ingestion'da yüklenecek.")

# Doğrulama
print("\n📐 silver_unit_master şeması:")
spark.table(TABLE).printSchema()
print("🔗 Köprü: silver_unit_master.unit_id  ==  Postgres units.fabric_unit_id")
