# =============================================================================
# ENERGY COPILOT PLATFORM
# Notebook: anomaly_detection.py
# Layer: GOLD — Rule-Based Anomaly Detection
# =============================================================================
#
# GÖREV (Purpose):
#   Silver temiz veri ve Gold KPI tablolarından rule-based anomaly tespiti yap.
#   Her anomaly: bina, tip, önem seviyesi, açıklama ve önerilen aksiyon içerir.
#
# PHASE 1 — RULE-BASED (bu notebook)
#   Sabit eşik değerleri ve istatistiksel kurallar kullanılır.
#   Makine öğrenmesi yok — hızlı, açıklanabilir, Fabric Trial uyumlu.
#
# PHASE 2 — ML-BASED (gelecek)
#   Isolation Forest, LSTM tabanlı zaman serisi anomaly detection.
#
# TESPİT EDİLEN ANOMALİ TİPLERİ:
#   1. CONSUMPTION_SPIKE    — Günlük tüketim rolling ortalamadan % X fazla
#   2. COP_DEGRADATION      — Isı pompası COP'u rated değerden fazla düştü
#   3. SOLAR_UNDERPERFORM   — Solar üretim irradiansa göre beklenenden az
#   4. AFTER_HOURS_WASTE    — Mesai dışı tüketim oranı eşiği aşıyor
#   5. BATTERY_IDLE         — Batarya uzun süre şarj/deşarj edilmiyor
#   6. DATA_GAP             — Bina için beklenen ölçüm periyodunda veri yok
#   7. HIGH_CARBON_INTENSITY — Karbon yoğunluğu sektör ortalamasının üzerinde
#
# OUTPUT:
#   Tables/gold_anomalies
#   Kolonlar: anomaly_id, building_id, anomaly_type, severity,
#             detected_date, metric_value, threshold_value,
#             description_en, description_de, description_tr,
#             recommended_action_en, is_resolved, detected_at
#
# DP-600 NOTLARI:
#   - gold_kpi_daily'den son 30 gün okunur (partition pruning)
#   - Window function: rolling 7-günlük ortalama tüketim
#   - Broadcast join: silver_building_master (küçük tablo)
#   - MERGE upsert: aynı anomaly günde iki kez üretilmez
#   - OPTIMIZE ZORDER BY (building_id, detected_date)
# =============================================================================


# =============================================================================
# BÖLÜM 1 — SPARK KONFİGÜRASYONU VE IMPORT'LAR
# =============================================================================

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField,
    StringType, DoubleType, IntegerType,
    TimestampType, BooleanType, DateType
)
from pyspark.sql.functions import (
    col, lit, current_timestamp, current_date, to_date,
    datediff, abs as spark_abs,
    avg as spark_avg, stddev as spark_stddev,
    sum as spark_sum, max as spark_max, min as spark_min,
    count, when, coalesce, concat_ws, md5,
    broadcast, date_sub, round as spark_round,
    expr, lag
)
from pyspark.sql.window import Window
from delta.tables import DeltaTable
import logging
from datetime import datetime

spark.conf.set("spark.sql.shuffle.partitions", "8")
spark.conf.set("spark.databricks.delta.schema.autoMerge.enabled", "true")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("anomaly_detection")

print("✅ Spark konfigürasyonu tamamlandı")


# =============================================================================
# BÖLÜM 2 — KONFİGÜRASYON
# =============================================================================

# Tablo yolları
PATHS = {
    "kpi_daily":      "Tables/gold_kpi_daily",
    "building":       "Tables/silver_building_master",
    "anomalies":      "Tables/gold_anomalies",
}

# Kaç günlük KPI verisi analiz edilsin
LOOKBACK_DAYS        = 30   # Rolling pencere için kaynak veri
ROLLING_WINDOW_DAYS  = 7    # Tüketim ortalaması penceresi

# ────────────────────────────────────────────────────────────
# Anomaly eşik değerleri
# ────────────────────────────────────────────────────────────

# CONSUMPTION_SPIKE
SPIKE_STDDEV_FACTOR   = 2.5   # Rolling ortalama + 2.5 × stddev → spike
SPIKE_MIN_PCT_ABOVE   = 0.30  # En az %30 artış olmalı (küçük gürültüyü filtrele)

# COP_DEGRADATION
COP_DROP_THRESHOLD    = 0.25  # Rated COP'un %25'in altına düşerse anomaly
                               # Örn: rated 3.5 → fiili < 2.625
COP_MIN_RATED         = 2.5   # Daha düşük rated COP'lu binaları atla

# SOLAR_UNDERPERFORM
SOLAR_PR_LOW          = 0.65  # Performance Ratio < 0.65 → anomaly
                               # Normal aralık: 0.70 – 0.85
SOLAR_IRRADIANCE_MIN  = 2.0   # Bu irradiance'ın altında analiz yapma (bulutlu gün)

# AFTER_HOURS_WASTE
# Mesai saatleri: 08:00-18:00 hafta içi
AFTER_HOURS_WASTE_PCT = 0.35  # Gece/hafta sonu tüketim toplam tüketimin %35'inden fazlaysa

