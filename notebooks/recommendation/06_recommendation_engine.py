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
    upper,
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

# ── NEW ACTION TYPE CONSTANTS ─────────────────────────────────────────────────
# Electricity rate by country (EUR/kWh) — used in rule-of-thumb calculations
# Sources: Eurostat 2024 non-household rates, EPDK Turkey 2024
RATE_DE  = 0.28
RATE_TR  = 0.10
RATE_AT  = 0.25
RATE_NL  = 0.26
RATE_DEFAULT = 0.25

# BMS Optimisation
BMS_SAVING_PCT         = 0.08   # 8% total consumption saving — conservative (ISO 50001 studies: 5-15%)
BMS_CAPEX_EUR_M2       = 22.0   # €22/m² conditioned area (hardware + software + commissioning)

# HVAC Scheduling
HVAC_SCHED_SAVING_PCT  = 0.12   # 12% of HVAC consumption (setback + scheduling, IEA benchmark)
HVAC_SCHED_CAPEX_M2    = 10.0   # €10/m² (mostly software, sensors, commissioning)

# CHP Cogeneration
CHP_SAVING_PCT         = 0.22   # 22% of annual energy cost (combined efficiency vs separate generation)
CHP_CAPEX_PER_KWE      = 800.0  # €800/kWe installed (VDI 2067 benchmark)
CHP_PEAK_FRACTION      = 0.30   # CHP sized at 30% of estimated peak demand

# Solar Thermal
SOLAR_THERMAL_CAPEX_M2       = 450.0   # €450/m² collector (installed, Fraunhofer ISE 2024)
SOLAR_THERMAL_M2_PER_M2_COND = 0.035  # Collector area = 3.5% of conditioned area
SOLAR_THERMAL_FRACTION       = 0.50   # 50% solar fraction of hot water demand (annual avg)

# Heat Recovery (Ventilation HRV/ERV)
HEAT_RECOVERY_SAVING_PCT     = 0.15   # 15% of HVAC consumption (EN 13053 efficiency class H1)
HEAT_RECOVERY_CAPEX_M2       = 22.0   # €22/m² conditioned area

# Battery Expansion
BAT_EXP_CAPEX_PER_KWH        = 550.0  # €550/kWh additional capacity (LFP commercial 2024)
BAT_EXP_FRACTION             = 0.50   # Add 50% to existing battery capacity
BAT_EXP_SAVING_PCT           = 0.06   # 6% of annual cost (self-consumption + peak shaving gain)

# Peak Demand Management
PEAK_MGMT_SAVING_PCT         = 0.06   # 6% of annual electricity cost (demand charge reduction)
PEAK_MGMT_CAPEX_FIXED        = 18000.0 # Fixed software + monitoring hardware
PEAK_MGMT_CAPEX_M2           = 3.0    # €3/m² additional sensors

# Power Factor Correction
PFC_SAVING_PCT               = 0.04   # 4% of annual electricity cost (reactive power penalties)
PFC_CAPEX_FIXED              = 15000.0 # Fixed: capacitor bank + control panel

# Submetering Upgrade
SUBMETER_SAVING_PCT          = 0.05   # 5% of total consumption (waste identification)
SUBMETER_CAPEX_M2            = 6.0    # €6/m² (smart meters per zone/floor)
SUBMETER_CAPEX_FIXED         = 4000.0 # Fixed: communication gateway + software


# ── 3. READ INPUT TABLES ───────────────────────────────────────────────────────

log_step("READ", "Loading input tables …")

df_building  = spark.read.format("delta").load(SILVER_PATHS["building_master"])
df_kpi_m     = spark.read.format("delta").load(GOLD_PATHS["kpi_monthly"])

# gold_simulation_results opsiyonel (04_simulation_engine çalışmamışsa yoktur)
try:
    df_sim = spark.read.format("delta").load(GOLD_PATHS["simulation_results"])
    HAS_SIM = True
    log_step("READ", f"gold_simulation_results loaded: {df_sim.count()} rows")
except Exception as _e:
    HAS_SIM = False
    log_step("WARN", f"gold_simulation_results missing — financial scores defaulted to 0: {_e}")
    # Boş schema ile devam et
    from pyspark.sql.types import StructType, StructField, StringType, DoubleType
    df_sim = spark.createDataFrame([], StructType([
        StructField("building_id", StringType(), True),
        StructField("scenario", StringType(), True),
        StructField("npv_eur", DoubleType(), True),
        StructField("capex_eur", DoubleType(), True),
        StructField("payback_years", DoubleType(), True),
        StructField("annual_co2_saving_kg", DoubleType(), True),
    ]))

# gold_compliance_results opsiyonel (05_compliance_checker çalışmamışsa yoktur)
# PIPELINE HATA KAYNAGI: bu tablo yokken notebook tamamen çöküyordu
try:
    df_comp = spark.read.format("delta").load(GOLD_PATHS["compliance_results"])
    HAS_COMP = True
    log_step("READ", f"gold_compliance_results loaded: {df_comp.count()} rows")
except Exception as _e:
    HAS_COMP = False
    log_step("WARN", f"gold_compliance_results missing — compliance urgency defaulted to 50: {_e}")
    from pyspark.sql.types import StructType, StructField, StringType, DoubleType, BooleanType
    # Fallback schema must include ALL columns referenced in df_comp_bc select below.
    # Missing columns here cause UNRESOLVED_COLUMN crash even on empty DataFrame.
    df_comp = spark.createDataFrame([], StructType([
        StructField("building_id",            StringType(),  True),
        StructField("overall_score",           DoubleType(),  True),
        StructField("enefg_score",             DoubleType(),  True),  # DE EnEfG (Energieeffizienzgesetz)
        StructField("enefg_audit_required",    BooleanType(), True),  # EnEfG audit flag (>250 FTE)
        StructField("geg_score",               DoubleType(),  True),  # DE GEG (Gebäudeenergiegesetz)
        StructField("geg_heating_compliant",   BooleanType(), True),
        StructField("geg_wall_compliant",      BooleanType(), True),
        StructField("geg_roof_compliant",      BooleanType(), True),
        StructField("eeg_score",               DoubleType(),  True),  # DE EEG (Erneuerbare-Energien-Gesetz)
        StructField("epbd_score",              DoubleType(),  True),  # EU EPBD 2024
        StructField("epbd_nzeb_gap_kwh_m2",    DoubleType(),  True),  # gap to NZEB target
        StructField("csrd_score",              DoubleType(),  True),  # EU CSRD reporting score
        StructField("beptr_score",             DoubleType(),  True),  # TR BEPTR
        StructField("kfw_programs_applicable", BooleanType(), True),  # DE KfW funding flag
        StructField("bafa_programs_applicable",BooleanType(), True),  # DE BAFA funding flag
        StructField("yeka_programs_applicable",BooleanType(), True),  # TR YEKA funding flag
    ]))

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
        # Extra building flags needed by new action types
        col("b.battery_capacity_kwh"),
        col("b.has_ev_charging"),
        col("b.iso50001_certified"),
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

# Normalize building_type to uppercase for reliable comparisons
# FIX: silver_building_master uses Title Case ("Office"), ref tables use UPPER ("OFFICE")
df_base = df_base.withColumn("building_type_upper", upper(col("building_type")))

