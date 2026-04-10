# =============================================================================
# ENERGY COPILOT PLATFORM
# Notebook: 07_consumption_forecast.py
# Layer: GOLD — ML Consumption Forecasting (Phase 2)
# =============================================================================
#
# GÖREV (Purpose):
#   Her bina için önümüzdeki 7 günün enerji tüketimini tahmin et.
#   Tahminler Power BI dashboard'unda "Beklenen Tüketim" olarak görünür,
#   anormal sapmalar anomaly detection'ı tetikler.
#
# YÖNTEM: Facebook Prophet (Pandas UDF ile Spark entegrasyonu)
#   - Hafif, Trial kapasitesinde çalışır
#   - Haftalık / mevsimsel kalıpları otomatik öğrenir
#   - hdd_day / cdd_day regressor olarak eklenir (hava etkisi)
#   - Her bina için AYRI model eğitilir (Pandas UDF ile paralel)
#
# GİRDİ:  Tables/gold_kpi_daily   (son 90 gün)
# ÇIKTI:  Tables/gold_consumption_forecast (7 günlük tahmin, bina bazında)
#
# ÇALIŞMA SIKLIĞI: Günlük — her sabah yeni 7 günlük pencere üretir
#
# DP-600 NOTLARI:
#   - Pandas UDF: applyInPandas ile per-group model eğitimi
#   - MERGE upsert: aynı bina + tarih çifti iki kez yazılmaz
#   - OPTIMIZE ZORDER BY (building_id, forecast_date)
# =============================================================================


# =============================================================================
# BÖLÜM 1 — KÜTÜPHANELERİ YÜKLE
# =============================================================================
# Prophet standart Fabric ortamında yüklü değil — pipeline çalışırken
# %pip magic command devre dışı olduğu için subprocess ile kuruyoruz.
# Kurulum ~2-3 dakika sürer.

import subprocess, sys

def install_if_missing(package: str) -> None:
    """Paket eksikse sessizce yükle, zaten varsa atla."""
    try:
        __import__(package.split("==")[0].replace("-", "_"))
        print(f"   ✅ {package} zaten yüklü")
    except ImportError:
        print(f"   📦 {package} yükleniyor...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package, "--quiet", "--no-warn-script-location"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"{package} yüklenemedi:\n{result.stderr}")
        print(f"   ✅ {package} yüklendi")

install_if_missing("prophet")

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField,
    StringType, DoubleType, IntegerType,
    TimestampType, DateType, LongType
)
from pyspark.sql.functions import (
    col, lit, current_timestamp, current_date,
    date_sub, date_add, to_date, datediff,
    count, avg as spark_avg, stddev as spark_stddev,
    min as spark_min, max as spark_max,
    when, coalesce, broadcast
)
from delta.tables import DeltaTable
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import warnings
warnings.filterwarnings("ignore")

spark.conf.set("spark.sql.shuffle.partitions", "8")
spark.conf.set("spark.databricks.delta.schema.autoMerge.enabled", "true")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("consumption_forecast")

print("✅ Kütüphaneler yüklendi")


# =============================================================================
# BÖLÜM 2 — KONFİGÜRASYON
# =============================================================================

PATHS = {
    "kpi_daily":  "Tables/gold_kpi_daily",
    "building":   "Tables/silver_building_master",
    "forecast":   "Tables/gold_consumption_forecast",
    "occupancy":  "Tables/gold_occupancy_profile",    # 08_occupancy_prediction çıktısı
}

# Eğitim ve tahmin parametreleri
TRAINING_DAYS    = 900  # Kaç günlük geçmiş veri kullanılacak (2.5 yıl — sample 2024-2025 verisini kapsar)
MIN_TRAINING_DAYS = 14  # En az bu kadar veri yoksa bina için model kurma
FORECAST_HORIZON = 7    # Kaç gün ilerisi tahmin edilecek

# Prophet model parametreleri
# changepoint_prior_scale: ne kadar "esnek" olsun
#   0.05 = konservatif (ani değişimleri takip etmez)
#   0.5  = agresif (her değişimi takip eder, overfitting riski)
CHANGEPOINT_PRIOR  = 0.1
SEASONALITY_PRIOR  = 10.0   # Mevsimsellik gücü

# Güven aralığı
INTERVAL_WIDTH     = 0.80   # %80 güven aralığı (yhat_lower / yhat_upper)