# BATTERY_IDLE
BATTERY_IDLE_DAYS     = 7     # X gün şarj/deşarj yoksa idle say

# DATA_GAP
DATA_GAP_HOURS        = 6     # Beklenen okuma sayısının altında kalınca gap say
                               # 15 dakikada bir = 4 okuma/saat → 6 saat = 24 eksik okuma

# HIGH_CARBON_INTENSITY
# Sektör referans değerleri (kg CO₂/m²/yıl → günlük: /365)
CARBON_REF_DAILY = {
    "OFFICE":     365 / 365,   # ~1.0 kg/m²/gün
    "RETAIL":     280 / 365,
    "INDUSTRIAL": 420 / 365,
    "HOTEL":      320 / 365,
    "HEALTHCARE": 450 / 365,
    "DEFAULT":    350 / 365,
}
CARBON_EXCEED_FACTOR  = 1.5   # Referansın 1.5 katını aşarsa anomaly

# Önem seviyeleri
SEV_LOW      = "LOW"
SEV_MEDIUM   = "MEDIUM"
SEV_HIGH     = "HIGH"
SEV_CRITICAL = "CRITICAL"

print("✅ Konfigürasyon tamamlandı")
print(f"   Lookback: {LOOKBACK_DAYS} gün | Rolling: {ROLLING_WINDOW_DAYS} gün")


# =============================================================================
# BÖLÜM 3 — YARDIMCI FONKSİYONLAR
# =============================================================================

def log_step(step, count=None, table=None):
    ts = datetime.now().strftime("%H:%M:%S")
    msg = f"[{ts}] {step}"
    if table:  msg += f" | {table}"
    if count is not None: msg += f" | {count:,} satır"
    print(msg)


def table_exists(path):
    # Fabric'te var olmayan Delta tablosu sorgulandığında
    # Java katmanından Py4JJavaError (400 Bad Request) fırlatılır.
    # spark.read ile limit(0) daha sağlam yakalanır.
    try:
        spark.read.format("delta").load(path).limit(0).count()
        return True
    except Exception:
        return False


def notebook_exit(message):
    """Fabric uyumlu notebook çıkışı — mssparkutils veya dbutils dener."""
    print(f"\n⏹️  Notebook durduruluyor: {message}")
    try:
        mssparkutils.notebook.exit(message)
    except NameError:
        try:
            dbutils.notebook.exit(message)
        except NameError:
            raise SystemExit(message)


def upsert_anomalies(df_new, target_path):
    """
    MERGE — anomaly_id üzerinden upsert.
    anomaly_id = md5(building_id + anomaly_type + detected_date)
    Aynı bina, aynı gün, aynı tip anomaly iki kez yazılmaz.
    """
    if df_new is None or df_new.count() == 0:
        print("   ℹ️  Yeni anomaly yok — MERGE atlandı")
        return 0

    count_new = df_new.count()

    if table_exists(target_path):
        dt = DeltaTable.forPath(spark, target_path)
        (dt.alias("t")
            .merge(
                df_new.alias("s"),
                "t.anomaly_id = s.anomaly_id"
            )
            .whenMatchedUpdate(set={
                "metric_value":        "s.metric_value",
                "threshold_value":     "s.threshold_value",
                "severity":            "s.severity",
                "description_en":      "s.description_en",
                "description_de":      "s.description_de",
                "description_tr":      "s.description_tr",
                "recommended_action_en": "s.recommended_action_en",
                "detected_at":         "s.detected_at",
            })
            .whenNotMatchedInsertAll()
            .execute()
        )
    else:
        (df_new.write
            .format("delta")
            .mode("overwrite")
            .option("overwriteSchema", "true")
            .save(target_path)
        )

    log_step(f"✅ Anomaly upsert tamamlandı", count_new, "gold_anomalies")
    return count_new


def build_anomaly_row(
    building_id, anomaly_type, severity, detected_date,
    metric_value, threshold_value,
    desc_en, desc_de, desc_tr, action_en
):
    """Tek anomaly satırı oluşturmak için tuple döner."""
    from pyspark.sql import Row
    anomaly_id = f"{building_id}__{anomaly_type}__{detected_date}"
    return Row(
        anomaly_id=anomaly_id,
        building_id=building_id,
        anomaly_type=anomaly_type,
        severity=severity,
        detected_date=str(detected_date),
        metric_value=float(metric_value) if metric_value is not None else None,
        threshold_value=float(threshold_value) if threshold_value is not None else None,
        description_en=desc_en,
        description_de=desc_de,
        description_tr=desc_tr,
        recommended_action_en=action_en,
        is_resolved=False,
        detected_at=datetime.utcnow(),
    )


# Anomaly DataFrame şeması
ANOMALY_SCHEMA = StructType([
    StructField("anomaly_id",            StringType(),    False),
    StructField("building_id",           StringType(),    False),
    StructField("anomaly_type",          StringType(),    True),
    StructField("severity",              StringType(),    True),
    StructField("detected_date",         StringType(),    True),
    StructField("metric_value",          DoubleType(),    True),
    StructField("threshold_value",       DoubleType(),    True),
    StructField("description_en",        StringType(),    True),
    StructField("description_de",        StringType(),    True),
    StructField("description_tr",        StringType(),    True),
    StructField("recommended_action_en", StringType(),    True),
    StructField("is_resolved",           BooleanType(),   True),
    StructField("detected_at",           TimestampType(), True),
])

