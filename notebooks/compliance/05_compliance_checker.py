# ============================================================
# Energy Copilot Platform – Compliance Checker
# Notebook : 05_compliance_checker.py
# Layer    : Gold (Compliance Results)
# Author   : Energy Copilot Team
# Updated  : 2026-04-08
# ============================================================
#
# PURPOSE
# -------
# Score-based regulatory compliance assessment for each building.
# Two output tables:
#   gold_compliance_results  — wide format, one row per building,
#                              one score per regulation + overall score
#   gold_compliance_issues   — long format, one row per rule violation,
#                              used for Power BI drill-down and alerts
#
# REGULATIONS COVERED
# -------------------
#   Germany (DE):
#     EnEfG  Energieeffizienzgesetz 2023      energy intensity & audit
#     GEG    Gebäudeenergiegesetz 2024        heating system + U-values
#     EEG    Erneuerbare-Energien-Gesetz 2023 solar self-consumption
#   European Union (all buildings):
#     EPBD   Energy Performance of Buildings Directive  nZEB gap
#     CSRD   Corporate Sustainability Reporting Directive  carbon
#   Turkey (TR):
#     BEP-TR Binalarda Enerji Performansı     energy class A–G
#
# SCORING SYSTEM
# --------------
#   Each regulation → 0–100 score (higher = more compliant)
#   Status thresholds:
#     EXCELLENT     ≥ 85
#     GOOD          70 – 84
#     PARTIAL       50 – 69
#     AT_RISK       30 – 49
#     NON_COMPLIANT  < 30
#   Overall score = weighted average (weights differ by country)
#     DE weights: EnEfG 25% | GEG 30% | EEG 15% | EPBD 20% | CSRD 10%
#     TR weights: BEP-TR 40% | EPBD 35% | CSRD 25%
#
# INPUT TABLES
# ------------
#   silver_building_master         actual U-values, year_built, tech flags
#   gold_kpi_monthly               annual EUI + carbon intensity aggregates
#   gold_simulation_results        GEG insulation compliance flag
#   ref_building_type_profiles     EUI benchmarks + nZEB targets per type
#   ref_simulation_inputs          heating_fuel_type per building
#
# OUTPUT TABLES
# -------------
#   gold_compliance_results        wide  — one row per building
#   gold_compliance_issues         long  — one row per rule check
#
# BMAD PHASE  : L4 (regulatory rules expressed as score functions)
# DP-600 HINTS: broadcast all reference tables, Delta MERGE upsert,
#               autoMerge enabled, AQE on
# ============================================================


# ── 0. IMPORTS & SPARK CONFIG ─────────────────────────────────────────────────

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, lit, when, coalesce, broadcast,
    sum as spark_sum, avg as spark_avg,
    max as spark_max, min as spark_min,
    round as spark_round, greatest, least,
    current_timestamp, concat_ws, count,
)
from pyspark.sql.types import (
    StructType, StructField,
    StringType, DoubleType, BooleanType, TimestampType,
)
from delta.tables import DeltaTable

spark = SparkSession.builder.getOrCreate()
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.databricks.delta.schema.autoMerge.enabled", "true")


def log_step(step: str, msg: str = "", rows: int = -1):
    row_str = f"  [{rows:,} rows]" if rows >= 0 else ""
    print(f"[05_COMP] {step:40s}{row_str}  {msg}")


# ── 1. TABLE PATHS ─────────────────────────────────────────────────────────────

SILVER_PATHS = {
    "building_master": "Tables/silver_building_master",
}
REF_PATHS = {
    "building_type_profiles": "Tables/ref_building_type_profiles",
    "simulation_inputs":      "Tables/ref_simulation_inputs",
}
GOLD_PATHS = {
    "kpi_monthly":          "Tables/gold_kpi_monthly",
    "simulation_results":   "Tables/gold_simulation_results",
    "compliance_results":   "Tables/gold_compliance_results",
    "compliance_issues":    "Tables/gold_compliance_issues",
}


# ── 2. REGULATORY THRESHOLDS (constants) ──────────────────────────────────────

# ── EnEfG (Germany) ───────────────────────────────────────────────────────────
# Energieeffizienzgesetz 2023: large energy consumers must reduce by 2% p.a.
# Audit threshold: buildings consuming > 500 MWh/year must have energy audit
ENEFG_LARGE_CONSUMER_MWH   = 500.0   # annual threshold for mandatory audit
ENEFG_REDUCTION_TARGET_PCT = 0.02    # 2 % per annum mandatory reduction

# ── GEG (Germany) ─────────────────────────────────────────────────────────────
# Gebäudeenergiegesetz 2024 (GEG §10, Anlage 1):
# Maximum allowable U-values for thermal renovations (W/m²K)
GEG_WALL_U_MAX   = 0.24   # exterior wall
GEG_ROOF_U_MAX   = 0.20   # roof / top ceiling
GEG_WINDOW_U_MAX = 1.30   # windows + doors
# GEG §71: from 2024, new heating systems must use ≥ 65% renewable energy
GEG_RENEWABLE_HEATING_SYSTEMS = ("HEAT_PUMP", "DISTRICT_HEAT", "BIOMASS", "SOLAR_THERMAL")

# ── EEG (Germany) ─────────────────────────────────────────────────────────────
# Erneuerbare-Energien-Gesetz 2023: self-consumption targets
EEG_SELF_CONSUMPTION_TARGET_PCT = 0.30   # 30 % self-consumption is "good"
EEG_SELF_CONSUMPTION_EXCELLENT  = 0.50   # 50 % is excellent

