# ============================================================
# Energy Copilot Platform – Recommendation Engine
# Notebook : 06_recommendation_engine.py
# Layer    : Gold (Recommendations)
# Author   : Energy Copilot Team
# Updated  : 2026-04-08
# ============================================================
#
# PURPOSE
# -------
# Synthesises compliance scores (05) and simulation ROI results (04)
# into a ranked, actionable recommendation list per building.
# This is the "Copilot" output — the single source of truth for
# "what should this building do next, and in what order?"
#
# RECOMMENDATION TYPES
# --------------------
#   INSTALL_HEAT_PUMP       replace gas/oil boiler → GEG §71 compliance
#   IMPROVE_INSULATION      wall/roof U-value upgrade → GEG §10 + EnEfG
#   EXPAND_BATTERY          add battery capacity → EEG self-consumption
#   INSTALL_SOLAR           add PV system → EEG + EPBD + CO2
#   ENERGY_AUDIT            mandatory audit for large consumers → EnEfG
#   UPGRADE_LIGHTING        LED replacement → quick win, low capex
#   CHANGE_BATTERY_STRATEGY switch self-consumption ↔ peak shaving
#   DEEP_RETROFIT           combined HP + insulation → highest impact
#
# PRIORITY SCORING (0–100)
# ------------------------
#   priority_score = 0.35 × compliance_urgency
#                  + 0.30 × financial_attractiveness
#                  + 0.20 × co2_impact
#                  + 0.15 × payback_speed
#
#   compliance_urgency    = 100 − min(relevant regulation score)
#   financial_attractiveness = normalised NPV/CAPEX ratio
#   co2_impact            = normalised annual CO2 saving (kg)
#   payback_speed         = max(0, 100 − payback_years × 8)
#
# Priority labels: CRITICAL (≥80) | HIGH (65–79) | MEDIUM (45–64) |
#                  LOW (25–44) | INFORMATIONAL (<25)
#
# INPUT TABLES
# ------------
#   gold_simulation_results   hp/bat/ins scenarios with ROI
#   gold_compliance_results   regulation scores + audit flags
#   silver_building_master    technology flags, LED, area
#   gold_kpi_monthly          annual consumption for context
#
# OUTPUT TABLE
# ------------
#   gold_recommendations   one row per building × action_type, ranked 1–N
#
# BMAD PHASE  : L4 (decision logic — synthesis of previous layers)
# DP-600 HINTS: window functions for per-building ranking, Delta MERGE,
#               broadcast on compliance (small lookup), AQE enabled
# ============================================================


# ── 0. IMPORTS & SPARK CONFIG ─────────────────────────────────────────────────

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, lit, when, coalesce, broadcast,
    sum as spark_sum, avg as spark_avg,
    max as spark_max,
    round as spark_round, greatest, least,
    current_timestamp, concat_ws, row_number,
)
from pyspark.sql.window import Window
from delta.tables import DeltaTable

spark = SparkSession.builder.getOrCreate()
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.databricks.delta.schema.autoMerge.enabled", "true")


def log_step(step: str, msg: str = "", rows: int = -1):
    row_str = f"  [{rows:,} rows]" if rows >= 0 else ""
    print(f"[06_REC] {step:40s}{row_str}  {msg}")


# ── 1. TABLE PATHS ─────────────────────────────────────────────────────────────

SILVER_PATHS = {
    "building_master": "Tables/silver_building_master",
}
GOLD_PATHS = {
    "kpi_monthly":          "Tables/gold_kpi_monthly",
    "simulation_results":   "Tables/gold_simulation_results",
    "compliance_results":   "Tables/gold_compliance_results",
    "recommendations":      "Tables/gold_recommendations",
}


# ── 2. SCORING CONSTANTS ───────────────────────────────────────────────────────

# Priority score weights
W_COMPLIANCE  = 0.35
W_FINANCIAL   = 0.30
W_CO2         = 0.20
W_PAYBACK     = 0.15

# Priority label thresholds
PRIORITY_CRITICAL      = 80.0
PRIORITY_HIGH          = 65.0
PRIORITY_MEDIUM        = 45.0
PRIORITY_LOW           = 25.0

# Normalisation denominators (sensible upper bounds for scoring)
MAX_NPV_EUR            = 200_000.0   # NPV above this = perfect financial score
MAX_CO2_SAVING_KG      = 50_000.0   # CO2 saving above this = perfect CO2 score
MAX_PAYBACK_YEARS      = 12.5        # payback above this = 0 payback score

# LED upgrade estimates (no simulation data — use rule-of-thumb)
LED_CAPEX_EUR_M2       = 12.0        # ~€12/m² for LED retrofit
LED_SAVING_PCT         = 0.30        # 30% lighting energy saving
LIGHTING_SHARE_PCT     = 0.20        # 20% of total consumption is lighting
LED_CO2_SAVING_KG_KWH  = 0.4        # kg CO2 per kWh avoided


# ── 3. READ INPUT TABLES ───────────────────────────────────────────────────────

log_step("READ", "Loading input tables …")

df_building  = spark.read.format("delta").load(SILVER_PATHS["building_master"])
df_sim       = spark.read.format("delta").load(GOLD_PATHS["simulation_results"])
df_comp      = spark.read.format("delta").load(GOLD_PATHS["compliance_results"])
df_kpi_m     = spark.read.format("delta").load(GOLD_PATHS["kpi_monthly"])

log_step("READ", "All tables loaded", rows=df_building.count())


# ── 4. ANNUAL CONSUMPTION FOR LED ESTIMATE ────────────────────────────────────

df_annual_kwh = (
    df_kpi_m
    .groupBy("building_id")
    .agg(spark_sum("total_consumption_kwh").alias("annual_consumption_kwh"))
)