print("✅ Yardımcı fonksiyonlar hazır")


# =============================================================================
# BÖLÜM 4 — VERİ OKUMA
# =============================================================================

print("\n" + "="*60)
print("VERİ OKUMA")
print("="*60)

# ── Bağımlılık kontrolü ──────────────────────────────────────
# Bu notebook gold_kpi_daily ve silver_building_master tablolarına
# bağımlıdır. Bunlar yoksa notebook hata vermeden çıkar —
# pipeline'da upstream adımların başarısız olduğu durumu yönetir.

missing = []
for key, path in [("gold_kpi_daily", PATHS["kpi_daily"]),
                  ("silver_building_master", PATHS["building"])]:
    if not table_exists(path):
        missing.append(key)

if missing:
    print(f"\n⚠️  Bağımlı tablolar henüz oluşturulmamış: {missing}")
    print("   Lütfen önce şu notebook'ları çalıştır:")
    if "gold_kpi_daily" in missing:
        print("   → 03_gold_kpi_engine.py")
    if "silver_building_master" in missing:
        print("   → 02_silver_transformation.py")
    print("\n   Anomaly detection atlanıyor — boş gold_anomalies tablosu oluşturuluyor.")

    # Downstream pipeline adımları bozulmasın diye boş tablo oluştur
    if not table_exists(PATHS["anomalies"]):
        empty_df = spark.createDataFrame([], ANOMALY_SCHEMA)
        (empty_df.write
            .format("delta")
            .mode("overwrite")
            .option("overwriteSchema", "true")
            .save(PATHS["anomalies"])
        )
        print("   ✅ Boş gold_anomalies tablosu oluşturuldu.")

    # Notebook'u sessizce sonlandır
    notebook_exit("SKIPPED: upstream tables not ready")

# ── Tablolar mevcut, veriyi oku ──────────────────────────────

# gold_kpi_daily — son 30 gün
df_kpi = (
    spark.read.format("delta").load(PATHS["kpi_daily"])
    .filter(col("date") >= date_sub(current_date(), LOOKBACK_DAYS))
)
log_step("gold_kpi_daily okundu", df_kpi.count(), "gold_kpi_daily")

# silver_building_master — broadcast (küçük referans tablosu)
# DP-600 NOT: gold_kpi_daily zaten şu kolonları içeriyor (KPI engine'den geliyor):
#   has_heat_pump, has_pv, has_battery, pv_capacity_kwp, battery_capacity_kwh
# Bunları df_building'den seçmiyoruz — join sonrası AMBIGUOUS_REFERENCE hatası verir.
# Sadece gold_kpi_daily'de OLMAYAN kolonları alıyoruz:
df_building = broadcast(
    spark.read.format("delta").load(PATHS["building"])
    .select(
        "building_id",
        "building_type",          # kpi_daily'de yok
        "country_code",           # kpi_daily'de yok
        "heat_pump_cop_rated",    # kpi_daily'de yok — COP degradasyon tespiti için
        "heat_pump_capacity_kw",  # kpi_daily'de yok
        "conditioned_area_m2",    # kpi_daily'de floor_area_m2 adıyla var, biz orijinalini alıyoruz
        "subscription_tier",      # kpi_daily'de yok
    )
)
log_step("silver_building_master okundu", df_building.count(), "silver_building_master")

# KPI + building join
df = df_kpi.join(df_building, on="building_id", how="left")
log_step("Join tamamlandı", df.count())

# Tüm bina listesi
buildings = [row["building_id"] for row in df_building.collect()]
print(f"\n📋 Analiz edilecek binalar: {buildings}")


# =============================================================================
# BÖLÜM 5 — ROLLING PENCERE HESAPLAMA
# =============================================================================
# Window function: her bina için son 7 günlük rolling ortalama ve stddev
# Bu değerler CONSUMPTION_SPIKE tespitinde eşik olarak kullanılır

print("\n" + "="*60)
print("ROLLING PENCERE — 7 GÜNLÜK ORTALAMA")
print("="*60)