# ── EPBD (EU) ─────────────────────────────────────────────────────────────────
# Energy Performance of Buildings Directive — 2030 renovation wave targets
# All buildings must reach at least EPC class E by 2030, D by 2033
# nZEB (nearly Zero Energy Building) target: EUI ≤ 50 kWh/m²/year
EPBD_NZEB_EUI_TARGET     = 50.0    # kWh/m²/year — aspirational 2050 target
EPBD_CLASS_D_EUI_TARGET  = 150.0   # kWh/m²/year — 2033 mandatory minimum
EPBD_CLASS_E_EUI_TARGET  = 200.0   # kWh/m²/year — 2030 mandatory minimum

# ── CSRD (EU) ─────────────────────────────────────────────────────────────────
# Corporate Sustainability Reporting Directive — Scope 2 carbon intensity
# EU taxonomy: < 10 kgCO₂/m²/year is "sustainable" for office buildings
CSRD_EXCELLENT_KG_M2  = 10.0    # kg CO₂/m²/year
CSRD_GOOD_KG_M2       = 20.0
CSRD_PARTIAL_KG_M2    = 40.0
CSRD_AT_RISK_KG_M2    = 60.0

# ── BEP-TR (Turkey) ───────────────────────────────────────────────────────────
# Binalarda Enerji Performansı Yönetmeliği — energy class EUI thresholds
# Class boundaries (kWh/m²/year) for commercial buildings (TS 825 based)
BEPTR_CLASS_A_MAX = 75.0
BEPTR_CLASS_B_MAX = 100.0
BEPTR_CLASS_C_MAX = 125.0
BEPTR_CLASS_D_MAX = 150.0
BEPTR_CLASS_E_MAX = 175.0
BEPTR_CLASS_F_MAX = 200.0
# G: > 200

# ── Overall score weights by country ──────────────────────────────────────────
# These sum to 1.0 per country group
DE_WEIGHTS = {
    "enefg": 0.25,
    "geg":   0.30,
    "eeg":   0.15,
    "epbd":  0.20,
    "csrd":  0.10,
}
TR_WEIGHTS = {
    "beptr": 0.40,
    "epbd":  0.35,
    "csrd":  0.25,
}

# Status label thresholds
STATUS_EXCELLENT     = 85.0
STATUS_GOOD          = 70.0
STATUS_PARTIAL       = 50.0
STATUS_AT_RISK       = 30.0


# ── 3. HELPER: score → status label ────────────────────────────────────────────

def score_to_status(score_col):
    """Convert a numeric score column (0-100) to a status string column."""
    return (
        when(score_col >= STATUS_EXCELLENT, lit("EXCELLENT"))
        .when(score_col >= STATUS_GOOD,     lit("GOOD"))
        .when(score_col >= STATUS_PARTIAL,  lit("PARTIAL"))
        .when(score_col >= STATUS_AT_RISK,  lit("AT_RISK"))
        .otherwise(lit("NON_COMPLIANT"))
    )


# ── 4. READ INPUT TABLES ───────────────────────────────────────────────────────

log_step("READ", "Loading input tables …")

df_building   = spark.read.format("delta").load(SILVER_PATHS["building_master"])
df_kpi_m      = spark.read.format("delta").load(GOLD_PATHS["kpi_monthly"])
df_sim_res    = spark.read.format("delta").load(GOLD_PATHS["simulation_results"])
df_profiles   = spark.read.format("delta").load(REF_PATHS["building_type_profiles"])
df_sim_inp    = spark.read.format("delta").load(REF_PATHS["simulation_inputs"])

log_step("READ", "All tables loaded", rows=df_building.count())


# ── 5. DERIVE ANNUAL KPI AGGREGATES ───────────────────────────────────────────
# gold_kpi_monthly is monthly — we need full-year totals per building
# Use the most recent 12 months of available data

log_step("AGG", "Computing annual KPI aggregates from gold_kpi_monthly …")

df_annual = (
    df_kpi_m
    .groupBy("building_id")
    .agg(
        spark_sum("total_consumption_kwh").alias("annual_consumption_kwh"),
        spark_sum("solar_generated_kwh").alias("annual_solar_kwh"),
        spark_sum("solar_self_consumed_kwh").alias("annual_self_consumed_kwh"),
        spark_sum("co2_emissions_kg").alias("annual_co2_kg"),
        spark_sum("co2_savings_from_solar_kg").alias("annual_co2_savings_kg"),
        spark_max("floor_area_m2").alias("floor_area_m2"),
        spark_avg("carbon_intensity_kg_m2").alias("avg_carbon_intensity_kg_m2"),
        count("month").alias("months_of_data"),
    )
    # Annual EUI (kWh/m²/year)
    .withColumn(
        "annual_eui_kwh_m2",
        when(col("floor_area_m2") > 0,
             spark_round(col("annual_consumption_kwh") / col("floor_area_m2"), 1))
        .otherwise(lit(None))
    )
    # Annual solar self-consumption rate (%)
    .withColumn(
        "solar_self_consumption_rate",
        when(col("annual_solar_kwh") > 0,
             spark_round(col("annual_self_consumed_kwh") / col("annual_solar_kwh"), 3))
        .otherwise(lit(0.0))
    )
    # Annual carbon intensity (kg CO₂/m²/year) — annualise from monthly avg
    .withColumn(
        "annual_carbon_intensity_kg_m2",
        spark_round(col("avg_carbon_intensity_kg_m2") * 12.0, 2)
    )
)

log_step("AGG", "Annual KPIs derived", rows=df_annual.count())


# ── 6. BASE JOIN ───────────────────────────────────────────────────────────────
# Combine building attributes with annual KPIs, simulation results,
# building type benchmarks and simulation inputs (for heating_fuel_type)

log_step("JOIN", "Joining all input sources …")

df_profiles_bc = broadcast(df_profiles)
df_sim_inp_bc  = broadcast(df_sim_inp)

# Narrow down simulation results to compliance-relevant columns only
df_sim_narrow = df_sim_res.select(
    "building_id",
    "ins_geg_compliant",
    "hp_is_feasible",
    "ins_is_feasible",
)