# ── 5. BASE JOIN ───────────────────────────────────────────────────────────────

log_step("JOIN", "Joining simulation + compliance + building …")

df_comp_bc = broadcast(df_comp.select(
    "building_id",
    "overall_score",
    "enefg_score", "enefg_audit_required",
    "geg_score", "geg_heating_compliant",
    "geg_wall_compliant", "geg_roof_compliant",
    "eeg_score",
    "epbd_score", "epbd_nzeb_gap_kwh_m2",
    "csrd_score",
    "beptr_score",
    "kfw_programs_applicable",
    "bafa_programs_applicable",
    "yeka_programs_applicable",
))

df_base = (
    df_building.alias("b")
    .join(df_sim.alias("s"),     on="building_id", how="left")
    .join(df_comp_bc.alias("c"), on="building_id", how="left")
    .join(df_annual_kwh.alias("k"), on="building_id", how="left")
    .select(
        # Identifiers
        col("b.building_id"),
        col("b.building_name"),
        col("b.country_code"),
        col("b.building_type"),
        col("b.conditioned_area_m2"),
        col("b.subscription_tier"),
        # Technology flags
        col("b.has_pv"),
        col("b.has_battery"),
        col("b.has_heat_pump"),
        col("b.has_led_lighting"),
        col("b.pv_capacity_kwp"),
        # Annual consumption
        col("k.annual_consumption_kwh"),
        # Compliance scores
        col("c.overall_score"),
        col("c.enefg_score"),
        col("c.enefg_audit_required"),
        col("c.geg_score"),
        col("c.geg_heating_compliant"),
        col("c.geg_wall_compliant"),
        col("c.geg_roof_compliant"),
        col("c.eeg_score"),
        col("c.epbd_score"),
        col("c.epbd_nzeb_gap_kwh_m2"),
        col("c.csrd_score"),
        col("c.beptr_score"),
        col("c.kfw_programs_applicable"),
        col("c.bafa_programs_applicable"),
        col("c.yeka_programs_applicable"),
        # Heat pump scenario
        col("s.hp_is_feasible"),
        col("s.hp_annual_saving_eur"),
        col("s.hp_capex_eur"),
        col("s.hp_net_capex_eur"),
        col("s.hp_payback_years"),
        col("s.hp_npv_eur"),
        col("s.hp_co2_saving_kg"),
        col("s.hp_kfw_grant_eur"),
        col("s.hp_bafa_grant_eur"),
        col("s.hp_yeka_grant_eur"),
        # Battery scenario
        col("s.bat_is_feasible"),
        col("s.bat_incremental_size_kwh"),
        col("s.bat_annual_saving_eur"),
        col("s.bat_capex_eur"),
        col("s.bat_net_capex_eur"),
        col("s.bat_payback_years"),
        col("s.bat_npv_eur"),
        col("s.bat_kfw_grant_eur"),
        # Insulation scenario
        col("s.ins_is_feasible"),
        col("s.ins_annual_saving_eur"),
        col("s.ins_capex_eur"),
        col("s.ins_net_capex_eur"),
        col("s.ins_payback_years"),
        col("s.ins_npv_eur"),
        col("s.ins_co2_saving_kg"),
        col("s.ins_kfw_grant_eur"),
        col("s.ins_geg_compliant"),
        # Deep retrofit scenario
        col("s.deep_capex_eur"),
        col("s.deep_grant_eur"),
        col("s.deep_net_capex_eur"),
        col("s.deep_annual_saving_eur"),
        col("s.deep_payback_years"),
        col("s.deep_npv_eur"),
    )
)

log_step("JOIN", "Base join complete", rows=df_base.count())


# ── 6. SCORING HELPER FUNCTIONS ────────────────────────────────────────────────

def compliance_urgency(score_col):
    """0–100: how urgent is compliance action? Higher = more urgent."""
    return least(lit(100.0), greatest(lit(0.0), lit(100.0) - score_col))


def financial_score(npv_col, capex_col):
    """0–100: attractiveness of the investment based on NPV/CAPEX ratio."""
    return (
        when(capex_col.isNull() | (capex_col <= 0), lit(0.0))
        .when(npv_col.isNull(), lit(0.0))
        .otherwise(
            least(lit(100.0),
                  greatest(lit(0.0),
                           spark_round(npv_col / lit(MAX_NPV_EUR) * 100.0, 1)))
        )
    )


def co2_score(co2_kg_col):
    """0–100: normalised annual CO2 saving."""
    return (
        when(co2_kg_col.isNull() | (co2_kg_col <= 0), lit(0.0))
        .otherwise(
            least(lit(100.0),
                  greatest(lit(0.0),
                           spark_round(co2_kg_col / lit(MAX_CO2_SAVING_KG) * 100.0, 1)))
        )
    )


def payback_score(payback_col):
    """0–100: faster payback = higher score. 0 years = 100, 12.5 years = 0."""
    return (
        when(payback_col.isNull() | (payback_col >= MAX_PAYBACK_YEARS), lit(0.0))
        .when(payback_col <= 0, lit(100.0))
        .otherwise(
            spark_round(
                greatest(lit(0.0),
                         (1.0 - payback_col / MAX_PAYBACK_YEARS) * 100.0), 1)
        )
    )


def priority_label(score_col):
    return (
        when(score_col >= PRIORITY_CRITICAL, lit("CRITICAL"))
        .when(score_col >= PRIORITY_HIGH,    lit("HIGH"))
        .when(score_col >= PRIORITY_MEDIUM,  lit("MEDIUM"))
        .when(score_col >= PRIORITY_LOW,     lit("LOW"))
        .otherwise(lit("INFORMATIONAL"))
    )