# Electricity rate lookup column (EUR/kWh) — reused across all new action types
_elec_rate = (
    when(col("country_code") == "TR", lit(RATE_TR))
    .when(col("country_code") == "DE", lit(RATE_DE))
    .when(col("country_code") == "AT", lit(RATE_AT))
    .when(col("country_code") == "NL", lit(RATE_NL))
    .otherwise(lit(RATE_DEFAULT))
)


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
        coalesce(
            when(col("kfw_programs_applicable")  == True, lit("KfW Bundesförderung")),
            when(col("yeka_programs_applicable") == True, lit("YEKA / ETKB Teşviki")),
            lit(None).cast("string")
        ))
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
    .withColumn("grant_programs",    when(col("kfw_programs_applicable") == True, lit("KfW Bundesförderung")).otherwise(lit(None).cast("string")))
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
    .withColumn("grant_programs", when(col("kfw_programs_applicable") == True, lit("KfW Bundesförderung")).otherwise(lit(None).cast("string")))
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
            when(col("kfw_programs_applicable")  == True, lit("KfW Bundesförderung")),
            when(col("bafa_programs_applicable") == True, lit("BAFA BEG NWG")),
            when(col("yeka_programs_applicable") == True, lit("YEKA / ETKB Teşviki"))
        ))
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


# ── 7g. BMS_OPTIMISATION ──────────────────────────────────────────────────────
# Applicable: ALL buildings — universal quick win, no major capex required
# Savings: 8% of total consumption (ISO 50001 case studies: 5–15% range)
# Source: IEA Building Efficiency Outlook 2023, BPIE Digital Buildings report

df_bms_rec = (
    df_base
    .withColumn("_bms_saving_kwh",
        spark_round(coalesce(col("annual_consumption_kwh"), lit(0.0)) * lit(BMS_SAVING_PCT), 0))
    .withColumn("_rate",  _elec_rate)
    .withColumn("_bms_saving_eur",
        spark_round(col("_bms_saving_kwh") * col("_rate"), 0))
    .withColumn("_bms_capex",
        spark_round(col("conditioned_area_m2") * lit(BMS_CAPEX_EUR_M2), 0))
    .withColumn("_bms_co2",
        spark_round(col("_bms_saving_kwh") * lit(0.4), 0))
    .withColumn("_bms_payback",
        when(col("_bms_saving_eur") > 0,
             spark_round(col("_bms_capex") / col("_bms_saving_eur"), 1))
        .otherwise(lit(99.0)))
    .withColumn("_bms_npv",
        spark_round(col("_bms_saving_eur") * lit(8.0) - col("_bms_capex"), 0))
    .withColumn("action_type",       lit("BMS_OPTIMISATION"))
    .withColumn("compliance_driver", lit("EnEfG §3 / EPBD Art.14 — Smart Readiness"))
    .withColumn("_comp_urg",
        compliance_urgency(coalesce(col("enefg_score"), col("epbd_score"), lit(50.0))))
    .withColumn("_fin",  financial_score(col("_bms_npv"),      col("_bms_capex")))
    .withColumn("_co2",  co2_score(col("_bms_co2")))
    .withColumn("_pay",  payback_score(col("_bms_payback")))
    .withColumn("priority_score",    total_priority(col("_comp_urg"), col("_fin"), col("_co2"), col("_pay")))
    .withColumn("annual_saving_eur", col("_bms_saving_eur"))
    .withColumn("co2_saving_kg",     col("_bms_co2"))
    .withColumn("capex_eur",         col("_bms_capex"))
    .withColumn("net_capex_eur",
        when(col("country_code") == "DE",
             spark_round(col("_bms_capex") * lit(0.70), 0))
        .otherwise(col("_bms_capex")))
    .withColumn("payback_years",     col("_bms_payback"))
    .withColumn("npv_eur",           col("_bms_npv"))
    .withColumn("grant_eur",
        when(col("country_code") == "DE",
             spark_round(col("_bms_capex") * lit(0.30), 0))
        .otherwise(lit(0.0)))
    .withColumn("grant_programs",
        when(col("country_code") == "DE", lit("BAFA BEG NWG — Sanierungsmaßnahmen"))
        .otherwise(lit(None).cast("string")))
    .withColumn("title_en", lit("Optimise Building Management System (BMS/GLT)"))
    .withColumn("title_de", lit("Gebäudeleittechnik (GLT) optimieren — Quick Win"))
    .withColumn("title_tr", lit("Bina Yönetim Sistemi (BYS) Optimizasyonu — Hızlı Kazanım"))
    .withColumn("description_en",
        concat_ws(" ",
            lit("Recalibrate setpoints, scheduling and control sequences to save ~"),
            col("_bms_saving_kwh").cast("string"),
            lit("kWh/year. Annual saving: €"),
            col("_bms_saving_eur").cast("string"),
            lit("| Payback:"),
            col("_bms_payback").cast("string"),
            lit("years. No major construction. Eligible for BAFA BEG NWG (DE).")))
    .withColumn("description_de",
        concat_ws(" ",
            lit("Sollwerte, Zeitpläne und Regelsequenzen anpassen — Einsparung ca."),
            col("_bms_saving_kwh").cast("string"),
            lit("kWh/Jahr. Jährliche Einsparung: €"),
            col("_bms_saving_eur").cast("string"),
            lit("| Amortisation:"),
            col("_bms_payback").cast("string"),
            lit("Jahre. Kein größerer Bauaufwand. BAFA BEG NWG förderfähig.")))
    .withColumn("description_tr",
        concat_ws(" ",
            lit("Setpoint, zamanlama ve kontrol mantığı optimize edilerek tahminen"),
            col("_bms_saving_kwh").cast("string"),
            lit("kWh/yıl tasarruf sağlanır. Yıllık tasarruf: €"),
            col("_bms_saving_eur").cast("string"),
            lit("| Geri ödeme:"),
            col("_bms_payback").cast("string"),
            lit("yıl. Büyük inşaat gerektirmez.")))
)


# ── 7h. HVAC_SCHEDULING ────────────────────────────────────────────────────────
# Applicable: All buildings EXCEPT HOSPITAL and DATA_CENTER (24/7 critical loads)
# Savings: 12% of HVAC portion of consumption (IEA benchmark for scheduling retrofit)
# Captures: night setback, weekend setback, pre-cooling/heating optimisation

HVAC_SHARE_BY_TYPE = {
    "OFFICE":     0.45, "RETAIL":   0.35, "LOGISTICS": 0.40,
    "HOTEL":      0.35, "SCHOOL":   0.50, "HEALTHCARE": 0.40,
    "EDUCATION":  0.50, "HOSPITAL": 0.40,
}