df_base = (
    df_building.alias("b")
    .join(df_annual.alias("k"),       on="building_id", how="left")
    .join(df_sim_narrow.alias("sr"),  on="building_id", how="left")
    .join(
        df_sim_inp_bc.alias("si"),
        on="building_id",
        how="left",
    )
    .join(
        df_profiles_bc.alias("p"),
        on=col("b.building_type") == col("p.building_type"),
        how="left",
    )
    .select(
        # Identifiers
        col("b.building_id"),
        col("b.building_name"),
        col("b.building_type"),
        col("b.country_code"),
        col("b.city"),
        col("b.year_built"),
        col("b.conditioned_area_m2"),
        col("b.subscription_tier"),
        # Technology flags
        col("b.has_pv"),
        col("b.has_battery"),
        col("b.has_heat_pump"),
        col("b.has_led_lighting"),
        # Building envelope (actual measured U-values from silver)
        col("b.wall_u_value"),
        col("b.roof_u_value"),
        col("b.window_u_value"),
        col("b.insulation_year"),
        col("b.energy_certificate"),
        col("b.energy_certificate_year"),
        # Annual KPIs
        col("k.annual_consumption_kwh"),
        col("k.annual_eui_kwh_m2"),
        col("k.solar_self_consumption_rate"),
        col("k.annual_co2_kg"),
        col("k.annual_carbon_intensity_kg_m2"),
        col("k.months_of_data"),
        # EUI benchmarks (from building type profile)
        col("p.eui_good_kwh_m2"),
        col("p.eui_average_kwh_m2"),
        col("p.eui_poor_kwh_m2"),
        col("p.eui_nzeb_target_kwh_m2"),
        # Heating fuel (from simulation inputs)
        col("si.heating_fuel_type"),
        # Simulation compliance flags
        col("sr.ins_geg_compliant"),
        col("sr.hp_is_feasible"),
        col("sr.ins_is_feasible"),
    )
)

log_step("JOIN", "Base join complete", rows=df_base.count())


# ── 7. ENEFG SCORE (Germany only) ─────────────────────────────────────────────
# Energieeffizienzgesetz 2023:
#   - Large consumers (>500 MWh/year) must conduct energy audit
#   - All non-SME commercial buildings must reduce consumption 2%/year
#
# Score components:
#   60 pts: EUI vs. building type benchmark
#   25 pts: large consumer audit compliance (audit required if > 500 MWh)
#   15 pts: energy intensity trend (year_built proxy — older = higher risk)

log_step("SCORE", "Computing EnEfG score …")

# EUI component: 0–60 pts
# 60 if EUI ≤ good_benchmark, 0 if EUI ≥ poor_benchmark, linear in between
enefg_eui_score = (
    when(col("annual_eui_kwh_m2").isNull(), lit(30.0))   # no data → neutral
    .when(col("annual_eui_kwh_m2") <= col("eui_good_kwh_m2"),
          lit(60.0))
    .when(col("annual_eui_kwh_m2") >= col("eui_poor_kwh_m2"),
          lit(0.0))
    .otherwise(
        spark_round(
            60.0 * (col("eui_poor_kwh_m2") - col("annual_eui_kwh_m2"))
            / (col("eui_poor_kwh_m2") - col("eui_good_kwh_m2")), 1
        )
    )
)

# Audit compliance component: 0–25 pts
# Large consumer = annual consumption > 500 MWh
# If large consumer and has energy certificate → 25, else → 0
# If not large consumer → full 25 (not required)
enefg_audit_score = (
    when(
        (col("annual_consumption_kwh") / 1000.0) <= ENEFG_LARGE_CONSUMER_MWH,
        lit(25.0)    # not a large consumer — not required
    )
    .when(
        col("energy_certificate").isNotNull()
        & (col("energy_certificate") != "NONE"),
        lit(25.0)    # large consumer with certificate
    )
    .otherwise(lit(0.0))   # large consumer without certificate → non-compliant
)

# Building age / renovation momentum: 0–15 pts
# year_built ≥ 2010 → 15, 2000–2009 → 10, 1990–1999 → 5, < 1990 → 0
enefg_age_score = (
    when(col("year_built") >= 2010, lit(15.0))
    .when(col("year_built") >= 2000, lit(10.0))
    .when(col("year_built") >= 1990, lit(5.0))
    .otherwise(lit(0.0))
)

enefg_raw = enefg_eui_score + enefg_audit_score + enefg_age_score

df_base = (
    df_base
    .withColumn("enefg_is_large_consumer",
        (col("annual_consumption_kwh") / 1000.0) > ENEFG_LARGE_CONSUMER_MWH)
    .withColumn("enefg_audit_required",
        (col("country_code") == "DE")
        & ((col("annual_consumption_kwh") / 1000.0) > ENEFG_LARGE_CONSUMER_MWH))
    .withColumn("enefg_score",
        when(col("country_code") == "DE",
             spark_round(least(enefg_raw, lit(100.0)), 1))
        .otherwise(lit(None)))   # not applicable for TR
)


# ── 8. GEG SCORE (Germany only) ────────────────────────────────────────────────
# Gebäudeenergiegesetz 2024:
#   §10  Thermal performance: U-values must meet renovation limits when
#        replacing components (wall ≤0.24, roof ≤0.20, window ≤1.30 W/m²K)
#   §71  Heating systems: ≥65% renewable energy from 2024 onwards
#   nZEB: nearly Zero Energy Building aspirational target
#
# Score components:
#   35 pts: heating system compliance (§71 renewable heat requirement)
#   35 pts: U-value compliance (wall + roof + window, ~12 pts each)
#   30 pts: insulation freshness (insulation_year) + simulation flag

log_step("SCORE", "Computing GEG score …")