def total_priority(comp_col, fin_col, co2_col, pay_col):
    return spark_round(
        comp_col * W_COMPLIANCE
        + fin_col * W_FINANCIAL
        + co2_col * W_CO2
        + pay_col * W_PAYBACK, 1)


# ── 7. BUILD INDIVIDUAL RECOMMENDATION DATAFRAMES ─────────────────────────────
# Each action type → filtered rows → scored → union'd into one table

log_step("REC", "Building recommendation rows per action type …")

# ── 7a. INSTALL_HEAT_PUMP ──────────────────────────────────────────────────────
# Applicable: has_heat_pump=False AND hp_is_feasible=True

df_hp_rec = (
    df_base
    .filter(
        (col("has_heat_pump") == False) &
        (col("hp_is_feasible") == True) &
        col("hp_net_capex_eur").isNotNull()
    )
    .withColumn("action_type",    lit("INSTALL_HEAT_PUMP"))
    .withColumn("compliance_driver",
        when(col("country_code") == "DE", lit("GEG §71 / EnEfG"))
        .otherwise(lit("EPBD / BEP-TR")))
    .withColumn("_comp_urg",
        compliance_urgency(coalesce(col("geg_score"), col("beptr_score"), lit(50.0))))
    .withColumn("_fin",   financial_score(col("hp_npv_eur"),          col("hp_net_capex_eur")))
    .withColumn("_co2",   co2_score(col("hp_co2_saving_kg")))
    .withColumn("_pay",   payback_score(col("hp_payback_years")))
    .withColumn("priority_score", total_priority(
        col("_comp_urg"), col("_fin"), col("_co2"), col("_pay")))
    .withColumn("annual_saving_eur", col("hp_annual_saving_eur"))
    .withColumn("co2_saving_kg",     col("hp_co2_saving_kg"))
    .withColumn("capex_eur",         col("hp_capex_eur"))
    .withColumn("net_capex_eur",     col("hp_net_capex_eur"))
    .withColumn("payback_years",     col("hp_payback_years"))
    .withColumn("npv_eur",           col("hp_npv_eur"))
    .withColumn("grant_eur",
        coalesce(col("hp_kfw_grant_eur"), lit(0.0))
        + coalesce(col("hp_bafa_grant_eur"), lit(0.0))
        + coalesce(col("hp_yeka_grant_eur"), lit(0.0)))
    .withColumn("grant_programs",
        coalesce(col("kfw_programs_applicable"), col("yeka_programs_applicable")))
    .withColumn("title_en", lit("Install Heat Pump — Replace Fossil Heating"))
    .withColumn("title_de", lit("Wärmepumpe installieren — Fossile Heizung ersetzen"))
    .withColumn("title_tr", lit("Isı Pompası Kur — Fosil Isıtmayı Değiştir"))
    .withColumn("description_en",
        concat_ws(" ",
            lit("Replace current heating system with a heat pump to meet GEG §71"),
            lit("(≥65% renewable heat). Annual saving: €"),
            spark_round(col("hp_annual_saving_eur"), 0).cast("string"),
            lit("| Payback:"),
            spark_round(col("hp_payback_years"), 1).cast("string"),
            lit("years | CO₂ avoided:"),
            spark_round(col("hp_co2_saving_kg") / 1000.0, 1).cast("string"),
            lit("t/year")))
    .withColumn("description_de",
        concat_ws(" ",
            lit("Heizungsanlage durch Wärmepumpe ersetzen (GEG §71: ≥65% erneuerbare Wärme)."),
            lit("Jährliche Einsparung: €"),
            spark_round(col("hp_annual_saving_eur"), 0).cast("string"),
            lit("| Amortisation:"),
            spark_round(col("hp_payback_years"), 1).cast("string"),
            lit("Jahre | CO₂-Einsparung:"),
            spark_round(col("hp_co2_saving_kg") / 1000.0, 1).cast("string"),
            lit("t/Jahr")))
    .withColumn("description_tr",
        concat_ws(" ",
            lit("Mevcut ısıtma sistemini ısı pompasıyla değiştirin (GEG §71: ≥%65 yenilenebilir ısı)."),
            lit("Yıllık tasarruf: ₺/€"),
            spark_round(col("hp_annual_saving_eur"), 0).cast("string"),
            lit("| Geri ödeme:"),
            spark_round(col("hp_payback_years"), 1).cast("string"),
            lit("yıl | CO₂ tasarrufu:"),
            spark_round(col("hp_co2_saving_kg") / 1000.0, 1).cast("string"),
            lit("t/yıl")))
)

# ── 7b. IMPROVE_INSULATION ─────────────────────────────────────────────────────
# Applicable: ins_is_feasible=True AND (wall or roof not GEG-compliant)