df_hvac_sched_rec = (
    df_base
    .filter(~col("building_type_upper").isin("HOSPITAL", "DATA_CENTER"))
    .withColumn("_hvac_share",
        when(col("building_type_upper") == "OFFICE",     lit(0.45))
        .when(col("building_type_upper") == "RETAIL",    lit(0.35))
        .when(col("building_type_upper") == "LOGISTICS", lit(0.40))
        .when(col("building_type_upper") == "HOTEL",     lit(0.35))
        .when(col("building_type_upper").isin("SCHOOL", "EDUCATION"), lit(0.50))
        .when(col("building_type_upper").isin("HEALTHCARE", "HOSPITAL"), lit(0.40))
        .otherwise(lit(0.40)))
    .withColumn("_rate", _elec_rate)
    .withColumn("_hvac_saving_kwh",
        spark_round(
            coalesce(col("annual_consumption_kwh"), lit(0.0))
            * col("_hvac_share") * lit(HVAC_SCHED_SAVING_PCT), 0))
    .withColumn("_hvac_saving_eur",
        spark_round(col("_hvac_saving_kwh") * col("_rate"), 0))
    .withColumn("_hvac_capex",
        spark_round(col("conditioned_area_m2") * lit(HVAC_SCHED_CAPEX_M2), 0))
    .withColumn("_hvac_co2",
        spark_round(col("_hvac_saving_kwh") * lit(0.4), 0))
    .withColumn("_hvac_payback",
        when(col("_hvac_saving_eur") > 0,
             spark_round(col("_hvac_capex") / col("_hvac_saving_eur"), 1))
        .otherwise(lit(99.0)))
    .withColumn("_hvac_npv",
        spark_round(col("_hvac_saving_eur") * lit(10.0) - col("_hvac_capex"), 0))
    .withColumn("action_type",       lit("HVAC_SCHEDULING"))
    .withColumn("compliance_driver", lit("EnEfG / EPBD — Operational Efficiency"))
    .withColumn("_comp_urg",
        compliance_urgency(coalesce(col("enefg_score"), col("epbd_score"), lit(45.0))))
    .withColumn("_fin",  financial_score(col("_hvac_npv"),       col("_hvac_capex")))
    .withColumn("_co2",  co2_score(col("_hvac_co2")))
    .withColumn("_pay",  payback_score(col("_hvac_payback")))
    .withColumn("priority_score",    total_priority(col("_comp_urg"), col("_fin"), col("_co2"), col("_pay")))
    .withColumn("annual_saving_eur", col("_hvac_saving_eur"))
    .withColumn("co2_saving_kg",     col("_hvac_co2"))
    .withColumn("capex_eur",         col("_hvac_capex"))
    .withColumn("net_capex_eur",
        when(col("country_code") == "DE",
             spark_round(col("_hvac_capex") * lit(0.75), 0))
        .otherwise(col("_hvac_capex")))
    .withColumn("payback_years",     col("_hvac_payback"))
    .withColumn("npv_eur",           col("_hvac_npv"))
    .withColumn("grant_eur",
        when(col("country_code") == "DE",
             spark_round(col("_hvac_capex") * lit(0.25), 0))
        .otherwise(lit(0.0)))
    .withColumn("grant_programs",
        when(col("country_code") == "DE", lit("BAFA BEG NWG"))
        .otherwise(lit(None).cast("string")))
    .withColumn("title_en", lit("Implement HVAC Scheduling & Setback"))
    .withColumn("title_de", lit("HLK-Zeitschaltung & Absenkbetrieb einrichten"))
    .withColumn("title_tr", lit("HVAC Zaman Programı ve Gece Modunu Devreye Al"))
    .withColumn("description_en",
        concat_ws(" ",
            lit("Implement time-based HVAC scheduling with night/weekend setback to save ~"),
            col("_hvac_saving_kwh").cast("string"),
            lit("kWh/year from HVAC alone. Annual saving: €"),
            col("_hvac_saving_eur").cast("string"),
            lit("| Payback:"),
            col("_hvac_payback").cast("string"),
            lit("years. Low-disruption, software-first approach.")))
    .withColumn("description_de",
        concat_ws(" ",
            lit("Zeitbasierte HLK-Steuerung mit Nacht- und Wochenendabsenkung — Einsparung ~"),
            col("_hvac_saving_kwh").cast("string"),
            lit("kWh/Jahr. Jährliche Einsparung: €"),
            col("_hvac_saving_eur").cast("string"),
            lit("| Amortisation:"),
            col("_hvac_payback").cast("string"),
            lit("Jahre. Softwarebasierter Ansatz, kein Bauaufwand.")))
    .withColumn("description_tr",
        concat_ws(" ",
            lit("Gece/hafta sonu HVAC setback ve zaman programlama ile HVAC tüketiminden ~"),
            col("_hvac_saving_kwh").cast("string"),
            lit("kWh/yıl tasarruf. Yıllık tasarruf: €"),
            col("_hvac_saving_eur").cast("string"),
            lit("| Geri ödeme:"),
            col("_hvac_payback").cast("string"),
            lit("yıl. Yazılım ağırlıklı, düşük kesinti.")))
)


# ── 7i. PEAK_DEMAND_MANAGEMENT ─────────────────────────────────────────────────
# Applicable: Buildings with battery storage OR EV charging OR LOGISTICS type
# Savings: 6% of annual electricity cost via demand charge reduction and load shifting
# Source: EPRI Demand Response potential study 2023

df_peak_rec = (
    df_base
    .filter(
        (col("has_battery") == True) |
        (col("has_ev_charging") == True) |
        (col("building_type_upper") == "LOGISTICS")
    )
    .withColumn("_rate", _elec_rate)
    .withColumn("_annual_cost_eur",
        spark_round(coalesce(col("annual_consumption_kwh"), lit(0.0)) * col("_rate"), 0))
    .withColumn("_peak_saving_eur",
        spark_round(col("_annual_cost_eur") * lit(PEAK_MGMT_SAVING_PCT), 0))
    .withColumn("_peak_saving_kwh",
        spark_round(coalesce(col("annual_consumption_kwh"), lit(0.0)) * lit(0.04), 0))
    .withColumn("_peak_capex",
        spark_round(
            lit(PEAK_MGMT_CAPEX_FIXED) + col("conditioned_area_m2") * lit(PEAK_MGMT_CAPEX_M2), 0))
    .withColumn("_peak_co2",
        spark_round(col("_peak_saving_kwh") * lit(0.4), 0))
    .withColumn("_peak_payback",
        when(col("_peak_saving_eur") > 0,
             spark_round(col("_peak_capex") / col("_peak_saving_eur"), 1))
        .otherwise(lit(99.0)))
    .withColumn("_peak_npv",
        spark_round(col("_peak_saving_eur") * lit(8.0) - col("_peak_capex"), 0))
    .withColumn("action_type",       lit("PEAK_DEMAND_MANAGEMENT"))
    .withColumn("compliance_driver", lit("EnEfG / Grid Tariff Optimisation"))
    .withColumn("_comp_urg",         lit(40.0))
    .withColumn("_fin",  financial_score(col("_peak_npv"),       col("_peak_capex")))
    .withColumn("_co2",  co2_score(col("_peak_co2")))
    .withColumn("_pay",  payback_score(col("_peak_payback")))
    .withColumn("priority_score",    total_priority(col("_comp_urg"), col("_fin"), col("_co2"), col("_pay")))
    .withColumn("annual_saving_eur", col("_peak_saving_eur"))
    .withColumn("co2_saving_kg",     col("_peak_co2"))
    .withColumn("capex_eur",         col("_peak_capex"))
    .withColumn("net_capex_eur",     col("_peak_capex"))
    .withColumn("payback_years",     col("_peak_payback"))
    .withColumn("npv_eur",           col("_peak_npv"))
    .withColumn("grant_eur",         lit(0.0))
    .withColumn("grant_programs",    lit(None).cast("string"))
    .withColumn("title_en", lit("Implement Peak Demand Management & Load Shifting"))
    .withColumn("title_de", lit("Lastspitzenmanagement & Lastverschiebung einführen"))
    .withColumn("title_tr", lit("Tepe Talep Yönetimi ve Yük Kaydırma Uygula"))
    .withColumn("description_en",
        concat_ws(" ",
            lit("Deploy demand response software to reduce peak demand charges. Annual saving: €"),
            col("_peak_saving_eur").cast("string"),
            lit("| Payback:"),
            col("_peak_payback").cast("string"),
            lit("years. Leverage existing battery / EV charging schedule for load shifting.")))
    .withColumn("description_de",
        concat_ws(" ",
            lit("Lastmanagement-Software zur Reduzierung von Lastspitzenkosten. Einsparung: €"),
            col("_peak_saving_eur").cast("string"),
            lit("| Amortisation:"),
            col("_peak_payback").cast("string"),
            lit("Jahre. Vorhandene Batterie/EV-Ladung für Lastverschiebung nutzen.")))
    .withColumn("description_tr",
        concat_ws(" ",
            lit("Tepe talep ücretlerini azaltmak için talep yönetimi yazılımı. Yıllık tasarruf: €"),
            col("_peak_saving_eur").cast("string"),
            lit("| Geri ödeme:"),
            col("_peak_payback").cast("string"),
            lit("yıl. Mevcut batarya/EV şarj altyapısını yük kaydırma için kullan.")))
)