# Heating system score: 0–35 pts (§71)
geg_heating_score = (
    when(
        col("has_heat_pump") == True,
        lit(35.0)    # heat pump = fully renewable-compatible
    )
    .when(
        col("heating_fuel_type").isin("DISTRICT_HEAT", "BIOMASS"),
        lit(30.0)
    )
    .when(
        col("heating_fuel_type") == "ELECTRIC",
        lit(20.0)    # electric resistance = legal but not optimal
    )
    .when(
        col("heating_fuel_type") == "GAS",
        lit(5.0)     # gas boiler = non-compliant under new §71
    )
    .otherwise(lit(10.0))   # unknown / other
)

# U-value score: 0–35 pts (wall 12 + roof 12 + window 11)
# Each component: full pts if below GEG limit, 0 if above
geg_wall_pts   = when(
    col("wall_u_value").isNull(),   lit(6.0))  .when(col("wall_u_value")   <= GEG_WALL_U_MAX,   lit(12.0)).otherwise(lit(0.0))
geg_roof_pts   = when(
    col("roof_u_value").isNull(),   lit(6.0))  .when(col("roof_u_value")   <= GEG_ROOF_U_MAX,   lit(12.0)).otherwise(lit(0.0))
geg_window_pts = when(
    col("window_u_value").isNull(), lit(5.5))  .when(col("window_u_value") <= GEG_WINDOW_U_MAX, lit(11.0)).otherwise(lit(0.0))

geg_uvalue_score = geg_wall_pts + geg_roof_pts + geg_window_pts

# Insulation freshness + simulation flag: 0–30 pts
# insulation_year ≥ 2020 → 20 pts, 2010–2019 → 12 pts, < 2010 → 4 pts
# ins_geg_compliant (from simulation) → +10 pts bonus
geg_ins_year_score = (
    when(col("insulation_year") >= 2020, lit(20.0))
    .when(col("insulation_year") >= 2010, lit(12.0))
    .when(col("insulation_year").isNotNull(), lit(4.0))
    .otherwise(lit(8.0))    # no data → neutral
)
geg_ins_sim_bonus = when(col("ins_geg_compliant") == True, lit(10.0)).otherwise(lit(0.0))
geg_insulation_score = least(geg_ins_year_score + geg_ins_sim_bonus, lit(30.0))

geg_raw = geg_heating_score + geg_uvalue_score + geg_insulation_score

df_base = (
    df_base
    .withColumn("geg_wall_compliant",   col("wall_u_value")   <= GEG_WALL_U_MAX)
    .withColumn("geg_roof_compliant",   col("roof_u_value")   <= GEG_ROOF_U_MAX)
    .withColumn("geg_window_compliant", col("window_u_value") <= GEG_WINDOW_U_MAX)
    .withColumn("geg_heating_compliant",
        col("has_heat_pump")
        | col("heating_fuel_type").isin("DISTRICT_HEAT", "BIOMASS"))
    .withColumn("geg_score",
        when(col("country_code") == "DE",
             spark_round(least(geg_raw, lit(100.0)), 1))
        .otherwise(lit(None)))
)


# ── 9. EEG SCORE (Germany only) ────────────────────────────────────────────────
# Erneuerbare-Energien-Gesetz 2023:
#   Buildings with PV should maximise self-consumption
#   No PV on a roof-eligible building is a missed opportunity
#
# Score components:
#   50 pts: solar self-consumption rate (if has_pv)
#   30 pts: PV system presence (has_pv)
#   20 pts: battery storage for self-consumption optimisation (has_battery)

log_step("SCORE", "Computing EEG score …")

# Self-consumption component: 0–50 pts
eeg_selfcons_score = (
    when(~col("has_pv"), lit(25.0))   # no PV → neutral on self-consumption
    .when(col("solar_self_consumption_rate") >= EEG_SELF_CONSUMPTION_EXCELLENT,
          lit(50.0))
    .when(col("solar_self_consumption_rate") >= EEG_SELF_CONSUMPTION_TARGET_PCT,
          spark_round(
              50.0 * (col("solar_self_consumption_rate") - EEG_SELF_CONSUMPTION_TARGET_PCT)
              / (EEG_SELF_CONSUMPTION_EXCELLENT - EEG_SELF_CONSUMPTION_TARGET_PCT)
              + 25.0, 1))
    .otherwise(
        spark_round(
            25.0 * col("solar_self_consumption_rate")
            / EEG_SELF_CONSUMPTION_TARGET_PCT, 1))
)

# PV presence component: 0–30 pts
eeg_pv_score = when(col("has_pv"), lit(30.0)).otherwise(lit(0.0))

# Battery component: 0–20 pts
eeg_battery_score = when(col("has_battery"), lit(20.0)).otherwise(lit(0.0))

eeg_raw = eeg_selfcons_score + eeg_pv_score + eeg_battery_score

df_base = df_base.withColumn("eeg_score",
    when(col("country_code") == "DE",
         spark_round(least(eeg_raw, lit(100.0)), 1))
    .otherwise(lit(None)))


# ── 10. EPBD SCORE (all buildings) ─────────────────────────────────────────────
# Energy Performance of Buildings Directive:
#   2030 target: all buildings at least EPC class E (EUI ≤ 200 kWh/m²/yr)
#   2033 target: all buildings at least EPC class D (EUI ≤ 150 kWh/m²/yr)
#   2050 aspiration: nZEB (EUI ≤ 50 kWh/m²/yr)
#   Building-type-specific nZEB targets from ref_building_type_profiles
#
# Score:
#   100 if EUI ≤ nZEB target
#   Linear 50–99 between nZEB and class D target
#   Linear 20–49 between class D and class E target
#   0–19 if EUI > class E target

log_step("SCORE", "Computing EPBD score …")

# Use building-type nZEB target if available, else global default
nzeb_target = coalesce(col("eui_nzeb_target_kwh_m2"), lit(EPBD_NZEB_EUI_TARGET))