df_ins_rec = (
    df_base
    .filter(
        (col("ins_is_feasible") == True) &
        (col("ins_net_capex_eur").isNotNull()) &
        (
            (col("geg_wall_compliant") == False) |
            (col("geg_roof_compliant") == False) |
            (col("ins_geg_compliant") == False)
        )
    )
    .withColumn("action_type", lit("IMPROVE_INSULATION"))
    .withColumn("compliance_driver",
        when(col("country_code") == "DE", lit("GEG §10 / EnEfG / EPBD"))
        .otherwise(lit("EPBD / BEP-TR")))
    .withColumn("_comp_urg",
        compliance_urgency(
            least(
                coalesce(col("geg_score"),   lit(100.0)),
                coalesce(col("epbd_score"),  lit(100.0)),
            )))
    .withColumn("_fin",  financial_score(col("ins_npv_eur"),      col("ins_net_capex_eur")))
    .withColumn("_co2",  co2_score(col("ins_co2_saving_kg")))
    .withColumn("_pay",  payback_score(col("ins_payback_years")))
    .withColumn("priority_score", total_priority(
        col("_comp_urg"), col("_fin"), col("_co2"), col("_pay")))
    .withColumn("annual_saving_eur", col("ins_annual_saving_eur"))
    .withColumn("co2_saving_kg",     col("ins_co2_saving_kg"))
    .withColumn("capex_eur",         col("ins_capex_eur"))
    .withColumn("net_capex_eur",     col("ins_net_capex_eur"))
    .withColumn("payback_years",     col("ins_payback_years"))
    .withColumn("npv_eur",           col("ins_npv_eur"))
    .withColumn("grant_eur",         coalesce(col("ins_kfw_grant_eur"), lit(0.0)))
    .withColumn("grant_programs",    col("kfw_programs_applicable"))
    .withColumn("title_en", lit("Improve Building Insulation — Wall & Roof"))
    .withColumn("title_de", lit("Gebäudedämmung verbessern — Wand & Dach"))
    .withColumn("title_tr", lit("Bina Yalıtımını İyileştir — Duvar ve Çatı"))
    .withColumn("description_en",
        concat_ws(" ",
            lit("Upgrade wall and roof insulation to meet GEG §10 U-value limits"),
            lit("(wall ≤0.24, roof ≤0.20 W/m²K). Annual heating saving: €"),
            spark_round(col("ins_annual_saving_eur"), 0).cast("string"),
            lit("| Payback:"),
            spark_round(col("ins_payback_years"), 1).cast("string"),
            lit("years")))
    .withColumn("description_de",
        concat_ws(" ",
            lit("Wand- und Dachdämmung auf GEG §10 U-Wert-Grenzwerte verbessern"),
            lit("(Wand ≤0,24, Dach ≤0,20 W/m²K). Jährliche Heizeinsparung: €"),
            spark_round(col("ins_annual_saving_eur"), 0).cast("string"),
            lit("| Amortisation:"),
            spark_round(col("ins_payback_years"), 1).cast("string"),
            lit("Jahre")))
    .withColumn("description_tr",
        concat_ws(" ",
            lit("Duvar ve çatı yalıtımını GEG §10 U-değeri limitlerini karşılayacak şekilde iyileştirin"),
            lit("(duvar ≤0.24, çatı ≤0.20 W/m²K). Yıllık ısıtma tasarrufu: €"),
            spark_round(col("ins_annual_saving_eur"), 0).cast("string"),
            lit("| Geri ödeme:"),
            spark_round(col("ins_payback_years"), 1).cast("string"),
            lit("yıl")))
)

# ── 7c. EXPAND_BATTERY ─────────────────────────────────────────────────────────
# Applicable: bat_is_feasible=True AND bat_incremental_size_kwh > 2

df_bat_rec = (
    df_base
    .filter(
        (col("bat_is_feasible") == True) &
        (col("bat_incremental_size_kwh") > 2.0) &
        col("bat_net_capex_eur").isNotNull()
    )
    .withColumn("action_type", lit("EXPAND_BATTERY"))
    .withColumn("compliance_driver",
        when(col("country_code") == "DE", lit("EEG / EPBD"))
        .otherwise(lit("EPBD / BEP-TR")))
    .withColumn("_comp_urg",
        compliance_urgency(coalesce(col("eeg_score"), col("epbd_score"), lit(50.0))))
    .withColumn("_fin",  financial_score(col("bat_npv_eur"),      col("bat_net_capex_eur")))
    .withColumn("_co2",  co2_score(
        col("bat_annual_saving_eur") / lit(0.30) * lit(0.35)))  # proxy CO2 from saving
    .withColumn("_pay",  payback_score(col("bat_payback_years")))
    .withColumn("priority_score", total_priority(
        col("_comp_urg"), col("_fin"), col("_co2"), col("_pay")))
    .withColumn("annual_saving_eur", col("bat_annual_saving_eur"))
    .withColumn("co2_saving_kg",
        spark_round(col("bat_annual_saving_eur") / lit(0.30) * lit(0.35), 0))
    .withColumn("capex_eur",     col("bat_capex_eur"))
    .withColumn("net_capex_eur", col("bat_net_capex_eur"))
    .withColumn("payback_years", col("bat_payback_years"))
    .withColumn("npv_eur",       col("bat_npv_eur"))
    .withColumn("grant_eur",     coalesce(col("bat_kfw_grant_eur"), lit(0.0)))
    .withColumn("grant_programs", col("kfw_programs_applicable"))
    .withColumn("title_en", lit("Expand Battery Storage — Optimise Self-Consumption"))
    .withColumn("title_de", lit("Batteriespeicher erweitern — Eigenverbrauch optimieren"))
    .withColumn("title_tr", lit("Batarya Kapasitesini Artır — Öz-Tüketimi Optimize Et"))
    .withColumn("description_en",
        concat_ws(" ",
            lit("Add"),
            spark_round(col("bat_incremental_size_kwh"), 0).cast("string"),
            lit("kWh battery capacity to increase solar self-consumption and reduce grid peak."),
            lit("Annual saving: €"),
            spark_round(col("bat_annual_saving_eur"), 0).cast("string"),
            lit("| Payback:"),
            spark_round(col("bat_payback_years"), 1).cast("string"),
            lit("years")))
    .withColumn("description_de",
        concat_ws(" ",
            lit(""),
            spark_round(col("bat_incremental_size_kwh"), 0).cast("string"),
            lit("kWh Batteriekapazität hinzufügen, um Eigenverbrauch zu steigern."),
            lit("Jährliche Einsparung: €"),
            spark_round(col("bat_annual_saving_eur"), 0).cast("string"),
            lit("| Amortisation:"),
            spark_round(col("bat_payback_years"), 1).cast("string"),
            lit("Jahre")))
    .withColumn("description_tr",
        concat_ws(" ",
            lit(""),
            spark_round(col("bat_incremental_size_kwh"), 0).cast("string"),
            lit("kWh batarya kapasitesi ekleyerek solar öz-tüketimi artırın."),
            lit("Yıllık tasarruf: €"),
            spark_round(col("bat_annual_saving_eur"), 0).cast("string"),
            lit("| Geri ödeme:"),
            spark_round(col("bat_payback_years"), 1).cast("string"),
            lit("yıl")))
)