# ── 7j. CHP_COGENERATION ──────────────────────────────────────────────────────
# Applicable: HOSPITAL and HOTEL (24/7 operation, high thermal load, gas supply)
# Logic: CHP generates electricity + recovers waste heat → replaces separate gas boiler + grid power
# Savings: 22% of annual energy cost (combined efficiency 85–90% vs separate ~55%)
# Capex: €800/kWe, CHP sized at 30% of estimated peak demand
# Source: ASUE Blockheizkraftwerke 2023, VDI 2067
# NOTE: has_gas_heating is not in silver_building_master — building type is sufficient proxy
#       (HOSPITAL/HOTEL/HEALTHCARE buildings are assumed to have thermal heating infrastructure)

df_chp_rec = (
    df_base
    .filter(
        col("building_type_upper").isin("HOSPITAL", "HOTEL", "HEALTHCARE")
    )
    .withColumn("_rate", _elec_rate)
    .withColumn("_annual_cost_eur",
        spark_round(coalesce(col("annual_consumption_kwh"), lit(0.0)) * col("_rate"), 0))
    .withColumn("_chp_saving_eur",
        spark_round(col("_annual_cost_eur") * lit(CHP_SAVING_PCT), 0))
    .withColumn("_chp_saving_kwh",
        spark_round(coalesce(col("annual_consumption_kwh"), lit(0.0)) * lit(0.15), 0))
    # CHP size: peak_kw estimate = annual_kwh / (8760 * load_factor 0.6) then take 30%
    .withColumn("_chp_kwe",
        spark_round(
            coalesce(col("annual_consumption_kwh"), lit(0.0))
            / lit(8760.0 * 0.60) * lit(CHP_PEAK_FRACTION), 1))
    .withColumn("_chp_capex",
        spark_round(col("_chp_kwe") * lit(CHP_CAPEX_PER_KWE), 0))
    .withColumn("_chp_co2",
        spark_round(col("_chp_saving_kwh") * lit(0.5), 0))
    .withColumn("_chp_payback",
        when(col("_chp_saving_eur") > 0,
             spark_round(col("_chp_capex") / col("_chp_saving_eur"), 1))
        .otherwise(lit(99.0)))
    .withColumn("_chp_npv",
        spark_round(col("_chp_saving_eur") * lit(12.0) - col("_chp_capex"), 0))
    .withColumn("action_type",       lit("CHP_COGENERATION"))
    .withColumn("compliance_driver", lit("EnEfG §12 / KWKG — CHP Promotion"))
    .withColumn("_comp_urg",
        compliance_urgency(coalesce(col("enefg_score"), lit(55.0))))
    .withColumn("_fin",  financial_score(col("_chp_npv"),       col("_chp_capex")))
    .withColumn("_co2",  co2_score(col("_chp_co2")))
    .withColumn("_pay",  payback_score(col("_chp_payback")))
    .withColumn("priority_score",    total_priority(col("_comp_urg"), col("_fin"), col("_co2"), col("_pay")))
    .withColumn("annual_saving_eur", col("_chp_saving_eur"))
    .withColumn("co2_saving_kg",     col("_chp_co2"))
    .withColumn("capex_eur",         col("_chp_capex"))
    .withColumn("net_capex_eur",
        when(col("country_code") == "DE",
             spark_round(col("_chp_capex") * lit(0.75), 0))
        .otherwise(col("_chp_capex")))
    .withColumn("payback_years",     col("_chp_payback"))
    .withColumn("npv_eur",           col("_chp_npv"))
    .withColumn("grant_eur",
        when(col("country_code") == "DE",
             spark_round(col("_chp_capex") * lit(0.25), 0))
        .otherwise(lit(0.0)))
    .withColumn("grant_programs",
        when(col("country_code") == "DE", lit("KWKG Zuschlag + BAFA KWK-Förderung"))
        .otherwise(lit(None).cast("string")))
    .withColumn("title_en",
        concat_ws(" ",
            lit("Install CHP Cogeneration Unit (~"),
            spark_round(col("_chp_kwe"), 0).cast("string"),
            lit("kWe) — Combined Heat & Power")))
    .withColumn("title_de",
        concat_ws(" ",
            lit("BHKW (Blockheizkraftwerk) installieren (~"),
            spark_round(col("_chp_kwe"), 0).cast("string"),
            lit("kWe) — Kraft-Wärme-Kopplung")))
    .withColumn("title_tr",
        concat_ws(" ",
            lit("Kojenerasyon Ünitesi Kur (~"),
            spark_round(col("_chp_kwe"), 0).cast("string"),
            lit("kWe) — Isı ve Güç Birlikte Üretimi")))
    .withColumn("description_en",
        concat_ws(" ",
            lit("A"),
            spark_round(col("_chp_kwe"), 0).cast("string"),
            lit("kWe CHP unit generates onsite electricity and recovers waste heat for heating/DHW."),
            lit("Annual saving: €"),
            col("_chp_saving_eur").cast("string"),
            lit("| Payback:"),
            col("_chp_payback").cast("string"),
            lit("years | KWKG feed-in tariff applicable (DE).")))
    .withColumn("description_de",
        concat_ws(" ",
            lit("Ein"),
            spark_round(col("_chp_kwe"), 0).cast("string"),
            lit("kWe BHKW erzeugt Strom vor Ort und nutzt Abwärme für Heizung/TWW."),
            lit("Jährliche Einsparung: €"),
            col("_chp_saving_eur").cast("string"),
            lit("| Amortisation:"),
            col("_chp_payback").cast("string"),
            lit("Jahre | KWKG-Zuschlag anwendbar.")))
    .withColumn("description_tr",
        concat_ws(" ",
            lit(""),
            spark_round(col("_chp_kwe"), 0).cast("string"),
            lit("kWe kojenerasyon ünitesi yerinde elektrik üretir ve atık ısıyı ısıtma/sıcak su için kullanır."),
            lit("Yıllık tasarruf: €"),
            col("_chp_saving_eur").cast("string"),
            lit("| Geri ödeme:"),
            col("_chp_payback").cast("string"),
            lit("yıl.")))
)