epbd_score_expr = (
    when(col("annual_eui_kwh_m2").isNull(), lit(40.0))  # no data → cautious neutral
    .when(col("annual_eui_kwh_m2") <= nzeb_target, lit(100.0))
    .when(col("annual_eui_kwh_m2") <= EPBD_CLASS_D_EUI_TARGET,
          spark_round(
              50.0 + 49.0 * (EPBD_CLASS_D_EUI_TARGET - col("annual_eui_kwh_m2"))
              / (EPBD_CLASS_D_EUI_TARGET - nzeb_target), 1))
    .when(col("annual_eui_kwh_m2") <= EPBD_CLASS_E_EUI_TARGET,
          spark_round(
              20.0 + 29.0 * (EPBD_CLASS_E_EUI_TARGET - col("annual_eui_kwh_m2"))
              / (EPBD_CLASS_E_EUI_TARGET - EPBD_CLASS_D_EUI_TARGET), 1))
    .otherwise(
        spark_round(
            greatest(
                lit(0.0),
                20.0 * (1.0 - (col("annual_eui_kwh_m2") - EPBD_CLASS_E_EUI_TARGET) / 100.0)
            ), 1))
)

df_base = (
    df_base
    .withColumn("epbd_nzeb_gap_kwh_m2",
        spark_round(
            when(col("annual_eui_kwh_m2").isNotNull(),
                 greatest(col("annual_eui_kwh_m2") - nzeb_target, lit(0.0)))
            .otherwise(lit(None)), 1))
    .withColumn("epbd_class_d_compliant",
        col("annual_eui_kwh_m2") <= EPBD_CLASS_D_EUI_TARGET)
    .withColumn("epbd_class_e_compliant",
        col("annual_eui_kwh_m2") <= EPBD_CLASS_E_EUI_TARGET)
    .withColumn("epbd_score", spark_round(epbd_score_expr, 1))
)


# ── 11. CSRD SCORE (all buildings) ─────────────────────────────────────────────
# Corporate Sustainability Reporting Directive (EU 2023/2365):
#   Companies with > 250 employees OR > €40M revenue must report Scope 1+2
#   Buildings must track carbon intensity (kg CO₂/m²/year)
#   EU Taxonomy "sustainable" threshold: < 10 kg CO₂/m²/year
#
# Score based on carbon intensity vs EU Taxonomy thresholds

log_step("SCORE", "Computing CSRD score …")

csrd_score_expr = (
    when(col("annual_carbon_intensity_kg_m2").isNull(), lit(40.0))
    .when(col("annual_carbon_intensity_kg_m2") <= CSRD_EXCELLENT_KG_M2,
          lit(100.0))
    .when(col("annual_carbon_intensity_kg_m2") <= CSRD_GOOD_KG_M2,
          spark_round(
              70.0 + 29.0 * (CSRD_GOOD_KG_M2 - col("annual_carbon_intensity_kg_m2"))
              / (CSRD_GOOD_KG_M2 - CSRD_EXCELLENT_KG_M2), 1))
    .when(col("annual_carbon_intensity_kg_m2") <= CSRD_PARTIAL_KG_M2,
          spark_round(
              50.0 + 19.0 * (CSRD_PARTIAL_KG_M2 - col("annual_carbon_intensity_kg_m2"))
              / (CSRD_PARTIAL_KG_M2 - CSRD_GOOD_KG_M2), 1))
    .when(col("annual_carbon_intensity_kg_m2") <= CSRD_AT_RISK_KG_M2,
          spark_round(
              30.0 + 19.0 * (CSRD_AT_RISK_KG_M2 - col("annual_carbon_intensity_kg_m2"))
              / (CSRD_AT_RISK_KG_M2 - CSRD_PARTIAL_KG_M2), 1))
    .otherwise(
        spark_round(
            greatest(
                lit(0.0),
                30.0 * (1.0 - (col("annual_carbon_intensity_kg_m2") - CSRD_AT_RISK_KG_M2) / 40.0)
            ), 1))
)

df_base = df_base.withColumn("csrd_score", spark_round(csrd_score_expr, 1))


# ── 12. BEP-TR SCORE (Turkey only) ─────────────────────────────────────────────
# Binalarda Enerji Performansı Yönetmeliği (BEP-TR):
#   Energy performance certificate classes A–G based on annual EUI
#   Mandatory for all buildings > 50 m² from 2011 (Yönetmelik §5)
#   Class C or better is the recommended renovation target for existing stock
#
# Score = directly mapped from EUI class:
#   A (≤75)  → 100 | B (75-100) → 80 | C (100-125) → 65
#   D (125-150) → 45 | E (150-175) → 30 | F (175-200) → 15 | G (>200) → 5

log_step("SCORE", "Computing BEP-TR score …")

beptr_class_expr = (
    when(col("annual_eui_kwh_m2").isNull(),                        lit("UNKNOWN"))
    .when(col("annual_eui_kwh_m2") <= BEPTR_CLASS_A_MAX,           lit("A"))
    .when(col("annual_eui_kwh_m2") <= BEPTR_CLASS_B_MAX,           lit("B"))
    .when(col("annual_eui_kwh_m2") <= BEPTR_CLASS_C_MAX,           lit("C"))
    .when(col("annual_eui_kwh_m2") <= BEPTR_CLASS_D_MAX,           lit("D"))
    .when(col("annual_eui_kwh_m2") <= BEPTR_CLASS_E_MAX,           lit("E"))
    .when(col("annual_eui_kwh_m2") <= BEPTR_CLASS_F_MAX,           lit("F"))
    .otherwise(lit("G"))
)