# Gün bazında toplam tüketim (zaten günlük KPI tablosunda mevcut)
# has_heat_pump, has_pv, has_battery, pv_capacity_kwp, battery_capacity_kwh
# → gold_kpi_daily'den geliyor (df_kpi)
# heat_pump_cop_rated, building_type, conditioned_area_m2
# → silver_building_master'dan geliyor (df_building)
df_daily = (
    df.select(
        "building_id", "date",
        "total_consumption_kwh",
        "eui_kwh_m2",
        "avg_solar_pr",
        "solar_generated_kwh",   # irradiance proxy: üretim > 0 ise güneşli gün
        "battery_charged_kwh",
        "battery_discharged_kwh",
        "carbon_intensity_kg_m2",
        "has_heat_pump",         # kpi_daily'den
        "heat_pump_cop_rated",   # building_master'dan
        "has_pv",                # kpi_daily'den
        "pv_capacity_kwp",       # kpi_daily'den
        "has_battery",           # kpi_daily'den
        "battery_capacity_kwh",  # kpi_daily'den
        "building_type",         # building_master'dan
        "conditioned_area_m2",   # building_master'dan
        "hdd_day"
        # NOT: avg_irradiance_wm2 gold_kpi_daily'de yok — saatlik hesaplamada
        # kullanılıyor ama günlük tabloya yazılmıyor. Proxy olarak
        # solar_generated_kwh > 0 kullanıyoruz (üretim varsa güneşli gün).
    )
    .orderBy("building_id", "date")
)

# Rolling window: son 7 gün (mevcut gün dahil)
# rowsBetween(-6, 0) = önceki 6 gün + bugün = 7 gün
win_roll = (
    Window
    .partitionBy("building_id")
    .orderBy("date")
    .rowsBetween(-ROLLING_WINDOW_DAYS + 1, 0)
)

df_daily = (
    df_daily
    .withColumn("rolling_avg_kwh",    spark_avg("total_consumption_kwh").over(win_roll))
    .withColumn("rolling_stddev_kwh", spark_stddev("total_consumption_kwh").over(win_roll))
    .withColumn("spike_threshold",
        col("rolling_avg_kwh") + (col("rolling_stddev_kwh") * lit(SPIKE_STDDEV_FACTOR))
    )
)

log_step("Rolling pencere hesaplandı", df_daily.count())
df_daily.cache()


# =============================================================================
# BÖLÜM 6 — ANOMALİ TESPİTİ
# =============================================================================

all_anomaly_rows = []

# ─────────────────────────────────────────────────────────────
# ANOMALİ 1: CONSUMPTION_SPIKE
# Günlük tüketim = rolling_avg + 2.5×stddev VE en az %30 fazla
# ─────────────────────────────────────────────────────────────

print("\n── 1/7 Consumption Spike Tespiti ──")

df_spikes = (
    df_daily
    .filter(
        (col("total_consumption_kwh") > col("spike_threshold")) &
        (col("rolling_avg_kwh") > lit(0)) &
        (col("total_consumption_kwh") >
            col("rolling_avg_kwh") * lit(1 + SPIKE_MIN_PCT_ABOVE))
    )
    .select("building_id", "date", "total_consumption_kwh",
            "rolling_avg_kwh", "spike_threshold")
)

spike_rows = df_spikes.collect()
for row in spike_rows:
    bid   = row["building_id"]
    dt    = row["date"]
    val   = round(row["total_consumption_kwh"], 1)
    avg   = round(row["rolling_avg_kwh"], 1)
    thr   = round(row["spike_threshold"], 1)
    pct   = round((val - avg) / avg * 100, 1) if avg > 0 else 0
    sev   = SEV_CRITICAL if pct > 75 else (SEV_HIGH if pct > 50 else SEV_MEDIUM)

    all_anomaly_rows.append(build_anomaly_row(
        building_id    = bid,
        anomaly_type   = "CONSUMPTION_SPIKE",
        severity       = sev,
        detected_date  = dt,
        metric_value   = val,
        threshold_value= thr,
        desc_en = f"Energy consumption {val:.1f} kWh is {pct:.0f}% above 7-day rolling average ({avg:.1f} kWh).",
        desc_de = f"Energieverbrauch {val:.1f} kWh liegt {pct:.0f}% über dem 7-Tage-Rollwert ({avg:.1f} kWh).",
        desc_tr = f"Enerji tüketimi {val:.1f} kWh, 7 günlük hareketli ortalamayı ({avg:.1f} kWh) %{pct:.0f} aşıyor.",
        action_en = "Investigate unusual loads on this day: HVAC fault, equipment left on, unscheduled event or data error.",
    ))

print(f"   → {len(spike_rows)} spike tespit edildi")


# ─────────────────────────────────────────────────────────────
# ANOMALİ 2: COP_DEGRADATION
# Isı pompası: avg_cop (tahmin) rated'ın altına düşmüş
# gold_kpi_daily'de doğrudan COP kolonu yok; EUI ve HDD üzerinden tahmin
# → Eğer kış günü (hdd > 5) ve tüketim/alan yüksekse, HP degradasyonu var sayılır
# NOT: Phase 2'de gerçek COP sensör verisinden hesaplanacak
# ─────────────────────────────────────────────────────────────

print("\n── 2/7 COP Degradation Tespiti ──")

df_cop = (
    df_daily
    .filter(
        (col("has_heat_pump") == "true") &
        (col("heat_pump_cop_rated") >= COP_MIN_RATED) &
        (col("hdd_day") >= 5.0)  # Isıtma gerektiren gün
    )
    # EUI proxy: kış günü ısıtma EUI'si rated COP'a göre normalden %40 fazlaysa sorun var
    # eui_expected = heat_demand / (cop_rated * floor_area)
    # Eğer eui_kwh_m2 > eui_expected * degradation_factor → anomaly
    .withColumn("expected_max_eui",
        lit(8.0) / col("heat_pump_cop_rated")  # 8 kWh/m² ısı talebi proxy
    )
    .filter(col("eui_kwh_m2") > col("expected_max_eui") * lit(1.5))
)