# ── 7k. SOLAR_THERMAL ──────────────────────────────────────────────────────────
# Applicable: HOTEL and HOSPITAL/HEALTHCARE — buildings with high domestic hot water (DHW) demand
# Savings: 50% of DHW energy portion covered by solar (Fraunhofer ISE: 40–65% typical)
# Hot water shares: HOTEL 25%, HOSPITAL/HEALTHCARE 10% of total consumption
# Capex: €450/m² collector (installed, incl. storage tank + installation)

df_solar_thermal_rec = (
    df_base
    .filter(col("building_type_upper").isin("HOTEL", "HOSPITAL", "HEALTHCARE"))
    .withColumn("_dhw_share",
        when(col("building_type_upper") == "HOTEL",                      lit(0.25))
        .when(col("building_type_upper").isin("HOSPITAL", "HEALTHCARE"),  lit(0.10))
        .otherwise(lit(0.10)))
    .withColumn("_rate", _elec_rate)
    .withColumn("_st_saving_kwh",
        spark_round(
            coalesce(col("annual_consumption_kwh"), lit(0.0))
            * col("_dhw_share") * lit(SOLAR_THERMAL_FRACTION), 0))
    .withColumn("_st_saving_eur",
        spark_round(col("_st_saving_kwh") * col("_rate"), 0))
    .withColumn("_st_area_m2",
        spark_round(col("conditioned_area_m2") * lit(SOLAR_THERMAL_M2_PER_M2_COND), 1))
    .withColumn("_st_capex",
        spark_round(col("_st_area_m2") * lit(SOLAR_THERMAL_CAPEX_M2), 0))
    .withColumn("_st_co2",
        spark_round(col("_st_saving_kwh") * lit(0.4), 0))
    .withColumn("_st_payback",
        when(col("_st_saving_eur") > 0,
             spark_round(col("_st_capex") / col("_st_saving_eur"), 1))
        .otherwise(lit(99.0)))
    .withColumn("_st_npv",
        spark_round(col("_st_saving_eur") * lit(20.0) - col("_st_capex"), 0))
    .withColumn("action_type",       lit("SOLAR_THERMAL"))
    .withColumn("compliance_driver", lit("EPBD nZEB / RED III — Renewable Heat"))
    .withColumn("_comp_urg",
        compliance_urgency(coalesce(col("epbd_score"), col("enefg_score"), lit(50.0))))
    .withColumn("_fin",  financial_score(col("_st_npv"),       col("_st_capex")))
    .withColumn("_co2",  co2_score(col("_st_co2")))
    .withColumn("_pay",  payback_score(col("_st_payback")))
    .withColumn("priority_score",    total_priority(col("_comp_urg"), col("_fin"), col("_co2"), col("_pay")))
    .withColumn("annual_saving_eur", col("_st_saving_eur"))
    .withColumn("co2_saving_kg",     col("_st_co2"))
    .withColumn("capex_eur",         col("_st_capex"))
    .withColumn("net_capex_eur",
        when(col("country_code") == "DE",
             spark_round(col("_st_capex") * lit(0.75), 0))
        .otherwise(col("_st_capex")))
    .withColumn("payback_years",     col("_st_payback"))
    .withColumn("npv_eur",           col("_st_npv"))
    .withColumn("grant_eur",
        when(col("country_code") == "DE",
             spark_round(col("_st_capex") * lit(0.25), 0))
        .otherwise(lit(0.0)))
    .withColumn("grant_programs",
        when(col("country_code") == "DE", lit("BAFA BEG NWG — Solarthermie"))
        .otherwise(lit(None).cast("string")))
    .withColumn("title_en",
        concat_ws(" ",
            lit("Install Solar Thermal System (~"),
            spark_round(col("_st_area_m2"), 0).cast("string"),
            lit("m²) — Domestic Hot Water")))
    .withColumn("title_de",
        concat_ws(" ",
            lit("Solarthermieanlage installieren (~"),
            spark_round(col("_st_area_m2"), 0).cast("string"),
            lit("m²) — Warmwasserbereitung")))
    .withColumn("title_tr",
        concat_ws(" ",
            lit("Güneş Termal Sistemi Kur (~"),
            spark_round(col("_st_area_m2"), 0).cast("string"),
            lit("m²) — Sıcak Su Üretimi")))
    .withColumn("description_en",
        concat_ws(" ",
            lit("A"),
            spark_round(col("_st_area_m2"), 0).cast("string"),
            lit("m² solar thermal array covers ~50% of DHW demand, saving ~"),
            col("_st_saving_kwh").cast("string"),
            lit("kWh/year. Annual saving: €"),
            col("_st_saving_eur").cast("string"),
            lit("| Payback:"),
            col("_st_payback").cast("string"),
            lit("years. 20-year system lifetime (Fraunhofer ISE benchmark).")))
    .withColumn("description_de",
        concat_ws(" ",
            lit("Eine"),
            spark_round(col("_st_area_m2"), 0).cast("string"),
            lit("m² Solarthermieanlage deckt ~50% des TWW-Bedarfs, Einsparung ~"),
            col("_st_saving_kwh").cast("string"),
            lit("kWh/Jahr. Jährliche Einsparung: €"),
            col("_st_saving_eur").cast("string"),
            lit("| Amortisation:"),
            col("_st_payback").cast("string"),
            lit("Jahre. Systemlebensdauer 20 Jahre.")))
    .withColumn("description_tr",
        concat_ws(" ",
            lit(""),
            spark_round(col("_st_area_m2"), 0).cast("string"),
            lit("m² güneş termal sistem sıcak su ihtiyacının ~%50'sini karşılar, tasarruf ~"),
            col("_st_saving_kwh").cast("string"),
            lit("kWh/yıl. Yıllık tasarruf: €"),
            col("_st_saving_eur").cast("string"),
            lit("| Geri ödeme:"),
            col("_st_payback").cast("string"),
            lit("yıl.")))
)


# ── 7l. HEAT_RECOVERY ──────────────────────────────────────────────────────────
# Applicable: LOGISTICS and HOSPITAL/HEALTHCARE
# Logic: High ventilation rates in these building types → HRV/ERV captures 70–85% of exhaust heat
# Savings: 15% of HVAC portion (EN 13053 Class H1 HRV efficiency)
# Capex: €22/m² conditioned area (ductwork modification + HRV units)