# Model versiyonu — parametreler değiştiğinde artır
MODEL_VERSION      = "v1.1-prophet-hdd-cdd-occ"   # +occupancy regressor eklendi

print("✅ Konfigürasyon tamamlandı")
print(f"   Eğitim penceresi : {TRAINING_DAYS} gün")
print(f"   Tahmin ufku      : {FORECAST_HORIZON} gün")
print(f"   Min eğitim verisi: {MIN_TRAINING_DAYS} gün")
print(f"   Model versiyonu  : {MODEL_VERSION}")


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
    try:
        spark.read.format("delta").load(path).limit(0).count()
        return True
    except Exception:
        return False


def notebook_exit(message):
    """
    Fabric uyumlu notebook çıkışı.
    Fabric ortamına göre mssparkutils veya dbutils kullanır.
    İkisi de yoksa SystemExit fırlatır — notebook durur.
    """
    print(f"\n⏹️  Notebook durduruluyor: {message}")
    try:
        mssparkutils.notebook.exit(message)
    except NameError:
        try:
            dbutils.notebook.exit(message)
        except NameError:
            raise SystemExit(message)


# =============================================================================
# BÖLÜM 4 — VERİ OKUMA
# =============================================================================

print("\n" + "="*60)
print("VERİ OKUMA")
print("="*60)

# Bağımlılık kontrolü
if not table_exists(PATHS["kpi_daily"]):
    print("⚠️  gold_kpi_daily bulunamadı — önce 03_gold_kpi_engine çalıştır.")
    notebook_exit("SKIPPED: gold_kpi_daily not found")

# Son TRAINING_DAYS günlük KPI verisi
df_kpi = (
    spark.read.format("delta").load(PATHS["kpi_daily"])
    .filter(col("date") >= date_sub(current_date(), TRAINING_DAYS))
    .select(
        "building_id",
        "date",
        "total_consumption_kwh",
        "hdd_day",
        "cdd_day",
        "avg_temperature_c",
    )
    .orderBy("building_id", "date")
)

log_step("gold_kpi_daily okundu", df_kpi.count(), "gold_kpi_daily")

# ── Occupancy profili yükle ────────────────────────────────────────────────
# gold_occupancy_profile: (building_id, day_of_week, hour_of_day, occupancy_probability)
# Günlük doluluk sinyali: iş saatlerinin (09:00–18:00) ortalama doluluk oranı
# day_of_week → 0=Pzt … 6=Paz  (gold_kpi_daily'deki date sütunundan türetilecek)
OCCUPANCY_AVAILABLE = table_exists(PATHS["occupancy"])

if OCCUPANCY_AVAILABLE:
    try:
        df_occ_raw = spark.read.format("delta").load(PATHS["occupancy"])

        # Boş schema kontrolü — DELTA_READ_TABLE_WITHOUT_COLUMNS durumu
        if len(df_occ_raw.columns) == 0:
            raise ValueError("gold_occupancy_profile schema boş (veri yazılmamış)")

        df_occ_daily = (
            df_occ_raw
            .filter(col("hour_of_day").between(9, 18))           # iş saatleri
            .groupBy("building_id", "day_of_week")
            .agg(spark_avg("occupancy_probability").alias("avg_occ_biz_hours"))
        )
        occ_count = df_occ_daily.count()

        if occ_count == 0:
            raise ValueError("gold_occupancy_profile satır içermiyor")

        log_step("gold_occupancy_profile okundu (iş saatleri ortalaması)", occ_count)

        # gold_kpi_daily tarihinden day_of_week türet (0=Pzt … 6=Paz)
        # Spark dayofweek(): 1=Paz, 2=Pzt … → (dayofweek - 2) mod 7
        df_kpi = (
            df_kpi
            .withColumn(
                "day_of_week",
                when(
                    (col("date").cast("string").isNotNull()),
                    ((F.dayofweek("date") + 5) % 7)   # 0=Pzt … 6=Paz
                ).otherwise(0)
            )
            .join(broadcast(df_occ_daily), on=["building_id", "day_of_week"], how="left")
            .withColumn("avg_occ_biz_hours", coalesce(col("avg_occ_biz_hours"), lit(0.5)))
            .drop("day_of_week")    # model için ds'den türetilecek, bu temp kolon
        )
        log_step("Occupancy regressor kpi_daily'e eklendi")

    except Exception as occ_err:
        # Tablo var ama boş/bozuk → nötr değer ile devam et
        df_kpi = df_kpi.withColumn("avg_occ_biz_hours", lit(0.5))
        print(f"⚠️  gold_occupancy_profile okunamadı ({occ_err})")
        print("   → Nötr occupancy (0.5) ile devam ediliyor.")
