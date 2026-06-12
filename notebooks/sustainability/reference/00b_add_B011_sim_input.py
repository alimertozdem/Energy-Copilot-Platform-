# =============================================================================
# 00b_add_B011_sim_input.py — Residential G2 (FLAT, paste-safe, TEK HÜCRE)
# ref_simulation_inputs'a SADECE B011 satırını ekler/günceller (upsert).
# 00_reference_data_loader'ı tamamen yeniden çalıştırmaya GEREK YOK — bu cerrahi,
# diğer ref tablolarına (profiles, tariffs) dokunmaz.
# Ön koşul: ref_simulation_inputs zaten var (B001/B002/B003 ile).
# Sonra çalıştır: 04_simulation_engine → 06_recommendation_engine.
# Değerler reviewer-onaylı (Mert, 2026-06-12); residential-retrofit-calculations.md hizalı.
# =============================================================================
from delta.tables import DeltaTable
from pyspark.sql import Row
import pyspark.sql.functions as F

NAME = "ref_simulation_inputs"


def _delta():
    # schema-enabled lakehouse: önce catalog, sonra Tables/dbo, sonra Tables/
    try:
        return DeltaTable.forName(spark, NAME)
    except Exception:
        for p in (f"Tables/dbo/{NAME}", f"Tables/{NAME}"):
            try:
                return DeltaTable.forPath(spark, p)
            except Exception:
                continue
    raise Exception(NAME + " bulunamadı (catalog/Tables yolu yok) — önce 00_reference_data_loader çalışmış olmalı")


dt = _delta()
tgt = dt.toDF()

# B011: 1970s Berlin MFH, merkezi gaz. RADIATOR_LT@60 → HP feasible. GEG U-hedefleri.
b011 = {
    "building_id": "B011", "tariff_id": "TAR-DE-TOU",
    "electricity_tariff_eur_kwh": 0.30, "gas_price_eur_kwh": 0.11,
    "feed_in_tariff_eur_kwh": 0.082, "demand_charge_eur_kw_month": 0.0,
    "heating_fuel_type": "GAS", "heating_system_age_years": 30,
    "heat_distribution_type": "RADIATOR_LT", "design_supply_temp_c": 60.0,
    "num_floors": 4, "floor_height_m": 3.0, "building_height_m": 12.0,
    "building_perimeter_m": 100.0, "grid_connection_kw": 250.0,
    "max_solar_export_kw": 50.0, "target_hp_capacity_kw": 100.0,
    "target_battery_kwh": 0.0, "target_wall_u_value": 0.22,
    "target_window_u_value": 0.95, "target_roof_u_value": 0.20,
    "hdd_annual": 3300.0, "cdd_annual": 90.0, "discount_rate_pct": 0.04,
    "energy_price_escalation_pct": 0.03, "project_lifetime_years": 20,
    "data_source": "ESTIMATED",
    "notes": "1970s yenilenmemis MFH Berlin, merkezi gaz, 24 daire/2400m2. "
             "RADIATOR_LT@60C -> HP feasible; GEG U-hedef 0.22/0.95/0.20; gas 0.11 EUR/kWh. "
             "Reviewer-onayli 2026-06-12; residential-retrofit-calculations.md hizali.",
}

# hedef şemaya hizala (kolon sırası + tip), eksik kolonları null yap → şema sürprizine dayanıklı
row_df = spark.createDataFrame([Row(**b011)])
for c in tgt.columns:
    if c not in row_df.columns:
        row_df = row_df.withColumn(c, F.lit(None))
row_df = row_df.select([F.col(c).cast(tgt.schema[c].dataType).alias(c) for c in tgt.columns])

# upsert: building_id'de eşleşirse güncelle, yoksa ekle (tekrar çalıştırmaya güvenli)
(dt.alias("t")
   .merge(row_df.alias("s"), "t.building_id = s.building_id")
   .whenMatchedUpdateAll()
   .whenNotMatchedInsertAll()
   .execute())

out = _delta().toDF().where(F.col("building_id") == "B011")
print("✅ B011 ref_simulation_inputs'ta:", out.count(), "satır")
out.select("building_id", "heating_fuel_type", "heat_distribution_type",
           "design_supply_temp_c", "target_wall_u_value", "target_hp_capacity_kw").show()