# ── 7d. INSTALL_SOLAR ──────────────────────────────────────────────────────────
# Applicable: has_pv=False AND eeg_score < 70 (or beptr/epbd poor)
# Financial estimate: use industry avg €900/kWp, roof_area for sizing

df_solar_rec = (
    df_base
    .filter(
        (col("has_pv") == False) &
        (
            (col("eeg_score") < 70) |
            (col("epbd_score") < 65) |
            (col("beptr_score") < 65)
        )
    )
    # Estimate: 10% of conditioned area as roof area, 0.15 kWp/m²
    .withColumn("_est_kwp",
        spark_round(col("conditioned_area_m2") * 0.10 * 0.15, 1))
    .withColumn("_est_capex",
        spark_round(col("_est_kwp") * 1100.0, 0))    # €1100/kWp installed
    .withColumn("_est_annual_kwh",
        spark_round(col("_est_kwp") * 950.0, 0))     # 950 kWh/kWp/year avg
    .withColumn("_est_saving",
        spark_round(col("_est_annual_kwh") * 0.28, 0))  # €0.28/kWh avg
    .withColumn("_est_co2",
        spark_round(col("_est_annual_kwh") * 0.35, 0))  # 0.35 kg CO2/kWh grid
    .withColumn("_est_payback",
        when(col("_est_saving") > 0,
             spark_round(col("_est_capex") / col("_est_saving"), 1))
        .otherwise(lit(99.0)))
    .withColumn("_est_npv",
        spark_round(col("_est_saving") * 8.5 - col("_est_capex"), 0))  # ~8.5x annuity
    .withColumn("action_type", lit("INSTALL_SOLAR"))
    .withColumn("compliance_driver",
        when(col("country_code") == "DE", lit("EEG / EPBD / CSRD"))
        .otherwise(lit("EPBD / BEP-TR / CSRD")))
    .withColumn("_comp_urg",
        compliance_urgency(
            least(
                coalesce(col("eeg_score"),  lit(100.0)),
                coalesce(col("epbd_score"), lit(100.0)),
            )))
    .withColumn("_fin",  financial_score(col("_est_npv"),     col("_est_capex")))
    .withColumn("_co2",  co2_score(col("_est_co2")))
    .withColumn("_pay",  payback_score(col("_est_payback")))
    .withColumn("priority_score", total_priority(
        col("_comp_urg"), col("_fin"), col("_co2"), col("_pay")))
    .withColumn("annual_saving_eur", col("_est_saving"))
    .withColumn("co2_saving_kg",     col("_est_co2"))
    .withColumn("capex_eur",         col("_est_capex"))
    .withColumn("net_capex_eur",     col("_est_capex"))  # no grant estimate without sim
    .withColumn("payback_years",     col("_est_payback"))
    .withColumn("npv_eur",           col("_est_npv"))
    .withColumn("grant_eur",         lit(0.0))
    .withColumn("grant_programs",
        when(col("country_code") == "DE", lit("KfW 270 Erneuerbare Energien"))
        .when(col("country_code") == "TR", lit("YEKA GES Teşviki"))
        .otherwise(lit(None)))
    .withColumn("title_en", lit("Install Solar PV System"))
    .withColumn("title_de", lit("Photovoltaikanlage installieren"))
    .withColumn("title_tr", lit("Solar PV Sistemi Kur"))
    .withColumn("description_en",
        concat_ws(" ",
            lit("Install an estimated"),
            col("_est_kwp").cast("string"),
            lit("kWp PV system. Estimated annual generation:"),
            col("_est_annual_kwh").cast("string"),
            lit("kWh | Saving: €"),
            col("_est_saving").cast("string"),
            lit("| Payback:"),
            col("_est_payback").cast("string"),
            lit("years. Note: run full simulation for accurate sizing.")))
    .withColumn("description_de",
        concat_ws(" ",
            lit("Photovoltaikanlage mit geschätzt"),
            col("_est_kwp").cast("string"),
            lit("kWp installieren. Geschätzte jährliche Erzeugung:"),
            col("_est_annual_kwh").cast("string"),
            lit("kWh | Einsparung: €"),
            col("_est_saving").cast("string"),
            lit("| Amortisation:"),
            col("_est_payback").cast("string"),
            lit("Jahre. Hinweis: vollständige Simulation für genaue Auslegung empfohlen.")))
    .withColumn("description_tr",
        concat_ws(" ",
            lit("Tahmini"),
            col("_est_kwp").cast("string"),
            lit("kWp PV sistemi kurun. Tahmini yıllık üretim:"),
            col("_est_annual_kwh").cast("string"),
            lit("kWh | Tasarruf: €"),
            col("_est_saving").cast("string"),
            lit("| Geri ödeme:"),
            col("_est_payback").cast("string"),
            lit("yıl. Not: kesin boyutlandırma için tam simülasyon çalıştırın.")))
)