else:
    # Occupancy notebook henüz çalışmadıysa → sabit 0.5 (nötr) ile devam et
    df_kpi = df_kpi.withColumn("avg_occ_biz_hours", lit(0.5))
    print("⚠️  gold_occupancy_profile bulunamadı → nötr occupancy (0.5) kullanılıyor.")
    print("   Çözüm: 08_occupancy_prediction.py'ı önce çalıştır.")

# ── Bina listesi ve tip bilgisi ───────────────────────────────────────────
from pyspark.sql import functions as F

df_building = broadcast(
    spark.read.format("delta").load(PATHS["building"])
    .select("building_id", "building_type", "country_code", "conditioned_area_m2")
)

# Join
df_train_full = (
    df_kpi
    .join(df_building, on="building_id", how="left")
    .fillna(0.0, subset=["hdd_day", "cdd_day", "avg_temperature_c"])
    .fillna(0.5, subset=["avg_occ_biz_hours"])
)

log_step("Eğitim verisi hazırlandı", df_train_full.count())

# Bina bazında veri kalitesi kontrolü
df_coverage = (
    df_train_full
    .groupBy("building_id")
    .agg(
        count("*").alias("available_days"),
        spark_avg("total_consumption_kwh").alias("avg_daily_kwh"),
        spark_min("date").alias("data_from"),
        spark_max("date").alias("data_to"),
    )
)

print("\n📊 Bina bazında eğitim verisi:")
df_coverage.show(truncate=False)

# Yeterli veri olan binaları filtrele
buildings_ok = [
    row["building_id"]
    for row in df_coverage.collect()
    if row["available_days"] >= MIN_TRAINING_DAYS
]

buildings_skip = [
    row["building_id"]
    for row in df_coverage.collect()
    if row["available_days"] < MIN_TRAINING_DAYS
]

print(f"\n✅ Model kurulacak binalar ({len(buildings_ok)}): {buildings_ok}")
if buildings_skip:
    print(f"⚠️  Yetersiz veri, atlanacak ({len(buildings_skip)}): {buildings_skip}")

df_train = df_train_full.filter(col("building_id").isin(buildings_ok))


# =============================================================================
# BÖLÜM 5 — PANDAS UDF FONKSİYONU (Per-Building Prophet)
# =============================================================================
#
# Pandas UDF Nasıl Çalışır:
#   1. Spark df_train'i building_id'ye göre gruplar
#   2. Her grup (= bir binanın tüm verisi) Python'a Pandas DataFrame olarak gönderilir
#   3. Bu fonksiyon her grup için çalışır, Prophet modeli kurar, tahmin üretir
#   4. Sonucu Pandas DataFrame olarak döndürür
#   5. Spark tüm sonuçları birleştirip Spark DataFrame yapar
#
# applyInPandas: "Bu Pandas fonksiyonunu her gruba uygula"

# Çıktı şeması — Spark'a dönecek DataFrame'in kolonları ve tipleri
FORECAST_SCHEMA = StructType([
    StructField("building_id",       StringType(),    False),
    StructField("forecast_date",     DateType(),      False),
    StructField("predicted_kwh",     DoubleType(),    True),
    StructField("lower_bound_kwh",   DoubleType(),    True),
    StructField("upper_bound_kwh",   DoubleType(),    True),
    StructField("confidence_pct",    DoubleType(),    True),
    StructField("model_mape_pct",    DoubleType(),    True),  # Mean Absolute % Error
    StructField("trained_on_days",   IntegerType(),   True),
    StructField("model_version",     StringType(),    True),
    StructField("forecasted_at",     TimestampType(), True),
])