beptr_score_expr = (
    when(col("annual_eui_kwh_m2").isNull(),                        lit(40.0))
    .when(col("annual_eui_kwh_m2") <= BEPTR_CLASS_A_MAX,           lit(100.0))
    .when(col("annual_eui_kwh_m2") <= BEPTR_CLASS_B_MAX,           lit(80.0))
    .when(col("annual_eui_kwh_m2") <= BEPTR_CLASS_C_MAX,           lit(65.0))
    .when(col("annual_eui_kwh_m2") <= BEPTR_CLASS_D_MAX,           lit(45.0))
    .when(col("annual_eui_kwh_m2") <= BEPTR_CLASS_E_MAX,           lit(30.0))
    .when(col("annual_eui_kwh_m2") <= BEPTR_CLASS_F_MAX,           lit(15.0))
    .otherwise(lit(5.0))
)

df_base = (
    df_base
    .withColumn("beptr_energy_class", beptr_class_expr)
    .withColumn("beptr_score",
        when(col("country_code") == "TR",
             spark_round(beptr_score_expr, 1))
        .otherwise(lit(None)))
)


# ── 13. OVERALL COMPLIANCE SCORE ───────────────────────────────────────────────
# Weighted average using country-specific weights.
# Null scores (regulations not applicable) are excluded from the weighted sum.

log_step("SCORE", "Computing overall compliance score …")

overall_score_de = (
    col("enefg_score") * DE_WEIGHTS["enefg"]
    + col("geg_score")   * DE_WEIGHTS["geg"]
    + col("eeg_score")   * DE_WEIGHTS["eeg"]
    + col("epbd_score")  * DE_WEIGHTS["epbd"]
    + col("csrd_score")  * DE_WEIGHTS["csrd"]
)

overall_score_tr = (
    col("beptr_score")  * TR_WEIGHTS["beptr"]
    + col("epbd_score") * TR_WEIGHTS["epbd"]
    + col("csrd_score") * TR_WEIGHTS["csrd"]
)

df_base = df_base.withColumn(
    "overall_score",
    spark_round(
        when(col("country_code") == "DE", overall_score_de)
        .when(col("country_code") == "TR", overall_score_tr)
        .otherwise(col("epbd_score")),    # fallback: EPBD only for other countries
        1)
)


# ── 14. STATUS LABELS ──────────────────────────────────────────────────────────

df_base = (
    df_base
    .withColumn("overall_status",  score_to_status(col("overall_score")))
    .withColumn("enefg_status",    score_to_status(col("enefg_score")))
    .withColumn("geg_status",      score_to_status(col("geg_score")))
    .withColumn("eeg_status",      score_to_status(col("eeg_score")))
    .withColumn("epbd_status",     score_to_status(col("epbd_score")))
    .withColumn("csrd_status",     score_to_status(col("csrd_score")))
    .withColumn("beptr_status",    score_to_status(col("beptr_score")))
)


# ── 15. PRIORITY ACTION ────────────────────────────────────────────────────────
# Identify the single highest-priority action per building
# based on the lowest individual score

log_step("PRIORITY", "Deriving priority actions …")

df_base = df_base.withColumn(
    "priority_action",
    when(col("country_code") == "DE",
        when(col("geg_score") < 40,
             lit("UPGRADE_HEATING_SYSTEM_GEG71"))
        .when(col("enefg_score") < 40,
             lit("REDUCE_ENERGY_INTENSITY_ENEFG"))
        .when(col("geg_score") < 60,
             lit("IMPROVE_BUILDING_ENVELOPE_GEG"))
        .when(col("eeg_score") < 50,
             lit("ADD_SOLAR_OR_BATTERY_EEG"))
        .when(col("epbd_score") < 60,
             lit("REDUCE_EUI_TO_EPBD_CLASS_D"))
        .when(col("csrd_score") < 60,
             lit("REDUCE_CARBON_INTENSITY_CSRD"))
        .otherwise(lit("MAINTAIN_AND_MONITOR"))
    )
    .when(col("country_code") == "TR",
        when(col("beptr_score") < 45,
             lit("MAJOR_RETROFIT_BEPTR_CLASS_C"))
        .when(col("beptr_score") < 65,
             lit("ENVELOPE_UPGRADE_BEPTR"))
        .when(col("epbd_score") < 50,
             lit("REDUCE_EUI_EPBD_2030"))
        .when(col("csrd_score") < 60,
             lit("REDUCE_CARBON_CSRD"))
        .otherwise(lit("MAINTAIN_AND_MONITOR"))
    )
    .otherwise(lit("MAINTAIN_AND_MONITOR"))
)


# ── 16. INCENTIVE ELIGIBILITY SUMMARY ─────────────────────────────────────────
# Quick lookup of applicable grants per country (for Power BI badge display)

df_base = (
    df_base
    .withColumn("kfw_programs_applicable",
        when(col("country_code") == "DE",
            concat_ws(", ",
                when(col("geg_heating_compliant") == False,
                     lit("KfW BEG §71 (Heizungstausch)")),
                when(col("geg_wall_compliant") == False,
                     lit("KfW BEG (Einzelmaßnahme Wand)")),
                when(col("eeg_score") < 60,
                     lit("KfW 270 (Erneuerbare Energien)"))
            ))
        .otherwise(lit(None))
    )
    .withColumn("bafa_programs_applicable",
        when(col("country_code") == "DE",
            concat_ws(", ",
                when(col("has_heat_pump") == False,
                     lit("BAFA BEG EM (Wärmepumpe)")),
                when(col("geg_score") < 60,
                     lit("BAFA Energieberatung"))
            ))
        .otherwise(lit(None))
    )
    .withColumn("yeka_programs_applicable",
        when(col("country_code") == "TR",
            concat_ws(", ",
                when(col("has_pv") == False,
                     lit("YEKA GES (Solar Teşviki)")),
                when(col("beptr_score") < 65,
                     lit("YEKA Bina Verimliliği"))
            ))
        .otherwise(lit(None))
    )
)


# ── 17. ASSEMBLE gold_compliance_results (wide) ────────────────────────────────

log_step("ASSEMBLE", "Building gold_compliance_results …")