# ── 7e. ENERGY_AUDIT ───────────────────────────────────────────────────────────
# Applicable: enefg_audit_required=True (Germany, large consumer)

df_audit_rec = (
    df_base
    .filter(
        (col("enefg_audit_required") == True) &
        (col("country_code") == "DE")
    )
    .withColumn("action_type",       lit("ENERGY_AUDIT"))
    .withColumn("compliance_driver", lit("EnEfG §8 — Large Consumer"))
    .withColumn("_comp_urg",
        compliance_urgency(coalesce(col("enefg_score"), lit(0.0))))
    .withColumn("_fin",  lit(60.0))   # audit is a pre-requisite, always financially justified
    .withColumn("_co2",  lit(20.0))   # indirect impact
    .withColumn("_pay",  lit(80.0))   # audit is low-cost, fast
    .withColumn("priority_score", total_priority(
        col("_comp_urg"), col("_fin"), col("_co2"), col("_pay")))
    .withColumn("annual_saving_eur", lit(None).cast("double"))
    .withColumn("co2_saving_kg",     lit(None).cast("double"))
    .withColumn("capex_eur",         lit(3500.0))   # typical audit cost
    .withColumn("net_capex_eur",     lit(1750.0))   # ~50% BAFA Energieberatung subsidy
    .withColumn("payback_years",     lit(0.5))      # compliance value is immediate
    .withColumn("npv_eur",           lit(None).cast("double"))
    .withColumn("grant_eur",         lit(1750.0))
    .withColumn("grant_programs",    lit("BAFA Energieberatung für Nichtwohngebäude"))
    .withColumn("title_en", lit("Commission Mandatory Energy Audit (EnEfG §8)"))
    .withColumn("title_de", lit("Pflicht-Energieaudit beauftragen (EnEfG §8)"))
    .withColumn("title_tr", lit("Zorunlu Enerji Denetimi Yaptırın (EnEfG §8)"))
    .withColumn("description_en",
        lit("Your building exceeds 500 MWh/year. EnEfG §8 requires a certified energy audit "
            "every 4 years. Estimated cost: €3,500 (BAFA Energieberatung covers ~50%). "
            "Non-compliance risk: administrative fines up to €50,000."))
    .withColumn("description_de",
        lit("Ihr Gebäude überschreitet 500 MWh/Jahr. EnEfG §8 schreibt alle 4 Jahre "
            "ein zertifiziertes Energieaudit vor. Kosten: ca. 3.500 € "
            "(BAFA Energieberatung übernimmt ~50%). Bußgeldrisiko: bis zu 50.000 €."))
    .withColumn("description_tr",
        lit("Binanız 500 MWh/yıl sınırını aşıyor. EnEfG §8 uyarınca her 4 yılda bir "
            "sertifikalı enerji denetimi zorunludur. Tahmini maliyet: €3.500 "
            "(BAFA Energieberatung ~%50 karşılıyor). Uyumsuzluk cezası: 50.000 €'ya kadar."))
)

# ── 7f. UPGRADE_LIGHTING ───────────────────────────────────────────────────────
# Applicable: has_led_lighting=False

df_led_rec = (
    df_base
    .filter(col("has_led_lighting") == False)
    .withColumn("_led_saving_kwh",
        spark_round(
            coalesce(col("annual_consumption_kwh"), lit(0.0))
            * LIGHTING_SHARE_PCT * LED_SAVING_PCT, 0))
    .withColumn("_led_saving_eur",
        spark_round(col("_led_saving_kwh") * 0.28, 0))
    .withColumn("_led_capex",
        spark_round(col("conditioned_area_m2") * LED_CAPEX_EUR_M2, 0))
    .withColumn("_led_co2",
        spark_round(col("_led_saving_kwh") * LED_CO2_SAVING_KG_KWH, 0))
    .withColumn("_led_payback",
        when(col("_led_saving_eur") > 0,
             spark_round(col("_led_capex") / col("_led_saving_eur"), 1))
        .otherwise(lit(99.0)))
    .withColumn("_led_npv",
        spark_round(col("_led_saving_eur") * 7.0 - col("_led_capex"), 0))
    .withColumn("action_type",       lit("UPGRADE_LIGHTING"))
    .withColumn("compliance_driver", lit("EnEfG / EPBD — Quick Win"))
    .withColumn("_comp_urg",
        compliance_urgency(coalesce(col("enefg_score"), col("epbd_score"), lit(60.0))))
    .withColumn("_fin",  financial_score(col("_led_npv"),     col("_led_capex")))
    .withColumn("_co2",  co2_score(col("_led_co2")))
    .withColumn("_pay",  payback_score(col("_led_payback")))
    .withColumn("priority_score", total_priority(
        col("_comp_urg"), col("_fin"), col("_co2"), col("_pay")))
    .withColumn("annual_saving_eur", col("_led_saving_eur"))
    .withColumn("co2_saving_kg",     col("_led_co2"))
    .withColumn("capex_eur",         col("_led_capex"))
    .withColumn("net_capex_eur",     col("_led_capex"))
    .withColumn("payback_years",     col("_led_payback"))
    .withColumn("npv_eur",           col("_led_npv"))
    .withColumn("grant_eur",         lit(0.0))
    .withColumn("grant_programs",    lit(None).cast("string"))
    .withColumn("title_en", lit("Upgrade to LED Lighting — Quick Win"))
    .withColumn("title_de", lit("LED-Beleuchtung nachrüsten — Quick Win"))
    .withColumn("title_tr", lit("LED Aydınlatmaya Geç — Hızlı Kazanım"))
    .withColumn("description_en",
        concat_ws(" ",
            lit("Replace conventional lighting with LED. Estimated saving:"),
            col("_led_saving_kwh").cast("string"),
            lit("kWh/year (€"),
            col("_led_saving_eur").cast("string"),
            lit(") | Payback:"),
            col("_led_payback").cast("string"),
            lit("years | CO₂ avoided:"),
            spark_round(col("_led_co2") / 1000.0, 1).cast("string"),
            lit("t/year")))
    .withColumn("description_de",
        concat_ws(" ",
            lit("Konventionelle Beleuchtung durch LED ersetzen. Einsparung:"),
            col("_led_saving_kwh").cast("string"),
            lit("kWh/Jahr (€"),
            col("_led_saving_eur").cast("string"),
            lit(") | Amortisation:"),
            col("_led_payback").cast("string"),
            lit("Jahre")))
    .withColumn("description_tr",
        concat_ws(" ",
            lit("Geleneksel aydınlatmayı LED ile değiştirin. Tasarruf:"),
            col("_led_saving_kwh").cast("string"),
            lit("kWh/yıl (€"),
            col("_led_saving_eur").cast("string"),
            lit(") | Geri ödeme:"),
            col("_led_payback").cast("string"),
            lit("yıl")))
)