def forecast_building(pdf: pd.DataFrame) -> pd.DataFrame:
    """
    Tek bir binanın geçmiş tüketim verisinden 7 günlük tahmin üret.

    Parametreler:
        pdf: building_id, date, total_consumption_kwh, hdd_day, cdd_day kolonları olan Pandas DataFrame

    Döndürür:
        FORECAST_SCHEMA'ya uygun Pandas DataFrame (7 satır = 7 gün)
    """
    from prophet import Prophet  # Her worker'da import — Pandas UDF gereksinimi
    import pandas as pd
    from datetime import datetime

    building_id = pdf["building_id"].iloc[0]
    now = datetime.utcnow()

    try:
        # ── Prophet veri formatı ──────────────────────────────
        # Prophet iki kolon bekliyor: "ds" (tarih) ve "y" (tahmin edilecek değer)
        feature_cols = ["ds", "y", "hdd_day", "cdd_day", "avg_occ_biz_hours"]
        df_prophet = pdf.rename(columns={
            "date": "ds",
            "total_consumption_kwh": "y"
        })[[c for c in feature_cols if c in pdf.rename(
            columns={"date":"ds","total_consumption_kwh":"y"}
        ).columns]].copy()

        # avg_occ_biz_hours yoksa (eski model çalıştıysa) nötr değer ekle
        if "avg_occ_biz_hours" not in df_prophet.columns:
            df_prophet["avg_occ_biz_hours"] = 0.5

        df_prophet["ds"] = pd.to_datetime(df_prophet["ds"])
        df_prophet = df_prophet.sort_values("ds").dropna(subset=["y"])
        df_prophet = df_prophet[df_prophet["y"] > 0]  # Sıfır tüketim günlerini çıkar

        if len(df_prophet) < 14:
            return pd.DataFrame(columns=[f.name for f in FORECAST_SCHEMA])

        # ── Model konfigürasyonu ──────────────────────────────
        model = Prophet(
            changepoint_prior_scale=CHANGEPOINT_PRIOR,
            seasonality_prior_scale=SEASONALITY_PRIOR,
            interval_width=INTERVAL_WIDTH,
            weekly_seasonality=True,    # Pzt-Cum vs hafta sonu kalıbı
            daily_seasonality=False,    # Günlük veri kullanıyoruz, saatlik değil
            yearly_seasonality=(len(df_prophet) >= 60),  # 60+ gün varsa açık
        )

        # Regressorlar — tüketimi etkileyen dış faktörler
        # HDD yüksekse ısıtma artar → tüketim artar
        # CDD yüksekse soğutma artar → tüketim artar
        # avg_occ_biz_hours: 0.0 (boş bina) → 1.0 (tam dolu) → doluluk ↑ tüketim ↑
        model.add_regressor("hdd_day",            standardize=True)
        model.add_regressor("cdd_day",            standardize=True)
        model.add_regressor("avg_occ_biz_hours",  standardize=False)  # zaten 0-1

        # ── Model eğitimi ─────────────────────────────────────
        model.fit(df_prophet)

        # ── Cross-validation ile MAPE hesapla ─────────────────
        # MAPE = Mean Absolute Percentage Error
        # "Modelin geçmişte ne kadar yanıldığını" gösterir
        # Küçük veri için basit in-sample hatası kullanıyoruz
        try:
            df_pred_train = model.predict(df_prophet[["ds", "hdd_day", "cdd_day", "avg_occ_biz_hours"]])
            actual = df_prophet["y"].values
            predicted = df_pred_train["yhat"].values
            # Sıfıra bölme koruması
            mask = actual > 0
            if mask.sum() > 0:
                mape = float(np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100)
            else:
                mape = None
        except Exception:
            mape = None

        # ── Gelecek tahmin ────────────────────────────────────
        # Son tarihten 7 gün sonrasını tahmin et
        last_date = df_prophet["ds"].max()
        future_dates = pd.date_range(
            start=last_date + pd.Timedelta(days=1),
            periods=FORECAST_HORIZON,
            freq="D"
        )

        # Gelecek günler için regressor tahminleri
        # Basit yaklaşım: eğitim verisindeki aynı haftanın günü ortalaması
        # Production'da gerçek hava tahmini API'si kullanılır
        df_future = pd.DataFrame({"ds": future_dates})
        # pandas dt.dayofweek: 0=Pzt … 6=Paz (bizim occupancy tablosuyla aynı!)
        df_future["day_of_week"] = df_future["ds"].dt.dayofweek
        df_prophet["day_of_week"] = df_prophet["ds"].dt.dayofweek

        # HDD / CDD: geçmişten aynı haftanın günü ortalaması
        hdd_by_dow = df_prophet.groupby("day_of_week")["hdd_day"].mean()
        cdd_by_dow = df_prophet.groupby("day_of_week")["cdd_day"].mean()
        df_future["hdd_day"] = df_future["day_of_week"].map(hdd_by_dow).fillna(df_prophet["hdd_day"].mean())
        df_future["cdd_day"] = df_future["day_of_week"].map(cdd_by_dow).fillna(df_prophet["cdd_day"].mean())

        # Occupancy: eğitim verisindeki gün bazlı doluluk oranı
        # (gold_occupancy_profile zaten iş saati ortalaması olarak geldi)
        occ_by_dow = df_prophet.groupby("day_of_week")["avg_occ_biz_hours"].mean()
        df_future["avg_occ_biz_hours"] = df_future["day_of_week"].map(occ_by_dow).fillna(
            df_prophet["avg_occ_biz_hours"].mean()
        )

        # Tahmin — tüm regressorlarla
        forecast = model.predict(df_future[["ds", "hdd_day", "cdd_day", "avg_occ_biz_hours"]])

        # ── Sonuçları FORECAST_SCHEMA formatına çevir ─────────
        results = []
        for _, row in forecast.iterrows():
            results.append({
                "building_id":     building_id,
                "forecast_date":   row["ds"].date(),
                "predicted_kwh":   max(0.0, float(row["yhat"])),           # Negatif olmasın
                "lower_bound_kwh": max(0.0, float(row["yhat_lower"])),
                "upper_bound_kwh": max(0.0, float(row["yhat_upper"])),
                "confidence_pct":  float(INTERVAL_WIDTH * 100),
                "model_mape_pct":  mape,
                "trained_on_days": int(len(df_prophet)),
                "model_version":   MODEL_VERSION,
                "forecasted_at":   now,
            })

        return pd.DataFrame(results)

    except Exception as e:
        # Tek bina hata alırsa pipeline durmasın — boş döndür
        print(f"   ⚠️  {building_id} için model hatası: {str(e)[:100]}")
        return pd.DataFrame(columns=[f.name for f in FORECAST_SCHEMA])