cop_rows = df_cop.collect()
for row in cop_rows:
    bid   = row["building_id"]
    dt    = row["date"]
    val   = round(row["eui_kwh_m2"], 3)
    thr   = round(row["expected_max_eui"] * 1.5, 3)
    rated = row["heat_pump_cop_rated"]
    sev   = SEV_HIGH if val > thr * 1.3 else SEV_MEDIUM

    all_anomaly_rows.append(build_anomaly_row(
        building_id    = bid,
        anomaly_type   = "COP_DEGRADATION",
        severity       = sev,
        detected_date  = dt,
        metric_value   = val,
        threshold_value= thr,
        desc_en = f"Heating EUI {val:.3f} kWh/m² exceeds expected threshold on a heating day (HDD≥5). Possible heat pump COP drop from rated {rated}.",
        desc_de = f"Heiz-EUI {val:.3f} kWh/m² überschreitet Erwartungswert an Heiztag (HGT≥5). Möglicher COP-Abfall von Nennwert {rated}.",
        desc_tr = f"Isıtma EUI {val:.3f} kWh/m², ısıtma günündeki (HDD≥5) beklenti eşiğini aşıyor. Isı pompası COP değeri {rated}'ın altına düşmüş olabilir.",
        action_en = f"Schedule heat pump maintenance inspection. Check refrigerant charge, heat exchanger fouling, and defrost cycle performance.",
    ))

print(f"   → {len(cop_rows)} COP degradasyon tespit edildi")


# ─────────────────────────────────────────────────────────────
# ANOMALİ 3: SOLAR_UNDERPERFORM
# Solar Performance Ratio < SOLAR_PR_LOW VE irradiance > minimum
# PR = actual_generation / (pv_capacity × irradiance × hours)
# gold_kpi_daily'de avg_solar_pr kolonu mevcut
# ─────────────────────────────────────────────────────────────

print("\n── 3/7 Solar Underperformance Tespiti ──")

df_solar = (
    df_daily
    .filter(
        (col("has_pv") == "true") &
        (col("pv_capacity_kwp") > lit(0)) &
        (coalesce(col("avg_solar_pr"), lit(1.0)) < lit(SOLAR_PR_LOW)) &
        # avg_irradiance_wm2 gold_kpi_daily'de yok.
        # Proxy: solar_generated_kwh > 0 → inverter çalışıyor, güneş var
        # ama PR hâlâ düşük → gerçek underperformance
        (coalesce(col("solar_generated_kwh"), lit(0.0)) > lit(0.5))
    )
    .select("building_id", "date", "avg_solar_pr", "solar_generated_kwh", "pv_capacity_kwp")
)

solar_rows = df_solar.collect()
for row in solar_rows:
    bid  = row["building_id"]
    dt   = row["date"]
    pr   = round(row["avg_solar_pr"] or 0, 3)
    gen  = round(row["solar_generated_kwh"] or 0, 1)
    cap  = row["pv_capacity_kwp"]
    sev  = SEV_CRITICAL if pr < 0.50 else (SEV_HIGH if pr < 0.58 else SEV_MEDIUM)

    all_anomaly_rows.append(build_anomaly_row(
        building_id    = bid,
        anomaly_type   = "SOLAR_UNDERPERFORM",
        severity       = sev,
        detected_date  = dt,
        metric_value   = pr,
        threshold_value= SOLAR_PR_LOW,
        desc_en = f"Solar Performance Ratio {pr:.3f} is below threshold {SOLAR_PR_LOW} despite active generation ({gen:.1f} kWh). System capacity: {cap} kWp.",
        desc_de = f"Solar-Performance-Ratio {pr:.3f} unterschreitet Schwellenwert {SOLAR_PR_LOW} trotz aktiver Erzeugung ({gen:.1f} kWh). Anlagenkapazität: {cap} kWp.",
        desc_tr = f"Solar Performans Oranı {pr:.3f}, aktif üretim ({gen:.1f} kWh) olmasına rağmen {SOLAR_PR_LOW} eşiğinin altında. Sistem kapasitesi: {cap} kWp.",
        action_en = f"Check inverter status, panel soiling/shading, string fuses, and monitoring data for gaps. Consider professional IR inspection.",
    ))

print(f"   → {len(solar_rows)} solar underperformance tespit edildi")


# ─────────────────────────────────────────────────────────────
# ANOMALİ 4: BATTERY_IDLE
# Son BATTERY_IDLE_DAYS gün boyunca hem charged hem discharged = 0
# Yani batarya hiç kullanılmamış
# ─────────────────────────────────────────────────────────────

print("\n── 4/7 Battery Idle Tespiti ──")

win_batt = (
    Window
    .partitionBy("building_id")
    .orderBy("date")
    .rowsBetween(-BATTERY_IDLE_DAYS + 1, 0)
)