df_heat_recovery_rec = (
    df_base
    .filter(col("building_type_upper").isin("LOGISTICS", "HOSPITAL", "HEALTHCARE"))
    .withColumn("_hr_hvac_share",
        when(col("building_type_upper") == "LOGISTICS",              lit(0.40))
        .when(col("building_type_upper").isin("HOSPITAL","HEALTHCARE"), lit(0.40))
        .otherwise(lit(0.40)))
    .withColumn("_rate", _elec_rate)
    .withColumn("_hr_saving_kwh",
        spark_round(
            coalesce(col("annual_consumption_kwh"), lit(0.0))
            * col("_hr_hvac_share") * lit(HEAT_RECOVERY_SAVING_PCT), 0))
    .withColumn("_hr_saving_eur",
        spark_round(col("_hr_saving_kwh") * col("_rate"), 0))
    .withColumn("_hr_capex",
        spark_round(col("conditioned_area_m2") * lit(HEAT_RECOVERY_CAPEX_M2), 0))
    .withColumn("_hr_co2",
        spark_round(col("_hr_saving_kwh") * lit(0.4), 0))
    .withColumn("_hr_payback",
        when(col("_hr_saving_eur") > 0,
             spark_round(col("_hr_capex") / col("_hr_saving_eur"), 1))
        .otherwise(lit(99.0)))
    .withColumn("_hr_npv",
        spark_round(col("_hr_saving_eur") * lit(15.0) - col("_hr_capex"), 0))
    .withColumn("action_type",       lit("HEAT_RECOVERY"))
    .withColumn("compliance_driver", lit("EnEfG / EPBD — Ventilation Heat Recovery"))
    .withColumn("_comp_urg",
        compliance_urgency(coalesce(col("enefg_score"), lit(50.0))))
    .withColumn("_fin",  financial_score(col("_hr_npv"),       col("_hr_capex")))
    .withColumn("_co2",  co2_score(col("_hr_co2")))
    .withColumn("_pay",  payback_score(col("_hr_payback")))
    .withColumn("priority_score",    total_priority(col("_comp_urg"), col("_fin"), col("_co2"), col("_pay")))
    .withColumn("annual_saving_eur", col("_hr_saving_eur"))
    .withColumn("co2_saving_kg",     col("_hr_co2"))
    .withColumn("capex_eur",         col("_hr_capex"))
    .withColumn("net_capex_eur",
        when(col("country_code") == "DE",
             spark_round(col("_hr_capex") * lit(0.80), 0))
        .otherwise(col("_hr_capex")))
    .withColumn("payback_years",     col("_hr_payback"))
    .withColumn("npv_eur",           col("_hr_npv"))
    .withColumn("grant_eur",
        when(col("country_code") == "DE",
             spark_round(col("_hr_capex") * lit(0.20), 0))
        .otherwise(lit(0.0)))
    .withColumn("grant_programs",
        when(col("country_code") == "DE", lit("BAFA BEG NWG — Lüftungsanlage"))
        .otherwise(lit(None).cast("string")))
    .withColumn("title_en", lit("Install Ventilation Heat Recovery (HRV/ERV)"))
    .withColumn("title_de", lit("Wärmerückgewinnung in der Lüftungsanlage nachrüsten (WRG)"))
    .withColumn("title_tr", lit("Havalandırma Isı Geri Kazanımı Sistemi Kur (HRV/ERV)"))
    .withColumn("description_en",
        concat_ws(" ",
            lit("Heat Recovery Ventilation (HRV) captures 70–85% of exhaust heat (EN 13053 Class H1)."),
            lit("Annual saving: ~"),
            col("_hr_saving_kwh").cast("string"),
            lit("kWh | €"),
            col("_hr_saving_eur").cast("string"),
            lit("| Payback:"),
            col("_hr_payback").cast("string"),
            lit("years. Especially effective in high-ventilation buildings (logistics, healthcare).")))
    .withColumn("description_de",
        concat_ws(" ",
            lit("Wärmerückgewinnung (WRG) erfasst 70–85% der Abluftenergie (EN 13053 Klasse H1)."),
            lit("Jährliche Einsparung: ~"),
            col("_hr_saving_kwh").cast("string"),
            lit("kWh | €"),
            col("_hr_saving_eur").cast("string"),
            lit("| Amortisation:"),
            col("_hr_payback").cast("string"),
            lit("Jahre.")))
    .withColumn("description_tr",
        concat_ws(" ",
            lit("HRV egzoz havasının %70–85'ini geri kazanır (EN 13053 Sınıf H1)."),
            lit("Yıllık tasarruf: ~"),
            col("_hr_saving_kwh").cast("string"),
            lit("kWh | €"),
            col("_hr_saving_eur").cast("string"),
            lit("| Geri ödeme:"),
            col("_hr_payback").cast("string"),
            lit("yıl.")))
)


# ── 7m. BATTERY_EXPANSION ─────────────────────────────────────────────────────
# Applicable: Buildings that already have a battery (has_battery=True)
# Logic: Expand existing battery by 50% to increase self-consumption window and peak shaving capacity
# Savings: 6% of annual electricity cost (marginal gain from expanded storage)
# Capex: €550/kWh additional capacity (LFP commercial 2024, Fraunhofer ISE)