# =============================================================================
# BÖLÜM 6 — MODEL EĞİTİMİ VE TAHMİN
# =============================================================================

print("\n" + "="*60)
print("MODEL EĞİTİMİ VE TAHMİN")
print("="*60)
print(f"   {len(buildings_ok)} bina için Prophet modeli eğitiliyor...")
print(f"   Eğitim verisi: son {TRAINING_DAYS} gün")
print(f"   Tahmin: önümüzdeki {FORECAST_HORIZON} gün")
print("   (Bu adım 2-5 dakika sürebilir — her bina için ayrı model)")

# applyInPandas: building_id'ye göre grupla, her gruba forecast_building uygula
df_forecasts = (
    df_train
    .groupBy("building_id")
    .applyInPandas(forecast_building, schema=FORECAST_SCHEMA)
)

# Spark lazy evaluation — count() ile tetikle ve sonucu cache'le
df_forecasts.cache()
forecast_count = df_forecasts.count()

log_step("Tahminler üretildi", forecast_count, "gold_consumption_forecast")

if forecast_count == 0:
    print("⚠️  Hiçbir bina için tahmin üretilemedi — veri kontrolü yap.")
    notebook_exit("WARNING: no forecasts generated")

# Tahmin özeti
print("\n📊 Bina bazında tahmin özeti:")
(df_forecasts
    .groupBy("building_id")
    .agg(
        count("*").alias("forecast_days"),
        spark_avg("predicted_kwh").alias("avg_predicted_kwh"),
        spark_avg("model_mape_pct").alias("avg_mape_pct"),
        spark_avg("trained_on_days").alias("trained_on_days"),
    )
    .show(truncate=False)
)


# =============================================================================
# BÖLÜM 7 — GOLD TABLOSUNA YAZ (MERGE)
# =============================================================================

print("\n" + "="*60)
print("GOLD_CONSUMPTION_FORECAST YAZMA")
print("="*60)

# Merge key: building_id + forecast_date
# Aynı bina için aynı günün tahmini zaten varsa güncelle (model yeniden çalıştı)
# Yoksa ekle

# Tablo var mı VE schema'sı dolu mu?
def table_has_schema(path):
    """Delta tablo var ama boş schema ile yaratılmışsa (DELTA_READ_TABLE_WITHOUT_COLUMNS) False döner."""
    try:
        df_check = spark.read.format("delta").load(path)
        return len(df_check.columns) > 0
    except Exception:
        return False