# ── 7g. DEEP_RETROFIT ──────────────────────────────────────────────────────────
# Applicable: both HP and insulation are feasible + overall_score < 60

df_deep_rec = (
    df_base
    .filter(
        (col("hp_is_feasible") == True) &
        (col("ins_is_feasible") == True) &
        (col("overall_score") < 60.0) &
        col("deep_net_capex_eur").isNotNull()
    )
    .withColumn("action_type",       lit("DEEP_RETROFIT"))
    .withColumn("compliance_driver",
        when(col("country_code") == "DE", lit("GEG §10+§71 / EnEfG / EPBD"))
        .otherwise(lit("EPBD / BEP-TR")))
    .withColumn("_comp_urg",
        compliance_urgency(coalesce(col("overall_score"), lit(50.0))))
    .withColumn("_fin",  financial_score(col("deep_npv_eur"),      col("deep_net_capex_eur")))
    .withColumn("_co2",  co2_score(
        coalesce(col("hp_co2_saving_kg"), lit(0.0))
        + coalesce(col("ins_co2_saving_kg"), lit(0.0))))
    .withColumn("_pay",  payback_score(col("deep_payback_years")))
    .withColumn("priority_score", total_priority(
        col("_comp_urg"), col("_fin"), col("_co2"), col("_pay")))
    .withColumn("annual_saving_eur", col("deep_annual_saving_eur"))
    .withColumn("co2_saving_kg",
        coalesce(col("hp_co2_saving_kg"), lit(0.0))
        + coalesce(col("ins_co2_saving_kg"), lit(0.0)))
    .withColumn("capex_eur",         col("deep_capex_eur"))
    .withColumn("net_capex_eur",     col("deep_net_capex_eur"))
    .withColumn("payback_years",     col("deep_payback_years"))
    .withColumn("npv_eur",           col("deep_npv_eur"))
    .withColumn("grant_eur",         coalesce(col("deep_grant_eur"), lit(0.0)))
    .withColumn("grant_programs",
        concat_ws(" + ",
            col("kfw_programs_applicable"),
            col("bafa_programs_applicable"),
            col("yeka_programs_applicable")))
    .withColumn("title_en", lit("Deep Retrofit — Heat Pump + Insulation Combined"))
    .withColumn("title_de", lit("Tiefgreifende Sanierung — Wärmepumpe + Dämmung"))
    .withColumn("title_tr", lit("Kapsamlı Yenileme — Isı Pompası + Yalıtım"))
    .withColumn("description_en",
        concat_ws(" ",
            lit("Combined heat pump installation and building envelope upgrade for maximum"),
            lit("compliance impact. Annual saving: €"),
            spark_round(col("deep_annual_saving_eur"), 0).cast("string"),
            lit("| Net CAPEX after grants: €"),
            spark_round(col("deep_net_capex_eur"), 0).cast("string"),
            lit("| Payback:"),
            spark_round(col("deep_payback_years"), 1).cast("string"),
            lit("years | NPV: €"),
            spark_round(col("deep_npv_eur"), 0).cast("string")))
    .withColumn("description_de",
        concat_ws(" ",
            lit("Kombinierte Wärmepumpeninstallation und Gebäudehüllenoptimierung für"),
            lit("maximale Compliance-Wirkung. Jährliche Einsparung: €"),
            spark_round(col("deep_annual_saving_eur"), 0).cast("string"),
            lit("| Netto-CAPEX nach Förderung: €"),
            spark_round(col("deep_net_capex_eur"), 0).cast("string"),
            lit("| Amortisation:"),
            spark_round(col("deep_payback_years"), 1).cast("string"),
            lit("Jahre")))
    .withColumn("description_tr",
        concat_ws(" ",
            lit("Maksimum uyum etkisi için ısı pompası kurulumu ve bina zarfı yükseltme kombinasyonu."),
            lit("Yıllık tasarruf: €"),
            spark_round(col("deep_annual_saving_eur"), 0).cast("string"),
            lit("| Hibe sonrası net maliyet: €"),
            spark_round(col("deep_net_capex_eur"), 0).cast("string"),
            lit("| Geri ödeme:"),
            spark_round(col("deep_payback_years"), 1).cast("string"),
            lit("yıl")))
)


# ── 8. UNION ALL RECOMMENDATIONS ──────────────────────────────────────────────

log_step("UNION", "Combining all recommendation types …")