df_bat_exp_rec = (
    df_base
    .filter(
        (col("has_battery") == True) &
        col("battery_capacity_kwh").isNotNull() &
        (col("battery_capacity_kwh") > 0)
    )
    .withColumn("_rate", _elec_rate)
    .withColumn("_annual_cost_eur",
        spark_round(coalesce(col("annual_consumption_kwh"), lit(0.0)) * col("_rate"), 0))
    .withColumn("_batexp_saving_eur",
        spark_round(col("_annual_cost_eur") * lit(BAT_EXP_SAVING_PCT), 0))
    .withColumn("_batexp_saving_kwh",
        spark_round(coalesce(col("annual_consumption_kwh"), lit(0.0)) * lit(0.04), 0))
    .withColumn("_batexp_kwh_add",
        spark_round(col("battery_capacity_kwh") * lit(BAT_EXP_FRACTION), 0))
    .withColumn("_batexp_capex",
        spark_round(col("_batexp_kwh_add") * lit(BAT_EXP_CAPEX_PER_KWH), 0))
    .withColumn("_batexp_co2",
        spark_round(col("_batexp_saving_kwh") * lit(0.4), 0))
    .withColumn("_batexp_payback",
        when(col("_batexp_saving_eur") > 0,
             spark_round(col("_batexp_capex") / col("_batexp_saving_eur"), 1))
        .otherwise(lit(99.0)))
    .withColumn("_batexp_npv",
        spark_round(col("_batexp_saving_eur") * lit(12.0) - col("_batexp_capex"), 0))
    .withColumn("action_type",       lit("BATTERY_EXPANSION"))
    .withColumn("compliance_driver", lit("EPBD / EED — Storage Flexibility"))
    .withColumn("_comp_urg",         lit(35.0))
    .withColumn("_fin",  financial_score(col("_batexp_npv"),     col("_batexp_capex")))
    .withColumn("_co2",  co2_score(col("_batexp_co2")))
    .withColumn("_pay",  payback_score(col("_batexp_payback")))
    .withColumn("priority_score",    total_priority(col("_comp_urg"), col("_fin"), col("_co2"), col("_pay")))
    .withColumn("annual_saving_eur", col("_batexp_saving_eur"))
    .withColumn("co2_saving_kg",     col("_batexp_co2"))
    .withColumn("capex_eur",         col("_batexp_capex"))
    .withColumn("net_capex_eur",
        when(col("country_code") == "DE",
             spark_round(col("_batexp_capex") * lit(0.80), 0))
        .otherwise(col("_batexp_capex")))
    .withColumn("payback_years",     col("_batexp_payback"))
    .withColumn("npv_eur",           col("_batexp_npv"))
    .withColumn("grant_eur",
        when(col("country_code") == "DE",
             spark_round(col("_batexp_capex") * lit(0.20), 0))
        .otherwise(lit(0.0)))
    .withColumn("grant_programs",
        when(col("country_code") == "DE", lit("KfW 270 — Erneuerbare Energien Speicher"))
        .otherwise(lit(None).cast("string")))
    .withColumn("title_en",
        concat_ws(" ",
            lit("Expand Battery Storage Capacity (+"),
            col("_batexp_kwh_add").cast("string"),
            lit("kWh — 50% increase)")))
    .withColumn("title_de",
        concat_ws(" ",
            lit("Batteriespeicher erweitern (+"),
            col("_batexp_kwh_add").cast("string"),
            lit("kWh — +50%)")))
    .withColumn("title_tr",
        concat_ws(" ",
            lit("Batarya Kapasitesini Genişlet (+"),
            col("_batexp_kwh_add").cast("string"),
            lit("kWh — %50 artış)")))
    .withColumn("description_en",
        concat_ws(" ",
            lit("Add"),
            col("_batexp_kwh_add").cast("string"),
            lit("kWh to existing battery system, increasing self-consumption window and peak shaving range."),
            lit("Annual saving: €"),
            col("_batexp_saving_eur").cast("string"),
            lit("| Payback:"),
            col("_batexp_payback").cast("string"),
            lit("years.")))
    .withColumn("description_de",
        concat_ws(" ",
            lit(""),
            col("_batexp_kwh_add").cast("string"),
            lit("kWh zum bestehenden Batteriesystem hinzufügen — mehr Eigenverbrauch und Lastspitzenkappung."),
            lit("Jährliche Einsparung: €"),
            col("_batexp_saving_eur").cast("string"),
            lit("| Amortisation:"),
            col("_batexp_payback").cast("string"),
            lit("Jahre.")))
    .withColumn("description_tr",
        concat_ws(" ",
            lit("Mevcut batarya sistemine"),
            col("_batexp_kwh_add").cast("string"),
            lit("kWh ekleyerek öz-tüketim penceresini ve tepe kesme kapasitesini artır."),
            lit("Yıllık tasarruf: €"),
            col("_batexp_saving_eur").cast("string"),
            lit("| Geri ödeme:"),
            col("_batexp_payback").cast("string"),
            lit("yıl.")))
)


# ── 7n. POWER_FACTOR_CORRECTION ────────────────────────────────────────────────
# Applicable: LOGISTICS, HOSPITAL, HOTEL — high inductive motor loads (compressors, fans, pumps)
# Savings: 4% of annual electricity cost (reactive power tariff penalties eliminated)
# Capex: Flat €15,000 for capacitor bank + controller (commercial scale)
# Source: VDE / DENA Reaktivleistungsmanagement Leitfaden 2022

df_pfc_rec = (
    df_base
    .filter(col("building_type_upper").isin("LOGISTICS", "HOSPITAL", "HEALTHCARE", "HOTEL"))
    .withColumn("_rate", _elec_rate)
    .withColumn("_annual_cost_eur",
        spark_round(coalesce(col("annual_consumption_kwh"), lit(0.0)) * col("_rate"), 0))
    .withColumn("_pfc_saving_eur",
        spark_round(col("_annual_cost_eur") * lit(PFC_SAVING_PCT), 0))
    .withColumn("_pfc_saving_kwh",  lit(0.0))  # PFC reduces bill cost, not kWh directly
    .withColumn("_pfc_capex",       lit(PFC_CAPEX_FIXED))
    .withColumn("_pfc_co2",         lit(0.0))   # Minimal direct CO2 impact
    .withColumn("_pfc_payback",
        when(col("_pfc_saving_eur") > 0,
             spark_round(lit(PFC_CAPEX_FIXED) / col("_pfc_saving_eur"), 1))
        .otherwise(lit(99.0)))
    .withColumn("_pfc_npv",
        spark_round(col("_pfc_saving_eur") * lit(10.0) - lit(PFC_CAPEX_FIXED), 0))
    .withColumn("action_type",       lit("POWER_FACTOR_CORRECTION"))
    .withColumn("compliance_driver", lit("Grid Tariff / VDE-AR-N 4100 — Power Quality"))
    .withColumn("_comp_urg",         lit(30.0))
    .withColumn("_fin",  financial_score(col("_pfc_npv"),       col("_pfc_capex")))
    .withColumn("_co2",  co2_score(col("_pfc_co2")))
    .withColumn("_pay",  payback_score(col("_pfc_payback")))
    .withColumn("priority_score",    total_priority(col("_comp_urg"), col("_fin"), col("_co2"), col("_pay")))
    .withColumn("annual_saving_eur", col("_pfc_saving_eur"))
    .withColumn("co2_saving_kg",     col("_pfc_co2"))
    .withColumn("capex_eur",         col("_pfc_capex"))
    .withColumn("net_capex_eur",     col("_pfc_capex"))
    .withColumn("payback_years",     col("_pfc_payback"))
    .withColumn("npv_eur",           col("_pfc_npv"))
    .withColumn("grant_eur",         lit(0.0))
    .withColumn("grant_programs",    lit(None).cast("string"))
    .withColumn("title_en", lit("Install Power Factor Correction (Capacitor Bank)"))
    .withColumn("title_de", lit("Blindleistungskompensation installieren (Kondensatorbatterie)"))
    .withColumn("title_tr", lit("Güç Faktörü Düzeltme Sistemi Kur (Kondansatör Bataryası)"))
    .withColumn("description_en",
        concat_ws(" ",
            lit("Install a reactive power compensation unit to eliminate power factor penalties."),
            lit("Annual saving: €"),
            col("_pfc_saving_eur").cast("string"),
            lit("| Payback:"),
            col("_pfc_payback").cast("string"),
            lit("years. Flat capex ~€15,000 for capacitor bank + controller. Fast ROI.")))
    .withColumn("description_de",
        concat_ws(" ",
            lit("Blindleistungskompensationsanlage installieren, um Blindleistungskosten zu eliminieren."),
            lit("Jährliche Einsparung: €"),
            col("_pfc_saving_eur").cast("string"),
            lit("| Amortisation:"),
            col("_pfc_payback").cast("string"),
            lit("Jahre. Pauschalkosten ~15.000 € für Kondensatorbatterie + Regler.")))
    .withColumn("description_tr",
        concat_ws(" ",
            lit("Reaktif güç cezalarını ortadan kaldırmak için güç faktörü düzeltme ünitesi kur."),
            lit("Yıllık tasarruf: €"),
            col("_pfc_saving_eur").cast("string"),
            lit("| Geri ödeme:"),
            col("_pfc_payback").cast("string"),
            lit("yıl. Sabit maliyet ~15.000 € kondansatör bataryası + kontrol.")))
)