df_batt_idle = (
    df_daily
    .filter(col("has_battery") == "true")
    .withColumn("sum_charged_window",
        spark_sum(coalesce(col("battery_charged_kwh"), lit(0.0))).over(win_batt)
    )
    .withColumn("sum_discharged_window",
        spark_sum(coalesce(col("battery_discharged_kwh"), lit(0.0))).over(win_batt)
    )
    # Sadece bugünkü satırı al (en güncel veriyi temsil eder)
    .filter(col("date") == date_sub(current_date(), 1))
    .filter(
        (col("sum_charged_window") < lit(0.1)) &
        (col("sum_discharged_window") < lit(0.1))
    )
    .select("building_id", "date", "battery_capacity_kwh",
            "sum_charged_window", "sum_discharged_window")
)

batt_rows = df_batt_idle.collect()
for row in batt_rows:
    bid  = row["building_id"]
    dt   = row["date"]
    cap  = row["battery_capacity_kwh"]

    all_anomaly_rows.append(build_anomaly_row(
        building_id    = bid,
        anomaly_type   = "BATTERY_IDLE",
        severity       = SEV_HIGH,
        detected_date  = dt,
        metric_value   = 0.0,
        threshold_value= 0.1,
        desc_en = f"Battery ({cap} kWh) has not been charged or discharged in the last {BATTERY_IDLE_DAYS} days. Possible BMS fault or disconnection.",
        desc_de = f"Batterie ({cap} kWh) wurde in den letzten {BATTERY_IDLE_DAYS} Tagen weder geladen noch entladen. Möglicher BMS-Fehler oder Trennung.",
        desc_tr = f"Batarya ({cap} kWh) son {BATTERY_IDLE_DAYS} gündür şarj/deşarj edilmemiş. BMS arızası veya bağlantı kesilmesi olabilir.",
        action_en = f"Check BMS connectivity, breaker status, and battery management system logs. Verify battery is not in manual override mode.",
    ))

print(f"   → {len(batt_rows)} battery idle tespit edildi")


# ─────────────────────────────────────────────────────────────
# ANOMALİ 5: HIGH_CARBON_INTENSITY
# Günlük karbon yoğunluğu bina tipi referansının 1.5 katını aşıyor
# ─────────────────────────────────────────────────────────────

print("\n── 5/7 High Carbon Intensity Tespiti ──")

# Bina tipi → referans karbon yoğunluğu (kg CO₂/m²/gün)
# Spark'ta map için when/otherwise zinciri kullanılır
df_carbon = (
    df_daily
    .filter(col("conditioned_area_m2") > lit(0))
    .withColumn("carbon_ref",
        when(col("building_type") == "OFFICE",     lit(CARBON_REF_DAILY.get("OFFICE", 0.96)))
        .when(col("building_type") == "RETAIL",    lit(CARBON_REF_DAILY.get("RETAIL", 0.77)))
        .when(col("building_type") == "INDUSTRIAL",lit(CARBON_REF_DAILY.get("INDUSTRIAL", 1.15)))
        .when(col("building_type") == "HOTEL",     lit(CARBON_REF_DAILY.get("HOTEL", 0.88)))
        .when(col("building_type") == "HEALTHCARE",lit(CARBON_REF_DAILY.get("HEALTHCARE", 1.23)))
        .otherwise(lit(CARBON_REF_DAILY.get("DEFAULT", 0.96)))
    )
    .withColumn("carbon_threshold", col("carbon_ref") * lit(CARBON_EXCEED_FACTOR))
    .filter(
        coalesce(col("carbon_intensity_kg_m2"), lit(0.0)) > col("carbon_threshold")
    )
    .select("building_id", "date", "carbon_intensity_kg_m2",
            "carbon_threshold", "building_type")
)

carbon_rows = df_carbon.collect()
for row in carbon_rows:
    bid  = row["building_id"]
    dt   = row["date"]
    val  = round(row["carbon_intensity_kg_m2"], 4)
    thr  = round(row["carbon_threshold"], 4)
    btyp = row["building_type"]
    sev  = SEV_HIGH if val > thr * 1.3 else SEV_MEDIUM

    all_anomaly_rows.append(build_anomaly_row(
        building_id    = bid,
        anomaly_type   = "HIGH_CARBON_INTENSITY",
        severity       = sev,
        detected_date  = dt,
        metric_value   = val,
        threshold_value= thr,
        desc_en = f"Carbon intensity {val:.4f} kg CO₂/m² exceeds {CARBON_EXCEED_FACTOR}× sector reference for {btyp} buildings ({thr:.4f} kg/m²/day).",
        desc_de = f"Kohlenstoffintensität {val:.4f} kg CO₂/m² überschreitet das {CARBON_EXCEED_FACTOR}-fache des Sektorreferenzwerts für {btyp}-Gebäude ({thr:.4f} kg/m²/Tag).",
        desc_tr = f"Karbon yoğunluğu {val:.4f} kg CO₂/m², {btyp} tipi binalar için sektör referansının {CARBON_EXCEED_FACTOR} katını ({thr:.4f} kg/m²/gün) aşıyor.",
        action_en = f"Review grid emission factor trends, shift flexible loads to low-carbon hours (renewable generation peaks), and consider on-site generation expansion.",
    ))