df_results = df_base.select(
    # Identifiers
    col("building_id"),
    col("building_name"),
    col("building_type"),
    col("country_code"),
    col("city"),
    col("year_built"),
    col("subscription_tier"),
    current_timestamp().alias("assessed_at"),
    # KPI inputs used for scoring
    spark_round(col("annual_eui_kwh_m2"), 1).alias("annual_eui_kwh_m2"),
    spark_round(col("annual_carbon_intensity_kg_m2"), 2).alias("annual_carbon_intensity_kg_m2"),
    spark_round(col("solar_self_consumption_rate") * 100.0, 1).alias("solar_self_consumption_pct"),
    # Overall
    col("overall_score"),
    col("overall_status"),
    col("priority_action"),
    # EnEfG (DE)
    col("enefg_score"),
    col("enefg_status"),
    col("enefg_audit_required"),
    col("enefg_is_large_consumer"),
    # GEG (DE)
    col("geg_score"),
    col("geg_status"),
    col("geg_heating_compliant"),
    col("geg_wall_compliant"),
    col("geg_roof_compliant"),
    col("geg_window_compliant"),
    spark_round(col("wall_u_value"), 3).alias("wall_u_value_current"),
    spark_round(col("roof_u_value"), 3).alias("roof_u_value_current"),
    spark_round(col("window_u_value"), 3).alias("window_u_value_current"),
    # EEG (DE)
    col("eeg_score"),
    col("eeg_status"),
    # EPBD (all)
    col("epbd_score"),
    col("epbd_status"),
    col("epbd_nzeb_gap_kwh_m2"),
    col("epbd_class_d_compliant"),
    col("epbd_class_e_compliant"),
    # CSRD (all)
    col("csrd_score"),
    col("csrd_status"),
    # BEP-TR (TR)
    col("beptr_score"),
    col("beptr_status"),
    col("beptr_energy_class"),
    # Incentives
    col("kfw_programs_applicable"),
    col("bafa_programs_applicable"),
    col("yeka_programs_applicable"),
)

log_step("ASSEMBLE", "gold_compliance_results ready", rows=df_results.count())


# ── 18. ASSEMBLE gold_compliance_issues (long) ────────────────────────────────
# One row per building × rule check
# Severity: CRITICAL (<30), WARNING (30-60), INFO (60-80), OK (>80)

log_step("ASSEMBLE", "Building gold_compliance_issues …")

from pyspark.sql import Row

def make_issue(building_id_col, regulation, rule_code, score_col,
               current_val_col, threshold_val, unit, severity_override=None):
    """Return a struct expression for one issue row."""
    severity = severity_override or (
        when(score_col < 30, lit("CRITICAL"))
        .when(score_col < 60, lit("WARNING"))
        .when(score_col < 80, lit("INFO"))
        .otherwise(lit("OK"))
    )
    return (
        col("building_id"),
        col("country_code"),
        lit(regulation).alias("regulation"),
        lit(rule_code).alias("rule_code"),
        spark_round(score_col, 1).alias("score"),
        severity.alias("severity"),
        spark_round(current_val_col, 2).alias("current_value"),
        lit(threshold_val).alias("threshold_value"),
        lit(unit).alias("unit"),
        current_timestamp().alias("checked_at"),
    )


# Build issues for each rule — one DataFrame per rule, then union all

def issues_df(df_in, regulation, rule_code, score_col_name,
              current_val_col_name, threshold_val, unit,
              applicable_filter=None):
    """
    Create a long-format issues DataFrame for a single rule.
    applicable_filter: Column expression to limit rows (e.g. country_code == DE)
    """
    base = df_in if applicable_filter is None else df_in.filter(applicable_filter)
    score_col   = col(score_col_name)
    current_col = col(current_val_col_name) if current_val_col_name else lit(None)
    return base.select(
        col("building_id"),
        col("building_name"),
        col("country_code"),
        lit(regulation).alias("regulation"),
        lit(rule_code).alias("rule_code"),
        spark_round(score_col, 1).alias("score"),
        (
            when(score_col < 30, lit("CRITICAL"))
            .when(score_col < 60, lit("WARNING"))
            .when(score_col < 80, lit("INFO"))
            .otherwise(lit("OK"))
        ).alias("severity"),
        spark_round(current_col.cast("double"), 2).alias("current_value"),
        lit(float(threshold_val)).alias("threshold_value"),
        lit(unit).alias("unit"),
        current_timestamp().alias("checked_at"),
    )


de_filter = col("country_code") == "DE"
tr_filter = col("country_code") == "TR"

issues_parts = [
    issues_df(df_base, "EnEfG", "ENEFG_ENERGY_INTENSITY",
              "enefg_score", "annual_eui_kwh_m2", 130.0, "kWh/m2/year", de_filter),

    issues_df(df_base, "GEG", "GEG_HEATING_SYSTEM",
              "geg_score", "geg_score", 60.0, "score", de_filter),

    issues_df(df_base, "GEG", "GEG_WALL_U_VALUE",
              "geg_score", "wall_u_value", GEG_WALL_U_MAX, "W/m2K", de_filter),

    issues_df(df_base, "GEG", "GEG_ROOF_U_VALUE",
              "geg_score", "roof_u_value", GEG_ROOF_U_MAX, "W/m2K", de_filter),

    issues_df(df_base, "GEG", "GEG_WINDOW_U_VALUE",
              "geg_score", "window_u_value", GEG_WINDOW_U_MAX, "W/m2K", de_filter),

    issues_df(df_base, "EEG", "EEG_SOLAR_SELF_CONSUMPTION",
              "eeg_score", "solar_self_consumption_rate", EEG_SELF_CONSUMPTION_TARGET_PCT, "ratio", de_filter),

    issues_df(df_base, "EPBD", "EPBD_NZEB_GAP",
              "epbd_score", "annual_eui_kwh_m2", EPBD_NZEB_EUI_TARGET, "kWh/m2/year"),

    issues_df(df_base, "CSRD", "CSRD_CARBON_INTENSITY",
              "csrd_score", "annual_carbon_intensity_kg_m2", CSRD_EXCELLENT_KG_M2, "kgCO2/m2/year"),

    issues_df(df_base, "BEP-TR", "BEPTR_ENERGY_CLASS",
              "beptr_score", "annual_eui_kwh_m2", BEPTR_CLASS_C_MAX, "kWh/m2/year", tr_filter),
]