# Select common columns from each type before union
COMMON_COLS = [
    "building_id", "building_name", "country_code", "building_type",
    "subscription_tier",
    "action_type", "compliance_driver", "priority_score",
    "annual_saving_eur", "co2_saving_kg",
    "capex_eur", "net_capex_eur", "payback_years", "npv_eur", "grant_eur",
    "grant_programs",
    "title_en", "title_de", "title_tr",
    "description_en", "description_de", "description_tr",
]

all_recs = [df_hp_rec, df_ins_rec, df_bat_rec,
            df_solar_rec, df_audit_rec, df_led_rec, df_deep_rec]

df_all = all_recs[0].select(COMMON_COLS)
for part in all_recs[1:]:
    df_all = df_all.union(part.select(COMMON_COLS))

log_step("UNION", "All recommendations combined", rows=df_all.count())


# ── 9. RANK WITHIN EACH BUILDING ──────────────────────────────────────────────

log_step("RANK", "Ranking recommendations per building …")

window_spec = Window.partitionBy("building_id").orderBy(col("priority_score").desc())

df_ranked = (
    df_all
    .withColumn("rank", row_number().over(window_spec))
    .withColumn("priority_label", priority_label(col("priority_score")))
    .withColumn("assessed_at", current_timestamp())
    # Keep top 8 recommendations per building (prevents overwhelming UI)
    .filter(col("rank") <= 8)
)

log_step("RANK", "Ranking complete", rows=df_ranked.count())


# ── 10. FINAL SELECT ───────────────────────────────────────────────────────────

df_results = df_ranked.select(
    col("building_id"),
    col("building_name"),
    col("country_code"),
    col("building_type"),
    col("subscription_tier"),
    col("rank"),
    col("action_type"),
    col("priority_label"),
    spark_round(col("priority_score"), 1).alias("priority_score"),
    col("compliance_driver"),
    spark_round(col("annual_saving_eur"), 0).alias("annual_saving_eur"),
    spark_round(col("co2_saving_kg"), 0).alias("co2_saving_kg"),
    spark_round(col("capex_eur"), 0).alias("capex_eur"),
    spark_round(col("net_capex_eur"), 0).alias("net_capex_eur"),
    spark_round(col("grant_eur"), 0).alias("grant_eur"),
    spark_round(col("payback_years"), 1).alias("payback_years"),
    spark_round(col("npv_eur"), 0).alias("npv_eur"),
    col("grant_programs"),
    col("title_en"),
    col("title_de"),
    col("title_tr"),
    col("description_en"),
    col("description_de"),
    col("description_tr"),
    col("assessed_at"),
)


# ── 11. WRITE TO DELTA (MERGE upsert) ─────────────────────────────────────────

log_step("WRITE", "Writing gold_recommendations …")

target_path = GOLD_PATHS["recommendations"]

if DeltaTable.isDeltaTable(spark, target_path):
    spark.conf.set("spark.databricks.delta.schema.autoMerge.enabled", "true")
    delta_tbl = DeltaTable.forPath(spark, target_path)
    (
        delta_tbl.alias("tgt")
        .merge(
            df_results.alias("src"),
            "tgt.building_id = src.building_id AND tgt.action_type = src.action_type"
        )
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )
    log_step("WRITE", "Delta MERGE complete")
else:
    (
        df_results.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .partitionBy("country_code")
        .save(target_path)
    )
    log_step("WRITE", "Delta table created (initial write)")


# ── 12. OPTIMIZE ───────────────────────────────────────────────────────────────

log_step("OPTIMIZE", "Running OPTIMIZE …")
spark.sql(f"OPTIMIZE delta.`{target_path}` ZORDER BY (building_id, rank)")
log_step("OPTIMIZE", "OPTIMIZE complete")


# ── 13. VALIDATION REPORT ──────────────────────────────────────────────────────

log_step("VALIDATE", "Running validation …")

df_val = spark.read.format("delta").load(target_path)
total  = df_val.count()

print()
print("=" * 72)
print("  RECOMMENDATION ENGINE — VALIDATION REPORT")
print("=" * 72)
print(f"  Total recommendations generated : {total}")
print(f"  Buildings covered               : "
      f"{df_val.select('building_id').distinct().count()}")
print()

print("── TOP RECOMMENDATION PER BUILDING ─────────────────────────────────────")
df_val.filter(col("rank") == 1).select(
    "building_id", "country_code", "rank",
    "action_type", "priority_label", "priority_score",
    "annual_saving_eur", "net_capex_eur", "payback_years",
    "compliance_driver",
).orderBy("country_code", col("priority_score").desc()).show(truncate=False)

print("── ALL CRITICAL / HIGH PRIORITY RECOMMENDATIONS ─────────────────────────")
df_val.filter(col("priority_label").isin("CRITICAL", "HIGH")).select(
    "building_id", "rank", "action_type",
    "priority_label", "priority_score",
    "annual_saving_eur", "grant_eur", "payback_years",
).orderBy(col("priority_score").desc()).show(20, truncate=False)

print("── SAMPLE RECOMMENDATION TEXTS ─────────────────────────────────────────")
df_val.filter(col("rank") == 1).select(
    "building_id", "title_en", "description_en"
).show(truncate=60)

print("── FINANCIAL SUMMARY ────────────────────────────────────────────────────")
df_val.groupBy("country_code", "priority_label").agg(
    spark_round(spark_sum("annual_saving_eur") / 1000.0, 0).alias("total_saving_k_eur"),
    spark_round(spark_sum("grant_eur") / 1000.0, 0).alias("total_grants_k_eur"),
    spark_round(spark_avg("payback_years"), 1).alias("avg_payback_years"),
).orderBy("country_code", "priority_label").show(truncate=False)

print("=" * 72)
print("  06_recommendation_engine.py — COMPLETE")
print("=" * 72)