print(f"   → {len(carbon_rows)} high carbon intensity tespit edildi")


# ─────────────────────────────────────────────────────────────
# ANOMALİ 6: DATA_GAP
# Dün için bir binanın veri sayısı beklenenin altındaysa
# Beklenen: 24 saat × 4 okuma/saat = 96 okuma/gün
# DATA_GAP_HOURS = 6 → 24 eksik okumayı tolere et → min = 96 - 24 = 72
# ─────────────────────────────────────────────────────────────

print("\n── 6/7 Data Gap Tespiti ──")

# gold_kpi_daily'de reading_count kolonu mevcut (hourly agg'den geliyor)
# Günlük beklenti: 24 saat × (reading_count per hour ortalaması)
# gold_kpi_daily'de kolon adı: reading_count (hourly), günlük toplamda yok
# Alternatif: eğer total_consumption_kwh = 0 ve date = dün → gap say

EXPECTED_DAILY_READINGS = 96    # 15 dakikada bir = 4/saat × 24 = 96
MIN_DAILY_READINGS      = EXPECTED_DAILY_READINGS - (DATA_GAP_HOURS * 4)  # = 72

df_gap = (
    df_daily
    .filter(col("date") == date_sub(current_date(), 1))
    .filter(
        (coalesce(col("total_consumption_kwh"), lit(0.0)) == lit(0.0))
    )
    .select("building_id", "date", "total_consumption_kwh")
)

gap_rows = df_gap.collect()
for row in gap_rows:
    bid = row["building_id"]
    dt  = row["date"]

    all_anomaly_rows.append(build_anomaly_row(
        building_id    = bid,
        anomaly_type   = "DATA_GAP",
        severity       = SEV_HIGH,
        detected_date  = dt,
        metric_value   = 0.0,
        threshold_value= float(MIN_DAILY_READINGS),
        desc_en = f"No energy consumption data recorded for {dt}. Sensor, gateway, or data pipeline failure likely.",
        desc_de = f"Keine Energieverbrauchsdaten für {dt} aufgezeichnet. Wahrscheinlich Sensor-, Gateway- oder Datenpipelinefehler.",
        desc_tr = f"{dt} tarihi için enerji tüketim verisi kaydedilmemiş. Sensör, ağ geçidi veya veri hattı arızası muhtemel.",
        action_en = f"Check IoT gateway connectivity, sensor firmware, and data pipeline logs. Verify if manual meter reading is available as fallback.",
    ))

print(f"   → {len(gap_rows)} data gap tespit edildi")


# ─────────────────────────────────────────────────────────────
# ANOMALİ 7: AFTER_HOURS_WASTE
# gold_kpi_daily'de is_night_hour flag'li veriye saatlik bakılması gerekir
# Bu notebook günlük tabloya bakar — tam gece ayrımı Phase 2'de ML ile gelecek
# Proxy: weekend/off-peak EUI analizi için baseline fazla aşılıyorsa flag
# Şimdilik: hafta sonu EUI, hafta içi ortalamasının %70'inden büyükse flag
# ─────────────────────────────────────────────────────────────

print("\n── 7/7 After-Hours Waste Tespiti (Proxy) ──")

from pyspark.sql.functions import dayofweek

# Hafta içi (2=Mon … 6=Fri) vs hafta sonu (1=Sun, 7=Sat)
win_weekday = Window.partitionBy("building_id")

df_weekend = (
    df_daily
    .withColumn("is_weekend",
        when(dayofweek(col("date")).isin(1, 7), lit(True)).otherwise(lit(False))
    )
)

# Hafta içi ortalama EUI
df_weekday_avg = (
    df_weekend
    .filter(col("is_weekend") == lit(False))
    .groupBy("building_id")
    .agg(spark_avg("eui_kwh_m2").alias("weekday_avg_eui"))
)

df_weekend_check = (
    df_weekend
    .filter(col("is_weekend") == lit(True))
    .join(df_weekday_avg, on="building_id", how="left")
    .withColumn("waste_threshold", col("weekday_avg_eui") * lit(AFTER_HOURS_WASTE_PCT * 2))
    .filter(
        (col("weekday_avg_eui").isNotNull()) &
        (col("eui_kwh_m2") > col("waste_threshold")) &
        (col("weekday_avg_eui") > lit(0.0))
    )
    .select("building_id", "date", "eui_kwh_m2", "waste_threshold", "weekday_avg_eui")
)