df_issues = issues_parts[0]
for part in issues_parts[1:]:
    df_issues = df_issues.union(part)

log_step("ASSEMBLE", "gold_compliance_issues ready", rows=df_issues.count())


# ── 19. WRITE gold_compliance_results (MERGE upsert) ──────────────────────────

log_step("WRITE", "Writing gold_compliance_results …")

target_results = GOLD_PATHS["compliance_results"]

if DeltaTable.isDeltaTable(spark, target_results):
    spark.conf.set("spark.databricks.delta.schema.autoMerge.enabled", "true")
    delta_tbl = DeltaTable.forPath(spark, target_results)
    (
        delta_tbl.alias("tgt")
        .merge(df_results.alias("src"), "tgt.building_id = src.building_id")
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )
    log_step("WRITE", "gold_compliance_results — MERGE complete")
else:
    (
        df_results.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .partitionBy("country_code")
        .save(target_results)
    )
    log_step("WRITE", "gold_compliance_results — initial write complete")


# ── 20. WRITE gold_compliance_issues (MERGE upsert) ───────────────────────────

log_step("WRITE", "Writing gold_compliance_issues …")

target_issues = GOLD_PATHS["compliance_issues"]

if DeltaTable.isDeltaTable(spark, target_issues):
    spark.conf.set("spark.databricks.delta.schema.autoMerge.enabled", "true")
    delta_tbl_i = DeltaTable.forPath(spark, target_issues)
    (
        delta_tbl_i.alias("tgt")
        .merge(
            df_issues.alias("src"),
            "tgt.building_id = src.building_id AND tgt.rule_code = src.rule_code"
        )
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )
    log_step("WRITE", "gold_compliance_issues — MERGE complete")
else:
    (
        df_issues.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .partitionBy("country_code")
        .save(target_issues)
    )
    log_step("WRITE", "gold_compliance_issues — initial write complete")


# ── 21. OPTIMIZE ───────────────────────────────────────────────────────────────

log_step("OPTIMIZE", "Running OPTIMIZE on compliance tables …")

spark.sql(f"OPTIMIZE delta.`{target_results}` ZORDER BY (country_code, overall_score)")
spark.sql(f"OPTIMIZE delta.`{target_issues}` ZORDER BY (country_code, regulation, severity)")

log_step("OPTIMIZE", "OPTIMIZE complete")


# ── 22. VALIDATION REPORT ──────────────────────────────────────────────────────

log_step("VALIDATE", "Running validation …")

df_val   = spark.read.format("delta").load(target_results)
df_val_i = spark.read.format("delta").load(target_issues)

total = df_val.count()
de_cnt = df_val.filter(col("country_code") == "DE").count()
tr_cnt = df_val.filter(col("country_code") == "TR").count()

print()
print("=" * 72)
print("  COMPLIANCE CHECKER — VALIDATION REPORT")
print("=" * 72)
print(f"  Buildings assessed : {total}")
print(f"    Germany (DE)     : {de_cnt}")
print(f"    Turkey  (TR)     : {tr_cnt}")
print(f"  Total issues logged: {df_val_i.count()}")
print()

print("── OVERALL SCORES ──────────────────────────────────────────────────────")
df_val.select(
    "building_id", "country_code", "building_type",
    "annual_eui_kwh_m2",
    "overall_score", "overall_status", "priority_action"
).orderBy("country_code", "overall_score").show(truncate=False)

print("── GERMANY: REGULATION SCORES ──────────────────────────────────────────")
df_val.filter(col("country_code") == "DE").select(
    "building_id",
    "enefg_score", "enefg_status",
    "geg_score", "geg_status",
    "eeg_score", "eeg_status",
    "epbd_score", "csrd_score",
).show(truncate=False)

print("── GERMANY: GEG U-VALUE DETAILS ────────────────────────────────────────")
df_val.filter(col("country_code") == "DE").select(
    "building_id",
    "wall_u_value_current", "geg_wall_compliant",
    "roof_u_value_current", "geg_roof_compliant",
    "window_u_value_current", "geg_window_compliant",
    "geg_heating_compliant",
).show(truncate=False)

print("── TURKEY: BEP-TR SCORES ───────────────────────────────────────────────")
df_val.filter(col("country_code") == "TR").select(
    "building_id",
    "annual_eui_kwh_m2", "beptr_energy_class",
    "beptr_score", "beptr_status",
    "epbd_score", "csrd_score",
).show(truncate=False)

print("── CRITICAL / WARNING ISSUES ───────────────────────────────────────────")
df_val_i.filter(col("severity").isin("CRITICAL", "WARNING")).select(
    "building_id", "regulation", "rule_code",
    "severity", "score", "current_value", "threshold_value", "unit"
).orderBy("severity", "score").show(truncate=False)

print("── INCENTIVE PROGRAMMES MATCHED ────────────────────────────────────────")
df_val.filter(
    col("kfw_programs_applicable").isNotNull()
    | col("bafa_programs_applicable").isNotNull()
    | col("yeka_programs_applicable").isNotNull()
).select(
    "building_id", "country_code",
    "kfw_programs_applicable",
    "bafa_programs_applicable",
    "yeka_programs_applicable",
).show(truncate=False)

print("=" * 72)
print("  05_compliance_checker.py — COMPLETE")
print("=" * 72)