# ── 7o. SUBMETERING_UPGRADE ────────────────────────────────────────────────────
# Applicable: Buildings without ISO 50001 certification (no systematic energy monitoring)
# Savings: 5% of total consumption (waste identification → corrective action)
# Capex: €6/m² + €4,000 fixed (smart meters per zone + gateway + monitoring software)
# Source: Carbon Trust Sub-metering guide, CIBSE TM39

df_submeter_rec = (
    df_base
    .filter(col("iso50001_certified") == False)
    .withColumn("_rate", _elec_rate)
    .withColumn("_sm_saving_kwh",
        spark_round(coalesce(col("annual_consumption_kwh"), lit(0.0)) * lit(SUBMETER_SAVING_PCT), 0))
    .withColumn("_sm_saving_eur",
        spark_round(col("_sm_saving_kwh") * col("_rate"), 0))
    .withColumn("_sm_capex",
        spark_round(
            lit(SUBMETER_CAPEX_FIXED) + col("conditioned_area_m2") * lit(SUBMETER_CAPEX_M2), 0))
    .withColumn("_sm_co2",
        spark_round(col("_sm_saving_kwh") * lit(0.4), 0))
    .withColumn("_sm_payback",
        when(col("_sm_saving_eur") > 0,
             spark_round(col("_sm_capex") / col("_sm_saving_eur"), 1))
        .otherwise(lit(99.0)))
    .withColumn("_sm_npv",
        spark_round(col("_sm_saving_eur") * lit(8.0) - col("_sm_capex"), 0))
    .withColumn("action_type",       lit("SUBMETERING_UPGRADE"))
    .withColumn("compliance_driver", lit("EnEfG §3 / EPBD — Energy Monitoring"))
    .withColumn("_comp_urg",
        compliance_urgency(coalesce(col("enefg_score"), col("epbd_score"), lit(45.0))))
    .withColumn("_fin",  financial_score(col("_sm_npv"),       col("_sm_capex")))
    .withColumn("_co2",  co2_score(col("_sm_co2")))
    .withColumn("_pay",  payback_score(col("_sm_payback")))
    .withColumn("priority_score",    total_priority(col("_comp_urg"), col("_fin"), col("_co2"), col("_pay")))
    .withColumn("annual_saving_eur", col("_sm_saving_eur"))
    .withColumn("co2_saving_kg",     col("_sm_co2"))
    .withColumn("capex_eur",         col("_sm_capex"))
    .withColumn("net_capex_eur",     col("_sm_capex"))
    .withColumn("payback_years",     col("_sm_payback"))
    .withColumn("npv_eur",           col("_sm_npv"))
    .withColumn("grant_eur",         lit(0.0))
    .withColumn("grant_programs",    lit(None).cast("string"))
    .withColumn("title_en", lit("Install Sub-metering for Zone-Level Energy Monitoring"))
    .withColumn("title_de", lit("Unterzähler für zonenbasiertes Energiemonitoring installieren"))
    .withColumn("title_tr", lit("Bölge Bazlı Enerji İzleme için Alt Sayaç Sistemi Kur"))
    .withColumn("description_en",
        concat_ws(" ",
            lit("Deploy zone/floor-level smart meters to identify waste and enable targeted action."),
            lit("Typical saving: 5% of total consumption ="),
            col("_sm_saving_kwh").cast("string"),
            lit("kWh | €"),
            col("_sm_saving_eur").cast("string"),
            lit("/year | Payback:"),
            col("_sm_payback").cast("string"),
            lit("years. Foundation for ISO 50001 compliance.")))
    .withColumn("description_de",
        concat_ws(" ",
            lit("Zonen-/Etagen-Unterzähler identifizieren Verschwendung und ermöglichen gezielte Maßnahmen."),
            lit("Typische Einsparung: 5% ="),
            col("_sm_saving_kwh").cast("string"),
            lit("kWh | €"),
            col("_sm_saving_eur").cast("string"),
            lit("/Jahr | Amortisation:"),
            col("_sm_payback").cast("string"),
            lit("Jahre. Grundlage für ISO 50001.")))
    .withColumn("description_tr",
        concat_ws(" ",
            lit("Bölge/kat bazlı akıllı sayaçlar enerji israfını tespit eder."),
            lit("Tipik tasarruf: %5 ="),
            col("_sm_saving_kwh").cast("string"),
            lit("kWh | €"),
            col("_sm_saving_eur").cast("string"),
            lit("/yıl | Geri ödeme:"),
            col("_sm_payback").cast("string"),
            lit("yıl. ISO 50001 uyumu için temel.")))
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

all_recs = [
    # Layer 0 — Original capital investment actions
    df_hp_rec, df_ins_rec, df_bat_rec, df_solar_rec,
    df_audit_rec, df_led_rec, df_deep_rec,
    # Layer 1 — Universal operational quick wins
    df_bms_rec, df_hvac_sched_rec, df_submeter_rec,
    # Layer 2 — Sector-specific technologies
    df_chp_rec, df_solar_thermal_rec, df_heat_recovery_rec,
    # Layer 3 — Advanced / asset-specific
    df_bat_exp_rec, df_peak_rec, df_pfc_rec,
]

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
    # Keep top 10 recommendations per building (expanded action type set — v2)
    .filter(col("rank") <= 10)
)

log_step("RANK", "Ranking complete", rows=df_ranked.count())


# ── 10. FINAL SELECT ───────────────────────────────────────────────────────────

df_results = (
    df_ranked
    # priority_sort_order: numeric sort key for Power BI visuals
    # Live Connection = no calculated columns in PBI → sort must come from the table
    # Used by: V12 "Actions by Priority" Y-axis sort (set Sort by Column in PBI)
    .withColumn("priority_sort_order",
        when(col("priority_label") == "CRITICAL",      lit(1))
        .when(col("priority_label") == "HIGH",          lit(2))
        .when(col("priority_label") == "MEDIUM",        lit(3))
        .when(col("priority_label") == "LOW",           lit(4))
        .when(col("priority_label") == "INFORMATIONAL", lit(5))
        .otherwise(lit(99)))
    .select(
        col("building_id"),
        col("building_name"),
        col("country_code"),
        col("building_type"),
        col("subscription_tier"),
        col("rank"),
        col("action_type"),
        col("priority_label"),
        col("priority_sort_order"),                          # ← NEW: PBI sort key
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
df_val.filter(col("priority_label").isin(["CRITICAL", "HIGH"])).select(
    "building_id", "country_code", "rank",
    "action_type", "priority_label", "priority_score",
    "annual_saving_eur", "net_capex_eur", "payback_years",
    "compliance_driver",
).orderBy(col("priority_score").desc()).show(50, truncate=False)

print()
print("── RECOMMENDATION COUNT BY BUILDING ─────────────────────────────────────")
df_val.groupBy("building_id", "country_code").count().orderBy("building_id").show()

print()
print("── PRIORITY DISTRIBUTION ────────────────────────────────────────────────")
df_val.groupBy("priority_label").count().orderBy("priority_label").show()

print()
print("=" * 72)
print("  RECOMMENDATION ENGINE COMPLETE")
print("=" * 72)