waste_rows = df_weekend_check.collect()
for row in waste_rows:
    bid  = row["building_id"]
    dt   = row["date"]
    val  = round(row["eui_kwh_m2"], 4)
    thr  = round(row["waste_threshold"], 4)
    avg  = round(row["weekday_avg_eui"], 4)
    pct  = round(val / avg * 100, 1) if avg > 0 else 0
    sev  = SEV_MEDIUM

    all_anomaly_rows.append(build_anomaly_row(
        building_id    = bid,
        anomaly_type   = "AFTER_HOURS_WASTE",
        severity       = sev,
        detected_date  = dt,
        metric_value   = val,
        threshold_value= thr,
        desc_en = f"Weekend EUI {val:.4f} kWh/m² is {pct:.0f}% of weekday average ({avg:.4f}), exceeding {AFTER_HOURS_WASTE_PCT*200:.0f}% threshold.",
        desc_de = f"Wochenend-EUI {val:.4f} kWh/m² beträgt {pct:.0f}% des Werktag-Durchschnitts ({avg:.4f}) und überschreitet den Schwellenwert.",
        desc_tr = f"Hafta sonu EUI {val:.4f} kWh/m², hafta içi ortalamasının ({avg:.4f}) %{pct:.0f}'ini oluşturuyor; eşik aşıldı.",
        action_en = f"Review weekend HVAC schedules, lighting timers, and standby loads. Implement building automation setbacks for unoccupied periods.",
    ))

print(f"   → {len(waste_rows)} after-hours waste tespit edildi")


# =============================================================================
# BÖLÜM 7 — ANOMALY DATAFRAME OLUŞTUR VE YAZ
# =============================================================================

print("\n" + "="*60)
print("GOLD_ANOMALIES YAZMA")
print("="*60)

total_detected = len(all_anomaly_rows)
print(f"\n📊 Toplam tespit edilen anomaly: {total_detected}")

if total_detected > 0:
    df_anomalies = spark.createDataFrame(all_anomaly_rows, schema=ANOMALY_SCHEMA)

    # Önem seviyesine göre özet
    print("\nÖnem Seviyesi Dağılımı:")
    df_anomalies.groupBy("severity", "anomaly_type").count().orderBy("severity", "anomaly_type").show(truncate=False)

    # Gold'a yaz
    written = upsert_anomalies(df_anomalies, PATHS["anomalies"])

    # OPTIMIZE
    try:
        spark.sql(f"OPTIMIZE delta.`{PATHS['anomalies']}` ZORDER BY (building_id, detected_date)")
        print("⚡ OPTIMIZE + ZORDER tamamlandı")
    except Exception as e:
        print(f"⚠️  OPTIMIZE atlandı: {str(e)[:60]}")

else:
    print("✅ Anomaly tespit edilmedi — sistem normal çalışıyor")

    # Tablo yoksa boş tablo oluştur (pipeline downstream adımları bozulmasın)
    if not table_exists(PATHS["anomalies"]):
        empty_df = spark.createDataFrame([], ANOMALY_SCHEMA)
        (empty_df.write
            .format("delta")
            .mode("overwrite")
            .option("overwriteSchema", "true")
            .save(PATHS["anomalies"])
        )
        print("   → Boş gold_anomalies tablosu oluşturuldu")


# =============================================================================
# BÖLÜM 8 — DOĞRULAMA RAPORU
# =============================================================================

print("\n" + "="*60)
print("DOĞRULAMA RAPORU")
print("="*60)

try:
    df_val = spark.read.format("delta").load(PATHS["anomalies"])
    total_in_table = df_val.count()

    print(f"\n📊 gold_anomalies toplam satır: {total_in_table:,}")

    print("\nTip × Önem Dağılımı (tüm zamanlar):")
    (df_val
        .groupBy("anomaly_type", "severity")
        .count()
        .orderBy("anomaly_type", "severity")
        .show(truncate=False)
    )

    print("\nBina Başına Aktif Anomaly Sayısı:")
    (df_val
        .filter(col("is_resolved") == lit(False))
        .groupBy("building_id")
        .count()
        .orderBy(col("count").desc())
        .show(truncate=False)
    )

    print("\nSon 3 Anomaly:")
    (df_val
        .orderBy(col("detected_at").desc())
        .select("building_id", "anomaly_type", "severity", "detected_date", "metric_value")
        .limit(3)
        .show(truncate=False)
    )

except Exception as e:
    print(f"❌ Doğrulama hatası: {str(e)}")


# =============================================================================
# ÖZET
# =============================================================================

print("\n" + "="*60)
print("ANOMALY DETECTION TAMAMLANDI")
print("="*60)
print(f"✅ Analiz penceresi: son {LOOKBACK_DAYS} gün")
print(f"✅ Analiz edilen bina sayısı: {len(buildings)}")
print(f"✅ Bu çalışmada tespit edilen anomaly: {total_detected}")
print(f"✅ Tespit edilen tipler: CONSUMPTION_SPIKE, COP_DEGRADATION,")
print(f"   SOLAR_UNDERPERFORM, BATTERY_IDLE, HIGH_CARBON_INTENSITY,")
print(f"   DATA_GAP, AFTER_HOURS_WASTE")
print(f"✅ Çıktı tablosu: Tables/gold_anomalies")
print(f"\n📌 Phase 2'de ML ile gelecek: Isolation Forest, LSTM anomaly,")
print(f"   real-time saatlik COP hesaplama, granüler after-hours detection.")
print("\n➡️  Sonraki adım: Data Pipeline (Fabric Data Factory)")