if table_exists(PATHS["forecast"]) and table_has_schema(PATHS["forecast"]):
    # Tablo var ve schema dolu → MERGE ile güncelle
    dt_forecast = DeltaTable.forPath(spark, PATHS["forecast"])

    (dt_forecast.alias("target")
        .merge(
            df_forecasts.alias("source"),
            "target.building_id = source.building_id AND target.forecast_date = source.forecast_date"
        )
        .whenMatchedUpdate(set={
            "predicted_kwh":   "source.predicted_kwh",
            "lower_bound_kwh": "source.lower_bound_kwh",
            "upper_bound_kwh": "source.upper_bound_kwh",
            "model_mape_pct":  "source.model_mape_pct",
            "model_version":   "source.model_version",
            "forecasted_at":   "source.forecasted_at",
        })
        .whenNotMatchedInsertAll()
        .execute()
    )
    print("✅ MERGE tamamlandı (mevcut tablo güncellendi)")
else:
    # Tablo yok VEYA boş schema ile var → overwrite ile yaz (schema oluşturulur)
    (df_forecasts.write
        .format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .partitionBy("building_id")
        .save(PATHS["forecast"])
    )
    print("✅ Tablo yazıldı (overwrite — boş schema üzerine ya da yeni tablo)")

# OPTIMIZE — küçük dosyaları birleştir
try:
    spark.sql(f"OPTIMIZE delta.`{PATHS['forecast']}` ZORDER BY (building_id, forecast_date)")
    print("⚡ OPTIMIZE + ZORDER tamamlandı")
except Exception as e:
    print(f"⚠️  OPTIMIZE atlandı: {str(e)[:60]}")


# =============================================================================
# BÖLÜM 8 — DOĞRULAMA RAPORU
# =============================================================================

print("\n" + "="*60)
print("DOĞRULAMA RAPORU")
print("="*60)

df_val = spark.read.format("delta").load(PATHS["forecast"])

print(f"\n📊 gold_consumption_forecast toplam satır: {df_val.count():,}")

print("\n7 Günlük Tahminler (tüm binalar):")
(df_val
    .filter(col("forecasted_at") >= date_sub(current_date(), 1))
    .select(
        "building_id",
        "forecast_date",
        "predicted_kwh",
        "lower_bound_kwh",
        "upper_bound_kwh",
        "model_mape_pct",
        "trained_on_days"
    )
    .orderBy("building_id", "forecast_date")
    .show(21, truncate=False)  # 3 bina × 7 gün = 21 satır
)

# MAPE yorumu
print("\n📈 Model Doğruluk Özeti:")
print("   MAPE < 10% → Mükemmel")
print("   MAPE 10-20% → İyi")
print("   MAPE 20-30% → Kabul edilebilir")
print("   MAPE > 30% → Daha fazla veri gerekiyor")

(df_val
    .filter(col("forecasted_at") >= date_sub(current_date(), 1))
    .groupBy("building_id")
    .agg(spark_avg("model_mape_pct").alias("mape_pct"))
    .show(truncate=False)
)


# =============================================================================
# ÖZET
# =============================================================================

print("\n" + "="*60)
print("CONSUMPTION FORECAST TAMAMLANDI")
print("="*60)
print(f"✅ Eğitilen bina sayısı : {len(buildings_ok)}")
print(f"✅ Üretilen tahmin sayısı: {forecast_count:,}")
print(f"✅ Tahmin ufku           : {FORECAST_HORIZON} gün")
occ_status = "gold_occupancy_profile (calibrated)" if OCCUPANCY_AVAILABLE else "nötr 0.5 (occupancy yok)"
print(f"✅ Model                 : Prophet + HDD/CDD + Occupancy regressors")
print(f"✅ Occupancy kaynağı     : {occ_status}")
print(f"✅ Model versiyonu       : {MODEL_VERSION}")
print(f"✅ Çıktı tablosu         : Tables/gold_consumption_forecast")
print(f"\n📌 Sonraki iyileştirmeler:")
print(f"   - Gerçek hava tahmini API'si ile HDD/CDD geleceğini doldur")
print(f"   - Daha fazla tarihsel veri → MAPE düşer, doğruluk artar")
print(f"   - Adaptive anomaly detection (Phase 2 ML)")
print(f"\n➡️  Pipeline'da sıra: Gold Wave 2 — Forecast + Anomaly + Recommendation (parallel)")
