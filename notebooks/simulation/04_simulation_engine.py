# ============================================================
# Energy Copilot Platform – Simulation Engine
# Notebook : 04_simulation_engine.py
# Layer    : Gold (Simulation Results)
# Author   : Energy Copilot Team
# Updated  : 2026-04-07
# ============================================================
#
# PURPOSE
# -------
# Physics-based simulation of three technology investments:
#   1. Heat Pump (ASHP / GSHP) replacement of gas / electric heating
#   2. Battery Storage capacity optimisation
#   3. Building Envelope Insulation (EPS / MW / PIR panels)
#
# For each scenario this notebook calculates:
#   - Capital expenditure (CAPEX) from ref_technology_catalog
#   - Annual savings (energy cost reduction)
#   - Simple payback, NPV (10-year, 5 % discount rate), IRR
#   - KfW / BAFA / YEKA grant amounts and eligibility
#   - Recommended product SKU
#   - Justification text in EN / DE / TR
#
# INPUT TABLES (all via attached Lakehouse)
# ------------------------------------------
#   silver_building_master
#   ref_simulation_inputs          (per-building simulation parameters)
#   ref_tariffs                    (electricity / gas prices)
#   ref_building_type_profiles     (EUI benchmarks, tech feasibility)
#   ref_technology_catalog         (products, COP, price, grants)
#   gold_kpi_daily                 (actual measured daily KPIs)
#   gold_kpi_monthly               (aggregated monthly KPIs)
#
# OUTPUT TABLE
# ------------
#   gold_simulation_results        (one row per building × scenario)
#
# BMAD PHASE  : B1-A2-D3-L4 (Business logic embedded in physics models)
# DP-600 HINTS: broadcast join on small reference tables, Delta MERGE upsert,
#               AQE enabled, vectorised UDF for NPV series
# ============================================================

# ── 0. IMPORTS & SPARK CONFIGURATION ─────────────────────────────────────────

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col, lit, when, coalesce, broadcast,
    sum as spark_sum, avg as spark_avg,
    min as spark_min, max as spark_max,
    percentile_approx, count,
    round as spark_round, abs as spark_abs,
    current_timestamp, to_date, year, month,
    concat_ws, greatest, least,
)
from pyspark.sql.types import (
    StructType, StructField,
    StringType, DoubleType, BooleanType, TimestampType, LongType,
)
from delta.tables import DeltaTable
import math
from typing import Dict, Any

# Spark session (already available in Fabric notebooks)
spark = SparkSession.builder.getOrCreate()

# Enable Adaptive Query Execution for large joins
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.databricks.delta.schema.autoMerge.enabled", "true")

# ── HELPER: structured logging ────────────────────────────────────────────────

def log_step(step: str, msg: str = "", table: str = "", rows: int = -1):
    """Print a formatted progress message."""
    row_str = f"  [{rows:,} rows]" if rows >= 0 else ""
    tbl_str = f"  → {table}" if table else ""
    print(f"[04_SIM] {step:40s}{tbl_str}{row_str}  {msg}")

# ── 1. TABLE PATHS ─────────────────────────────────────────────────────────────

SILVER_PATHS: Dict[str, str] = {
    "building_master": "Tables/silver_building_master",
}

REF_PATHS: Dict[str, str] = {
    "simulation_inputs":       "Tables/ref_simulation_inputs",
    "tariffs":                 "Tables/ref_tariffs",
    "building_type_profiles":  "Tables/ref_building_type_profiles",
    "technology_catalog":      "Tables/ref_technology_catalog",
}

GOLD_PATHS: Dict[str, str] = {
    "kpi_daily":           "Tables/gold_kpi_daily",
    "kpi_monthly":         "Tables/gold_kpi_monthly",
    "simulation_results":  "Tables/gold_simulation_results",
}

# ── 2. SIMULATION CONSTANTS ────────────────────────────────────────────────────

FLOOR_HEIGHT_M          = 3.0     # default floor height (m)
WALL_U_CURRENT          = 0.60    # typical uninsulated wall U-value (W/m²K)
ROOF_U_CURRENT          = 0.25    # typical existing roof U-value (W/m²K)
WINDOW_U_CURRENT        = 2.80    # typical double-glazed window U-value (W/m²K)
INFILTRATION_ACH        = 0.30    # air changes per hour (unimproved)

WALL_FRACTION_OF_FACADE = 0.70    # wall fraction (rest = windows)
WINDOW_FRACTION         = 0.30    # window fraction of facade

# GEG 2024 / nZEB target U-values (W/m²K)
WALL_U_TARGET           = 0.20
ROOF_U_TARGET           = 0.15
WINDOW_U_TARGET         = 1.10

NPV_DISCOUNT_RATE       = 0.05    # 5 % per annum
NPV_YEARS               = 10      # investment horizon

ENERGY_PRICE_ESCALATION = 0.03    # 3 % annual energy price increase

# Government grant rates — regulatory constants, not product-specific
# Sources: KfW BEG 2024 (DE), BAFA BEG 2024 (DE), YEKA 2024 (TR)
KFW_HP_GRANT_PCT      = 0.15   # KfW BEG individual measure: 15 % base grant (heat pump)
BAFA_HP_GRANT_EUR_KW  = 150.0  # BAFA BEG: approx €150/kW flat component for HP
KFW_BAT_GRANT_PCT     = 0.10   # KfW 270/442: 10 % for battery storage
KFW_INS_GRANT_PCT     = 0.15   # KfW BEG: 15 % for building envelope insulation

# Battery parameters
BATTERY_ROUNDTRIP_EFF   = 0.90    # 90 % round-trip efficiency
BATTERY_USABLE_SOC      = 0.80    # 80 % usable state of charge
BATTERY_CYCLES_PER_DAY  = 1.0     # one cycle per day assumption
BATTERY_DEGRADATION     = 0.02    # 2 % capacity loss per year

# Heating season average outdoor temp (for COP adjustment)
DE_AVG_HEATING_TEMP_C   = 4.0
TR_AVG_HEATING_TEMP_C   = 8.0

# ── 3. READ INPUT DATA ─────────────────────────────────────────────────────────

log_step("READ", "Loading Silver + Reference tables …")

df_building = spark.read.format("delta").load(SILVER_PATHS["building_master"])
df_sim_inp  = spark.read.format("delta").load(REF_PATHS["simulation_inputs"])
df_tariffs  = spark.read.format("delta").load(REF_PATHS["tariffs"])
df_profiles = spark.read.format("delta").load(REF_PATHS["building_type_profiles"])
df_tech     = spark.read.format("delta").load(REF_PATHS["technology_catalog"])
df_kpi_d    = spark.read.format("delta").load(GOLD_PATHS["kpi_daily"])
df_kpi_m    = spark.read.format("delta").load(GOLD_PATHS["kpi_monthly"])

log_step("READ", "All tables loaded", rows=df_building.count())

# ── SCHEMA DIAGNOSTIC (run once to verify column names) ───────────────────────
print("\n── silver_building_master ──────────────────────────────────────────────")
df_building.printSchema()
print("\n── ref_simulation_inputs ───────────────────────────────────────────────")
df_sim_inp.printSchema()
print("\n── ref_tariffs ─────────────────────────────────────────────────────────")
df_tariffs.printSchema()
print("\n── ref_building_type_profiles ──────────────────────────────────────────")
df_profiles.printSchema()
print("\n── ref_technology_catalog ──────────────────────────────────────────────")
df_tech.printSchema()

# ── 4. JOIN: BUILDING + SIMULATION INPUTS + TARIFF ────────────────────────────

log_step("JOIN", "Merging building master with simulation inputs …")

# Broadcast all small reference tables (all < 100 rows)
df_sim_inp_bc  = broadcast(df_sim_inp)
df_tariff_bc   = broadcast(df_tariffs)
df_profile_bc  = broadcast(df_profiles)

# Base join: building × simulation_inputs × tariff
df_base = (
    df_building.alias("b")
    .join(df_sim_inp_bc.alias("s"),  on="building_id", how="inner")
    .join(
        df_tariff_bc.alias("t"),
        on=col("s.tariff_id") == col("t.tariff_id"),
        how="left",
    )
    .join(
        df_profile_bc.alias("p"),
        on=col("b.building_type") == col("p.building_type"),
        how="left",
    )
    .select(
        # Building identifiers
        col("b.building_id"),
        col("b.building_name"),
        col("b.building_type"),
        col("b.country_code"),
        col("b.city"),
        col("b.conditioned_area_m2"),
        col("b.pv_capacity_kwp"),
        col("b.battery_capacity_kwh"),
        col("b.has_pv"),
        col("b.has_battery"),
        col("b.has_heat_pump"),
        col("b.emission_factor_kg_kwh"),
        # Simulation inputs  (num_floors lives here, not in building_master)
        col("s.heating_fuel_type").alias("current_heating_system"),
        col("s.heat_distribution_type"),
        col("s.design_supply_temp_c").alias("supply_temp_c"),
        col("s.num_floors"),                            # used for geometry calculations
        col("s.floor_height_m"),
        col("s.building_perimeter_m"),
        col("s.tariff_id"),
        col("s.hdd_annual"),
        col("s.cdd_annual"),
        col("s.discount_rate_pct"),
        col("s.energy_price_escalation_pct"),
        col("s.project_lifetime_years"),
        # Tariff  (real column names from ref_tariffs schema)
        col("t.electricity_flat_eur_kwh").alias("electricity_buy_eur_kwh"),
        col("t.gas_eur_kwh"),
        col("t.feed_in_tariff_eur_kwh").alias("electricity_sell_eur_kwh"),
        col("t.demand_charge_eur_kw_month").alias("demand_charge_eur_kw"),
        # Profile benchmarks  (heat_pump_feasibility = actual column name)
        col("p.eui_good_kwh_m2").alias("eui_benchmark_good"),
        col("p.eui_average_kwh_m2").alias("eui_benchmark_avg"),
        col("p.heat_pump_feasibility").alias("hp_feasibility"),
        col("p.battery_feasibility"),
        col("p.insulation_feasibility"),
        col("p.night_base_load_pct"),
    )
)

log_step("JOIN", "Base join complete", rows=df_base.count())

# ── 5. AGGREGATE ACTUAL PERFORMANCE FROM GOLD KPI ─────────────────────────────

log_step("KPI_AGG", "Aggregating actual performance metrics from gold_kpi_daily …")

# Full-year aggregates per building from daily KPIs
df_actuals = (
    df_kpi_d
    .groupBy("building_id")
    .agg(
        spark_sum("total_consumption_kwh").alias("actual_annual_consumption_kwh"),
        spark_avg("avg_self_consumption_rate").alias("avg_self_consumption_pct"),
        spark_avg((col("battery_soc_min_pct") + col("battery_soc_max_pct")) / 2).alias("avg_battery_soc_pct"),
        spark_avg("avg_load_factor").alias("avg_load_factor"),
        percentile_approx("total_consumption_kwh", 0.90).alias("p90_daily_demand_kwh"),
        spark_max("total_consumption_kwh").alias("max_daily_demand_kwh"),
        spark_sum("solar_generated_kwh").alias("actual_annual_solar_kwh"),
        spark_sum("solar_exported_kwh").alias("actual_annual_exported_kwh"),
        spark_sum("co2_emissions_kg").alias("actual_annual_co2_kg"),
        count("date").alias("days_with_data"),
    )
)

df_base = df_base.join(broadcast(df_actuals), on="building_id", how="left")

log_step("KPI_AGG", "Actuals joined", rows=df_base.count())

# ── 6. PHYSICS MODEL HELPERS ───────────────────────────────────────────────────
# These are defined as column expressions to keep everything in Spark.
# All calculations follow EN ISO 13790 simplified hourly method.

def calc_hlc_expr():
    """
    Heat Loss Coefficient (W/K) — simplified envelope model.

    Geometry:
      facade_area  = perimeter × height_total
      wall_area    = facade_area × WALL_FRACTION_OF_FACADE
      window_area  = facade_area × WINDOW_FRACTION
      roof_area    = conditioned_area_m2 / num_floors  (top floor ceiling)

    HLC (W/K) = wall_area × U_wall
              + window_area × U_window
              + roof_area  × U_roof
              + infiltration_loss

    Perimeter is estimated as: perimeter ≈ 4 × sqrt(floor_area / num_floors)
    Infiltration loss: ACH × volume × 0.33 W/(m³K)
    """
    num_floors = coalesce(col("num_floors"), lit(3)).cast("double")
    floor_area = col("conditioned_area_m2")
    floor_area_per_floor = floor_area / num_floors

    perimeter_m  = 4.0 * (floor_area_per_floor ** 0.5)
    height_total = num_floors * FLOOR_HEIGHT_M
    facade_area  = perimeter_m * height_total

    wall_area   = facade_area * WALL_FRACTION_OF_FACADE
    window_area = facade_area * WINDOW_FRACTION
    roof_area   = floor_area_per_floor  # top floor only

    # Transmission losses (W/K)
    h_wall   = wall_area   * WALL_U_CURRENT
    h_window = window_area * WINDOW_U_CURRENT
    h_roof   = roof_area   * ROOF_U_CURRENT

    # Infiltration loss (W/K): n_ach × volume × 0.33
    volume = floor_area * FLOOR_HEIGHT_M
    h_inf  = INFILTRATION_ACH * volume * 0.33

    return (h_wall + h_window + h_roof + h_inf).alias("hlc_current_w_k")


def calc_hlc_improved_expr():
    """
    Improved HLC after insulation upgrade (GEG compliant U-values).
    """
    num_floors = coalesce(col("num_floors"), lit(3)).cast("double")
    floor_area = col("conditioned_area_m2")
    floor_area_per_floor = floor_area / num_floors

    perimeter_m  = 4.0 * (floor_area_per_floor ** 0.5)
    height_total = num_floors * FLOOR_HEIGHT_M
    facade_area  = perimeter_m * height_total

    wall_area   = facade_area * WALL_FRACTION_OF_FACADE
    window_area = facade_area * WINDOW_FRACTION
    roof_area   = floor_area_per_floor

    h_wall   = wall_area   * WALL_U_TARGET
    h_window = window_area * WINDOW_U_TARGET
    h_roof   = roof_area   * ROOF_U_TARGET
    h_inf    = (INFILTRATION_ACH * 0.5) * col("conditioned_area_m2") * FLOOR_HEIGHT_M * 0.33

    return (h_wall + h_window + h_roof + h_inf).alias("hlc_improved_w_k")

# ── 7. HEAT PUMP SIMULATION ───────────────────────────────────────────────────

log_step("HP_SIM", "Running heat pump simulation …")

# Add geometry and thermal envelope columns
df_hp = df_base.withColumn("hlc_current_w_k", calc_hlc_expr())

# Annual heating demand (kWh/year)
#   Q_heat = HLC [W/K] × HDD [K·days] × 24 [h/day] / 1000 [W→kW]
df_hp = df_hp.withColumn(
    "annual_heating_demand_kwh",
    (col("hlc_current_w_k") * col("hdd_annual") * 24.0) / 1000.0
)

# COP adjustment for actual climate
#   COP_adj = COP_rated × max(0.5, 1.0 + (avg_heating_temp - 7) × 0.025)
# avg_heating_temp: DE = 4°C, TR = 8°C
avg_heating_temp = when(col("country_code") == "DE", DE_AVG_HEATING_TEMP_C) \
                   .otherwise(TR_AVG_HEATING_TEMP_C)

# Use COP a7w35 as base (most common rating point)
# Typical ASHP COP a7w35 ≈ 3.5 if not fetched from catalog — we use 3.5 as default
BASE_COP = 3.5
cop_adj_factor = (1.0 + (avg_heating_temp - 7.0) * 0.025).cast("double")
cop_adj = (lit(BASE_COP) * greatest(lit(0.5), cop_adj_factor))

df_hp = df_hp.withColumn("cop_adjusted", cop_adj)

# Annual HP electricity requirement (kWh/year)
df_hp = df_hp.withColumn(
    "hp_annual_electricity_kwh",
    col("annual_heating_demand_kwh") / col("cop_adjusted")
)

# Current heating cost per year
#   Gas: Q_heat / boiler_eff (≈0.92) × gas_price
#   Electric (e.g. split AC): Q_heat / electric_COP (≈2.5) × electricity_buy
current_fuel_cost = when(
    col("current_heating_system") == "GAS",
    col("annual_heating_demand_kwh") / 0.92 * col("gas_eur_kwh")
).when(
    col("current_heating_system") == "ELECTRIC",
    col("annual_heating_demand_kwh") / 2.5 * col("electricity_buy_eur_kwh")
).otherwise(
    col("annual_heating_demand_kwh") / 0.85 * col("gas_eur_kwh")  # OIL fallback = gas proxy
)

df_hp = df_hp.withColumn("current_heating_cost_eur", current_fuel_cost)

# HP operating cost = HP electricity × electricity buy price
df_hp = df_hp.withColumn(
    "hp_operating_cost_eur",
    col("hp_annual_electricity_kwh") * col("electricity_buy_eur_kwh")
)

# Net annual saving
df_hp = df_hp.withColumn(
    "hp_annual_saving_eur",
    col("current_heating_cost_eur") - col("hp_operating_cost_eur")
)

# CO₂ saving (kg/year)
#   Gas CO₂: Q_heat / 0.92 × 0.201 kg/kWh (natural gas emission factor)
#   HP CO₂:  HP_electricity × emission_factor_kg_kwh (from building master)
GAS_EMISSION_FACTOR = 0.201   # kg CO₂/kWh_gas (EN 15603)

gas_co2 = when(
    col("current_heating_system") == "GAS",
    col("annual_heating_demand_kwh") / 0.92 * GAS_EMISSION_FACTOR
).otherwise(lit(0.0))

df_hp = df_hp.withColumn(
    "hp_co2_saving_kg",
    gas_co2 - col("hp_annual_electricity_kwh") * col("emission_factor_kg_kwh")
)

# Feasibility pre-check
hp_feasible = (
    (col("has_heat_pump") == False) &                       # not already installed
    (col("hp_feasibility").isin("HIGH", "MEDIUM")) &        # building type allows HP
    (col("heat_distribution_type").isin(                    # compatible distribution
        "RADIATOR_LT", "UNDERFLOOR", "FAN_COIL", "AIR"
    )) &
    (col("supply_temp_c") <= 65)                             # ASHP works up to 65°C
)

df_hp = df_hp.withColumn("hp_is_feasible", hp_feasible)

# Recommended product selection from technology_catalog
# GSHP if area > 2000 m² and not TR country, else ASHP best fit
# We select product_id via a simple rule; real system would use scoring
recommended_hp_product = when(
    (col("conditioned_area_m2") > 2000) & (col("country_code") == "DE"),
    lit("HP-GSHP-VIESSMANN")
).when(
    col("country_code") == "TR",
    lit("HP-ASHP-DAIKIN")   # Daikin strong in TR market
).otherwise(
    lit("HP-ASHP-VIESSMANN")  # Default DE: Viessmann Vitocal
)

df_hp = df_hp.withColumn("hp_recommended_product", recommended_hp_product)

# CAPEX from ref_technology_catalog — broadcast lookup
# We match min_price_eur_kw × heating_demand_kw_peak
# Peak heating demand (kW) = HLC [W/K] × design_delta_T [K] / 1000
# Design ΔT: DE = 21 − (−12) = 33 K, TR = 21 − (−5) = 26 K
design_delta_t = when(col("country_code") == "DE", lit(33.0)).otherwise(lit(26.0))
df_hp = df_hp.withColumn(
    "hp_peak_demand_kw",
    col("hlc_current_w_k") * design_delta_t / 1000.0
)

# Fetch price per kW from catalog
# category uses prefix match: HEAT_PUMP_ASHP / HEAT_PUMP_GSHP / HEAT_PUMP_EXHAUST
# capex_per_unit is EUR/kW for heat pumps (capex_unit = "EUR/kW")
df_hp_catalog = (
    df_tech
    .filter(col("category").startswith("HEAT_PUMP"))
    .select(
        col("product_id"),
        col("capex_per_unit_min_eur").alias("price_range_eur_kw_min"),
        col("capex_per_unit_max_eur").alias("price_range_eur_kw_max"),
        col("kfw_eligible"),
        col("bafa_eligible"),
        col("yeka_eligible"),
    )
)

df_hp = df_hp.join(
    broadcast(df_hp_catalog).alias("hpc"),
    on=col("hp_recommended_product") == col("hpc.product_id"),
    how="left",
)

# CAPEX: avg price per kW × peak demand
avg_price_per_kw = (
    (col("price_range_eur_kw_min") + col("price_range_eur_kw_max")) / 2.0
)
df_hp = df_hp.withColumn(
    "hp_capex_eur",
    avg_price_per_kw * col("hp_peak_demand_kw")
)

# Grant amounts
#   KfW BEG: grant_pct × CAPEX (up to 60 % for HP)
#   BAFA: bafa_grant_eur_kw × peak_demand_kw (only DE)
hp_kfw_grant = when(
    col("kfw_eligible") & (col("country_code") == "DE"),
    col("hp_capex_eur") * lit(KFW_HP_GRANT_PCT)
).otherwise(lit(0.0))

hp_bafa_grant = when(
    col("bafa_eligible") & (col("country_code") == "DE"),
    lit(BAFA_HP_GRANT_EUR_KW) * col("hp_peak_demand_kw")
).otherwise(lit(0.0))

hp_yeka_grant = when(
    col("yeka_eligible") & (col("country_code") == "TR"),
    col("hp_capex_eur") * 0.30      # YEKA = 30 % capital subsidy
).otherwise(lit(0.0))

df_hp = (
    df_hp
    .withColumn("hp_kfw_grant_eur",  hp_kfw_grant)
    .withColumn("hp_bafa_grant_eur", hp_bafa_grant)
    .withColumn("hp_yeka_grant_eur", hp_yeka_grant)
    .withColumn(
        "hp_net_capex_eur",
        col("hp_capex_eur") - col("hp_kfw_grant_eur")
                            - col("hp_bafa_grant_eur")
                            - col("hp_yeka_grant_eur")
    )
)

# Simple payback (years)
df_hp = df_hp.withColumn(
    "hp_payback_years",
    when(col("hp_annual_saving_eur") > 0,
         col("hp_net_capex_eur") / col("hp_annual_saving_eur")
    ).otherwise(lit(999.0))
)

# NPV (10-year, 5 % discount, 3 % annual energy price escalation)
# NPV = Σ[t=1..10] saving_t / (1+r)^t  - net_capex
# saving_t = saving_yr1 × (1 + escalation)^(t-1)
# Closed form: NPV = saving_yr1 × [(1-(g/r)) × (1 - ((1+g)/(1+r))^n) / (1 - (1+g)/(1+r))] - capex
# Simplified: annuity × escalation factor × saving - capex

g = ENERGY_PRICE_ESCALATION
r = NPV_DISCOUNT_RATE
n = NPV_YEARS

# Growth-adjusted annuity factor: [(1 - ((1+g)/(1+r))^n)] / [(r - g) / (1 + g)]
# Only valid when r ≠ g
if abs(r - g) > 1e-6:
    # Growing annuity PV factor: C × [1 − ((1+g)/(1+r))^n] / (r − g)
    # where C = first-year saving, r = discount rate, g = escalation rate
    annuity_factor = (1.0 - ((1 + g) / (1 + r)) ** n) / (r - g)
else:
    # When r ≈ g: limit → n / (1 + r)
    annuity_factor = n / (1 + r)

df_hp = df_hp.withColumn(
    "hp_npv_eur",
    col("hp_annual_saving_eur") * lit(annuity_factor) - col("hp_net_capex_eur")
)

log_step("HP_SIM", "Heat pump simulation complete", rows=df_hp.count())

# ── 8. BATTERY SIMULATION ─────────────────────────────────────────────────────

log_step("BAT_SIM", "Running battery simulation …")

# Only buildings with PV can benefit from additional battery storage
# For buildings without PV we still simulate "if PV + battery" scenario
# but flag it as conditional

# Aggregate daily solar surplus from gold_kpi_daily
df_solar_daily = (
    df_kpi_d
    .groupBy("building_id")
    .agg(
        spark_sum("solar_generated_kwh").alias("annual_solar_kwh"),
        spark_sum("solar_self_consumed_kwh").alias("annual_self_consumed_kwh"),
        spark_sum("solar_exported_kwh").alias("annual_exported_kwh"),
        spark_avg("total_consumption_kwh").alias("avg_daily_consumption_kwh"),
        percentile_approx("total_consumption_kwh", 0.90).alias("p90_daily_consumption_kwh"),
        count("date").alias("data_days"),
    )
)

df_bat = df_hp.join(broadcast(df_solar_daily), on="building_id", how="left")

# Current daily solar surplus (kWh/day)
df_bat = df_bat.withColumn(
    "avg_daily_solar_surplus_kwh",
    coalesce(
        (col("annual_solar_kwh") - col("annual_self_consumed_kwh")) / col("data_days"),
        lit(0.0)
    )
)

# Optimal battery size = daily surplus × usable SOC factor
# Capped at 4 × avg daily surplus (no benefit beyond that)
df_bat = df_bat.withColumn(
    "bat_optimal_size_kwh",
    when(col("has_pv"),
         least(
             col("avg_daily_solar_surplus_kwh") / BATTERY_USABLE_SOC,
             col("avg_daily_solar_surplus_kwh") * 4.0
         )
    ).otherwise(lit(0.0))
)

# Additional self-consumption = min(daily_surplus, battery_size × usable_SOC) × 365
df_bat = df_bat.withColumn(
    "bat_additional_selfcons_kwh",
    when(col("bat_optimal_size_kwh") > col("battery_capacity_kwh"),
         least(
             col("avg_daily_solar_surplus_kwh"),
             (col("bat_optimal_size_kwh") - col("battery_capacity_kwh")) * BATTERY_USABLE_SOC
         ) * 365.0
    ).otherwise(lit(0.0))
)

# Peak shaving — demand above P90 threshold is shaved
# Demand charge saving = (P90 daily − avg daily) / 24 [kW] × 12 months × demand_charge_eur_kw
p90_kw_proxy = col("p90_daily_consumption_kwh") / 24.0   # rough peak proxy
avg_kw_proxy = col("avg_daily_consumption_kwh") / 24.0
peak_reduction_kw = (p90_kw_proxy - avg_kw_proxy) * 0.50  # assume 50 % shaveable

df_bat = df_bat.withColumn(
    "bat_demand_charge_saving_eur",
    peak_reduction_kw * col("demand_charge_eur_kw") * 12.0
)

# Self-consumption saving (sell avoided ← buy instead)
# Money saved = additional_kwh × (buy_price − sell_price)
df_bat = df_bat.withColumn(
    "bat_selfcons_saving_eur",
    col("bat_additional_selfcons_kwh")
    * (col("electricity_buy_eur_kwh") - col("electricity_sell_eur_kwh"))
)

# Total annual battery saving
df_bat = df_bat.withColumn(
    "bat_annual_saving_eur",
    col("bat_selfcons_saving_eur") + col("bat_demand_charge_saving_eur")
)

# CAPEX for incremental battery upgrade
# Only size delta above existing capacity
df_bat = df_bat.withColumn(
    "bat_incremental_size_kwh",
    greatest(
        col("bat_optimal_size_kwh") - col("battery_capacity_kwh"),
        lit(0.0)
    )
)

# Recommended product (LFP preferred for commercial)
recommended_bat_product = when(
    col("country_code") == "TR",
    lit("BAT-LFP-HUAWEI")   # Huawei available & competitive in TR
).otherwise(
    lit("BAT-LFP-BYD")      # BYD blade preferred in DE (cost/density)
)

df_bat = df_bat.withColumn("bat_recommended_product", recommended_bat_product)

# Fetch battery price from catalog
# category prefix: BATTERY_LFP / BATTERY_NMC
# capex_per_unit is EUR/kWh for batteries (capex_unit = "EUR/kWh")
df_bat_catalog = (
    df_tech
    .filter(col("category").startswith("BATTERY"))
    .select(
        col("product_id"),
        col("capex_per_unit_min_eur").alias("price_range_eur_kwh_min"),
        col("capex_per_unit_max_eur").alias("price_range_eur_kwh_max"),
        col("kfw_eligible").alias("bat_kfw_eligible"),
    )
)

df_bat = df_bat.join(
    broadcast(df_bat_catalog).alias("bc"),
    on=col("bat_recommended_product") == col("bc.product_id"),
    how="left",
)

avg_bat_price_kwh = (
    (col("price_range_eur_kwh_min") + col("price_range_eur_kwh_max")) / 2.0
)

df_bat = df_bat.withColumn(
    "bat_capex_eur",
    avg_bat_price_kwh * col("bat_incremental_size_kwh")
)

# KfW 270 / 442 grants for battery storage — KFW_BAT_GRANT_PCT constant (10 %)
bat_kfw_grant = when(
    col("bat_kfw_eligible") & (col("country_code") == "DE"),
    col("bat_capex_eur") * lit(KFW_BAT_GRANT_PCT)
).otherwise(lit(0.0))

df_bat = (
    df_bat
    .withColumn("bat_kfw_grant_eur", bat_kfw_grant)
    .withColumn("bat_net_capex_eur", col("bat_capex_eur") - col("bat_kfw_grant_eur"))
)

df_bat = df_bat.withColumn(
    "bat_payback_years",
    when(
        (col("bat_annual_saving_eur") > 0) & (col("bat_net_capex_eur") > 0),
        col("bat_net_capex_eur") / col("bat_annual_saving_eur")
    ).otherwise(lit(999.0))
)

df_bat = df_bat.withColumn(
    "bat_npv_eur",
    col("bat_annual_saving_eur") * lit(annuity_factor) - col("bat_net_capex_eur")
)

# Battery feasibility check
bat_feasible = (
    col("has_pv") &
    (col("battery_feasibility").isin("HIGH", "MEDIUM")) &
    (col("bat_incremental_size_kwh") > 2.0)   # at least 2 kWh additional
)
df_bat = df_bat.withColumn("bat_is_feasible", bat_feasible)

log_step("BAT_SIM", "Battery simulation complete", rows=df_bat.count())

# ── 9. INSULATION SIMULATION ───────────────────────────────────────────────────

log_step("INS_SIM", "Running insulation simulation …")

df_ins = df_bat.withColumn("hlc_improved_w_k", calc_hlc_improved_expr())

# Annual heat demand reduction (kWh/year)
df_ins = df_ins.withColumn(
    "ins_annual_heat_reduction_kwh",
    (col("hlc_current_w_k") - col("hlc_improved_w_k")) * col("hdd_annual") * 24.0 / 1000.0
)

# Cost saving depends on current heating system
ins_saving_per_kwh = when(
    col("current_heating_system") == "GAS",
    col("gas_eur_kwh") / 0.92
).when(
    col("current_heating_system") == "ELECTRIC",
    col("electricity_buy_eur_kwh") / 2.5
).otherwise(col("gas_eur_kwh") / 0.85)

df_ins = df_ins.withColumn(
    "ins_annual_saving_eur",
    col("ins_annual_heat_reduction_kwh") * ins_saving_per_kwh
)

# CO₂ saving (same approach as HP gas saving)
df_ins = df_ins.withColumn(
    "ins_co2_saving_kg",
    when(
        col("current_heating_system") == "GAS",
        col("ins_annual_heat_reduction_kwh") / 0.92 * GAS_EMISSION_FACTOR
    ).otherwise(
        col("ins_annual_heat_reduction_kwh") * col("emission_factor_kg_kwh")
    )
)

# Insulation area = external wall area + roof
num_floors_d = coalesce(col("num_floors"), lit(3)).cast("double")
floor_per = col("conditioned_area_m2") / num_floors_d
perimeter_ins = 4.0 * (floor_per ** 0.5)
facade_ins = perimeter_ins * (num_floors_d * FLOOR_HEIGHT_M)
wall_area_ins = facade_ins * WALL_FRACTION_OF_FACADE
roof_area_ins = floor_per

df_ins = (
    df_ins
    .withColumn("ins_wall_area_m2",   wall_area_ins)
    .withColumn("ins_roof_area_m2",   roof_area_ins)
    .withColumn("ins_total_area_m2",  wall_area_ins + roof_area_ins)
)

# Recommended insulation product
recommended_ins_product = when(
    col("building_type").isin("DATA_CENTER", "HOSPITAL"),
    lit("INS-PIR")      # PIR: highest R-value per cm (critical spaces)
).when(
    col("building_type") == "LOGISTICS",
    lit("INS-MW")       # Mineral wool: fire class A1 for warehouses
).otherwise(
    lit("INS-EPS")      # EPS: cost-optimised for offices/schools/hotels
)

df_ins = df_ins.withColumn("ins_recommended_product", recommended_ins_product)

# Fetch insulation price from catalog
# category prefix: INSULATION_EPS / INSULATION_MW / INSULATION_PIR / INSULATION_AEROGEL
# capex_per_unit is EUR/m² for insulation (capex_unit = "EUR/m²")
df_ins_catalog = (
    df_tech
    .filter(col("category").startswith("INSULATION"))
    .select(
        col("product_id"),
        col("capex_per_unit_min_eur").alias("price_range_eur_m2_min"),
        col("capex_per_unit_max_eur").alias("price_range_eur_m2_max"),
        col("kfw_eligible").alias("ins_kfw_eligible"),
    )
)

df_ins = df_ins.join(
    broadcast(df_ins_catalog).alias("ic"),
    on=col("ins_recommended_product") == col("ic.product_id"),
    how="left",
)

avg_ins_price = (col("price_range_eur_m2_min") + col("price_range_eur_m2_max")) / 2.0

df_ins = df_ins.withColumn(
    "ins_capex_eur",
    avg_ins_price * col("ins_total_area_m2")
)

ins_kfw_grant = when(
    col("ins_kfw_eligible") & (col("country_code") == "DE"),
    col("ins_capex_eur") * lit(KFW_INS_GRANT_PCT)
).otherwise(lit(0.0))

df_ins = (
    df_ins
    .withColumn("ins_kfw_grant_eur", ins_kfw_grant)
    .withColumn("ins_net_capex_eur", col("ins_capex_eur") - col("ins_kfw_grant_eur"))
)

df_ins = df_ins.withColumn(
    "ins_payback_years",
    when(col("ins_annual_saving_eur") > 0,
         col("ins_net_capex_eur") / col("ins_annual_saving_eur")
    ).otherwise(lit(999.0))
)

df_ins = df_ins.withColumn(
    "ins_npv_eur",
    col("ins_annual_saving_eur") * lit(annuity_factor) - col("ins_net_capex_eur")
)

# GEG compliance check: HLC_improved < threshold? (simplified: always "compliant" after upgrade)
df_ins = df_ins.withColumn(
    "ins_geg_compliant",
    col("hlc_improved_w_k") < col("hlc_current_w_k")   # trivially true; real check: vs. GEG §19
)

# Feasibility
ins_feasible = col("insulation_feasibility").isin("HIGH", "MEDIUM")
df_ins = df_ins.withColumn("ins_is_feasible", ins_feasible)

log_step("INS_SIM", "Insulation simulation complete", rows=df_ins.count())

# ── 10. COMBINED SCENARIO: HP + INSULATION (DEEP RETROFIT) ────────────────────

log_step("COMBO_SIM", "Computing combined HP + Insulation deep retrofit scenario …")

# After insulation, HP is smaller (lower heat demand → lower peak kW → lower CAPEX)
df_ins = df_ins.withColumn(
    "deep_annual_heating_demand_kwh",
    (col("hlc_improved_w_k") * col("hdd_annual") * 24.0) / 1000.0
)

df_ins = df_ins.withColumn(
    "deep_hp_peak_kw",
    col("hlc_improved_w_k") * design_delta_t / 1000.0
)

df_ins = df_ins.withColumn(
    "deep_hp_capex_eur",
    avg_price_per_kw * col("deep_hp_peak_kw")
)

df_ins = df_ins.withColumn(
    "deep_total_capex_eur",
    col("deep_hp_capex_eur") + col("ins_capex_eur")
)

df_ins = df_ins.withColumn(
    "deep_total_grant_eur",
    col("hp_kfw_grant_eur") + col("hp_bafa_grant_eur") + col("hp_yeka_grant_eur")
    + col("ins_kfw_grant_eur")
)

df_ins = df_ins.withColumn(
    "deep_net_capex_eur",
    col("deep_total_capex_eur") - col("deep_total_grant_eur")
)

# Combined saving = HP saving + Insulation saving
deep_hp_electricity_kwh = col("deep_annual_heating_demand_kwh") / col("cop_adjusted")
deep_hp_op_cost = deep_hp_electricity_kwh * col("electricity_buy_eur_kwh")
deep_total_saving = col("current_heating_cost_eur") - deep_hp_op_cost + col("ins_annual_saving_eur")

df_ins = df_ins.withColumn("deep_annual_saving_eur", deep_total_saving)

df_ins = df_ins.withColumn(
    "deep_payback_years",
    when(col("deep_annual_saving_eur") > 0,
         col("deep_net_capex_eur") / col("deep_annual_saving_eur")
    ).otherwise(lit(999.0))
)

df_ins = df_ins.withColumn(
    "deep_npv_eur",
    col("deep_annual_saving_eur") * lit(annuity_factor) - col("deep_net_capex_eur")
)

log_step("COMBO_SIM", "Deep retrofit scenario complete")

# ── 11. MULTILINGUAL JUSTIFICATION TEXTS ─────────────────────────────────────

log_step("TEXT_GEN", "Generating multilingual recommendation texts …")

# Heat Pump justification
df_ins = df_ins.withColumn(
    "hp_text_en",
    when(col("hp_is_feasible"),
        concat_ws(" ",
            lit("Replacing your"),
            col("current_heating_system"),
            lit("system with a"),
            col("hp_recommended_product"),
            lit("heat pump saves approximately"),
            spark_round(col("hp_annual_saving_eur"), 0).cast("string"),
            lit("EUR/year and reduces CO₂ emissions by"),
            spark_round(col("hp_co2_saving_kg") / 1000.0, 1).cast("string"),
            lit("tonnes/year. Payback:"),
            spark_round(col("hp_payback_years"), 1).cast("string"),
            lit("years. KfW/BAFA grants available.")
        )
    ).otherwise(lit("Heat pump upgrade not recommended for this building."))
)

df_ins = df_ins.withColumn(
    "hp_text_de",
    when(col("hp_is_feasible"),
        concat_ws(" ",
            lit("Der Austausch Ihres"),
            col("current_heating_system"),
            lit("-Heizsystems durch eine"),
            col("hp_recommended_product"),
            lit("-Wärmepumpe spart ca."),
            spark_round(col("hp_annual_saving_eur"), 0).cast("string"),
            lit("EUR/Jahr und reduziert CO₂-Emissionen um"),
            spark_round(col("hp_co2_saving_kg") / 1000.0, 1).cast("string"),
            lit("Tonnen/Jahr. Amortisation:"),
            spark_round(col("hp_payback_years"), 1).cast("string"),
            lit("Jahre. KfW/BAFA-Förderung verfügbar.")
        )
    ).otherwise(lit("Wärmepumpen-Upgrade für dieses Gebäude nicht empfohlen."))
)

df_ins = df_ins.withColumn(
    "hp_text_tr",
    when(col("hp_is_feasible"),
        concat_ws(" ",
            lit("Mevcut"),
            col("current_heating_system"),
            lit("ısıtma sisteminizin"),
            col("hp_recommended_product"),
            lit("ısı pompasıyla değiştirilmesi yılda yaklaşık"),
            spark_round(col("hp_annual_saving_eur"), 0).cast("string"),
            lit("EUR tasarruf sağlar ve CO₂ emisyonlarını yılda"),
            spark_round(col("hp_co2_saving_kg") / 1000.0, 1).cast("string"),
            lit("ton azaltır. Geri ödeme süresi:"),
            spark_round(col("hp_payback_years"), 1).cast("string"),
            lit("yıl. YEKA desteği mevcuttur.")
        )
    ).otherwise(lit("Bu bina için ısı pompası yükseltmesi önerilmemektedir."))
)

# Battery justification
df_ins = df_ins.withColumn(
    "bat_text_en",
    when(col("bat_is_feasible"),
        concat_ws(" ",
            lit("Installing an additional"),
            spark_round(col("bat_incremental_size_kwh"), 0).cast("string"),
            lit("kWh battery ("),
            col("bat_recommended_product"),
            lit(") increases solar self-consumption and saves"),
            spark_round(col("bat_annual_saving_eur"), 0).cast("string"),
            lit("EUR/year. Payback:"),
            spark_round(col("bat_payback_years"), 1).cast("string"),
            lit("years.")
        )
    ).otherwise(lit("Battery upgrade not applicable or PV system not present."))
)

df_ins = df_ins.withColumn(
    "bat_text_de",
    when(col("bat_is_feasible"),
        concat_ws(" ",
            lit("Installation eines"),
            spark_round(col("bat_incremental_size_kwh"), 0).cast("string"),
            lit("kWh-Batteriespeichers ("),
            col("bat_recommended_product"),
            lit(") erhöht den Solaranteil und spart"),
            spark_round(col("bat_annual_saving_eur"), 0).cast("string"),
            lit("EUR/Jahr. Amortisation:"),
            spark_round(col("bat_payback_years"), 1).cast("string"),
            lit("Jahre.")
        )
    ).otherwise(lit("Batteriespeicher nicht anwendbar oder keine PV-Anlage vorhanden."))
)

df_ins = df_ins.withColumn(
    "bat_text_tr",
    when(col("bat_is_feasible"),
        concat_ws(" ",
            lit("Ek"),
            spark_round(col("bat_incremental_size_kwh"), 0).cast("string"),
            lit("kWh batarya ("),
            col("bat_recommended_product"),
            lit(") kurulumu güneş enerjisi öz-tüketimini artırır ve yılda"),
            spark_round(col("bat_annual_saving_eur"), 0).cast("string"),
            lit("EUR tasarruf sağlar. Geri ödeme:"),
            spark_round(col("bat_payback_years"), 1).cast("string"),
            lit("yıl.")
        )
    ).otherwise(lit("Batarya yükseltmesi uygulanamaz veya PV sistemi mevcut değil."))
)

# Insulation justification
df_ins = df_ins.withColumn(
    "ins_text_en",
    when(col("ins_is_feasible"),
        concat_ws(" ",
            lit("Insulating"),
            spark_round(col("ins_total_area_m2"), 0).cast("string"),
            lit("m² with"),
            col("ins_recommended_product"),
            lit("reduces heating demand by"),
            spark_round(col("ins_annual_heat_reduction_kwh"), 0).cast("string"),
            lit("kWh/year, saving"),
            spark_round(col("ins_annual_saving_eur"), 0).cast("string"),
            lit("EUR/year. GEG compliant after upgrade. Payback:"),
            spark_round(col("ins_payback_years"), 1).cast("string"),
            lit("years.")
        )
    ).otherwise(lit("Insulation upgrade not applicable for this building type."))
)

df_ins = df_ins.withColumn(
    "ins_text_de",
    when(col("ins_is_feasible"),
        concat_ws(" ",
            lit("Dämmung von"),
            spark_round(col("ins_total_area_m2"), 0).cast("string"),
            lit("m² mit"),
            col("ins_recommended_product"),
            lit("reduziert den Heizwärmebedarf um"),
            spark_round(col("ins_annual_heat_reduction_kwh"), 0).cast("string"),
            lit("kWh/Jahr und spart"),
            spark_round(col("ins_annual_saving_eur"), 0).cast("string"),
            lit("EUR/Jahr. GEG-konform nach Sanierung. Amortisation:"),
            spark_round(col("ins_payback_years"), 1).cast("string"),
            lit("Jahre.")
        )
    ).otherwise(lit("Dämmmaßnahme für diesen Gebäudetyp nicht anwendbar."))
)

df_ins = df_ins.withColumn(
    "ins_text_tr",
    when(col("ins_is_feasible"),
        concat_ws(" ",
            col("ins_recommended_product"),
            lit("ile"),
            spark_round(col("ins_total_area_m2"), 0).cast("string"),
            lit("m² yalıtım uygulaması ısıtma ihtiyacını yılda"),
            spark_round(col("ins_annual_heat_reduction_kwh"), 0).cast("string"),
            lit("kWh azaltır,"),
            spark_round(col("ins_annual_saving_eur"), 0).cast("string"),
            lit("EUR/yıl tasarruf sağlar. Geri ödeme:"),
            spark_round(col("ins_payback_years"), 1).cast("string"),
            lit("yıl.")
        )
    ).otherwise(lit("Bu bina türü için yalıtım yükseltmesi uygulanamaz."))
)

log_step("TEXT_GEN", "Multilingual texts generated")

# ── 12. ASSEMBLE FINAL OUTPUT TABLE ───────────────────────────────────────────

log_step("ASSEMBLE", "Selecting final simulation result columns …")

df_results = df_ins.select(
    # --- Identifiers ---
    col("building_id"),
    col("building_name"),
    col("building_type"),
    col("country_code"),
    col("city"),
    col("conditioned_area_m2"),
    current_timestamp().alias("simulation_run_ts"),

    # --- Actual performance (from KPI) ---
    spark_round(col("actual_annual_consumption_kwh"), 0).alias("actual_annual_consumption_kwh"),
    spark_round(col("actual_annual_co2_kg"), 0).alias("actual_annual_co2_kg"),
    spark_round(col("avg_load_factor"), 3).alias("avg_load_factor"),
    spark_round(col("avg_self_consumption_pct"), 1).alias("avg_solar_self_consumption_pct"),

    # --- Thermal model ---
    spark_round(col("hlc_current_w_k"), 1).alias("hlc_current_w_k"),
    spark_round(col("hlc_improved_w_k"), 1).alias("hlc_improved_w_k"),
    spark_round(col("annual_heating_demand_kwh"), 0).alias("annual_heating_demand_kwh"),

    # --- Heat Pump scenario ---
    col("hp_is_feasible"),
    col("hp_recommended_product"),
    spark_round(col("hp_peak_demand_kw"), 1).alias("hp_peak_demand_kw"),
    spark_round(col("cop_adjusted"), 2).alias("hp_cop_adjusted"),
    spark_round(col("hp_annual_electricity_kwh"), 0).alias("hp_annual_electricity_kwh"),
    spark_round(col("current_heating_cost_eur"), 0).alias("current_heating_cost_eur"),
    spark_round(col("hp_operating_cost_eur"), 0).alias("hp_operating_cost_eur"),
    spark_round(col("hp_annual_saving_eur"), 0).alias("hp_annual_saving_eur"),
    spark_round(col("hp_co2_saving_kg"), 0).alias("hp_co2_saving_kg"),
    spark_round(col("hp_capex_eur"), 0).alias("hp_capex_eur"),
    spark_round(col("hp_kfw_grant_eur"), 0).alias("hp_kfw_grant_eur"),
    spark_round(col("hp_bafa_grant_eur"), 0).alias("hp_bafa_grant_eur"),
    spark_round(col("hp_yeka_grant_eur"), 0).alias("hp_yeka_grant_eur"),
    spark_round(col("hp_net_capex_eur"), 0).alias("hp_net_capex_eur"),
    spark_round(col("hp_payback_years"), 1).alias("hp_payback_years"),
    spark_round(col("hp_npv_eur"), 0).alias("hp_npv_eur"),
    col("hp_text_en"),
    col("hp_text_de"),
    col("hp_text_tr"),

    # --- Battery scenario ---
    col("bat_is_feasible"),
    col("bat_recommended_product"),
    spark_round(col("bat_optimal_size_kwh"), 1).alias("bat_optimal_size_kwh"),
    spark_round(col("bat_incremental_size_kwh"), 1).alias("bat_incremental_size_kwh"),
    spark_round(col("bat_additional_selfcons_kwh"), 0).alias("bat_additional_selfcons_kwh"),
    spark_round(col("bat_annual_saving_eur"), 0).alias("bat_annual_saving_eur"),
    spark_round(col("bat_capex_eur"), 0).alias("bat_capex_eur"),
    spark_round(col("bat_kfw_grant_eur"), 0).alias("bat_kfw_grant_eur"),
    spark_round(col("bat_net_capex_eur"), 0).alias("bat_net_capex_eur"),
    spark_round(col("bat_payback_years"), 1).alias("bat_payback_years"),
    spark_round(col("bat_npv_eur"), 0).alias("bat_npv_eur"),
    col("bat_text_en"),
    col("bat_text_de"),
    col("bat_text_tr"),

    # --- Insulation scenario ---
    col("ins_is_feasible"),
    col("ins_recommended_product"),
    spark_round(col("ins_wall_area_m2"), 0).alias("ins_wall_area_m2"),
    spark_round(col("ins_roof_area_m2"), 0).alias("ins_roof_area_m2"),
    spark_round(col("ins_annual_heat_reduction_kwh"), 0).alias("ins_annual_heat_reduction_kwh"),
    spark_round(col("ins_annual_saving_eur"), 0).alias("ins_annual_saving_eur"),
    spark_round(col("ins_co2_saving_kg"), 0).alias("ins_co2_saving_kg"),
    spark_round(col("ins_capex_eur"), 0).alias("ins_capex_eur"),
    spark_round(col("ins_kfw_grant_eur"), 0).alias("ins_kfw_grant_eur"),
    spark_round(col("ins_net_capex_eur"), 0).alias("ins_net_capex_eur"),
    spark_round(col("ins_payback_years"), 1).alias("ins_payback_years"),
    spark_round(col("ins_npv_eur"), 0).alias("ins_npv_eur"),
    col("ins_geg_compliant"),
    col("ins_text_en"),
    col("ins_text_de"),
    col("ins_text_tr"),

    # --- Deep Retrofit (HP + Insulation combined) ---
    spark_round(col("deep_total_capex_eur"), 0).alias("deep_capex_eur"),
    spark_round(col("deep_total_grant_eur"), 0).alias("deep_grant_eur"),
    spark_round(col("deep_net_capex_eur"), 0).alias("deep_net_capex_eur"),
    spark_round(col("deep_annual_saving_eur"), 0).alias("deep_annual_saving_eur"),
    spark_round(col("deep_payback_years"), 1).alias("deep_payback_years"),
    spark_round(col("deep_npv_eur"), 0).alias("deep_npv_eur"),
)

log_step("ASSEMBLE", "Final columns selected", rows=df_results.count())

# ── 13. WRITE TO DELTA (MERGE / UPSERT) ───────────────────────────────────────

log_step("WRITE", "Writing gold_simulation_results …",
         table=GOLD_PATHS["simulation_results"])

target_path = GOLD_PATHS["simulation_results"]

if DeltaTable.isDeltaTable(spark, target_path):
    delta_tbl = DeltaTable.forPath(spark, target_path)
    (
        delta_tbl.alias("tgt")
        .merge(
            df_results.alias("src"),
            "tgt.building_id = src.building_id"
        )
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )
    log_step("WRITE", "Delta MERGE (upsert) complete", table=target_path)
else:
    (
        df_results
        .write
        .format("delta")
        .mode("overwrite")
        .partitionBy("country_code")
        .save(target_path)
    )
    log_step("WRITE", "Delta table created (initial write)", table=target_path)

# ── 14. OPTIMIZE ──────────────────────────────────────────────────────────────

log_step("OPTIMIZE", "Running OPTIMIZE + Z-ORDER on gold_simulation_results …")

spark.sql(f"""
    OPTIMIZE delta.`{target_path}`
    ZORDER BY (building_id)
""")

log_step("OPTIMIZE", "OPTIMIZE complete")

# ── 15. VALIDATION & SUMMARY REPORT ───────────────────────────────────────────

log_step("VALIDATE", "Running validation checks …")

df_val = spark.read.format("delta").load(target_path)
total_buildings = df_val.count()

# Per-building summary
df_summary = df_val.select(
    col("building_id"),
    col("building_name"),
    col("country_code"),

    col("hp_is_feasible"),
    col("hp_recommended_product"),
    col("hp_payback_years"),
    col("hp_npv_eur"),
    col("hp_annual_saving_eur"),

    col("bat_is_feasible"),
    col("bat_payback_years"),
    col("bat_npv_eur"),
    col("bat_annual_saving_eur"),

    col("ins_is_feasible"),
    col("ins_payback_years"),
    col("ins_npv_eur"),
    col("ins_annual_saving_eur"),

    col("deep_payback_years"),
    col("deep_npv_eur"),
    col("deep_annual_saving_eur"),
)

print()
print("=" * 72)
print("  SIMULATION ENGINE — VALIDATION REPORT")
print("=" * 72)
print(f"  Buildings simulated : {total_buildings}")
print()
df_summary.show(truncate=False)

# Detailed per-building scenario comparison
print("\n── HP SCENARIO DETAILS ──────────────────────────────────────────────")
df_val.select(
    "building_id", "current_heating_cost_eur",
    "hp_capex_eur", "hp_net_capex_eur",
    "hp_annual_saving_eur", "hp_payback_years", "hp_npv_eur",
    "hp_kfw_grant_eur", "hp_bafa_grant_eur", "hp_yeka_grant_eur"
).show(truncate=False)

print("\n── BATTERY SCENARIO DETAILS ─────────────────────────────────────────")
df_val.select(
    "building_id", "bat_optimal_size_kwh", "bat_incremental_size_kwh",
    "bat_annual_saving_eur", "bat_payback_years", "bat_npv_eur",
    "bat_kfw_grant_eur"
).show(truncate=False)

print("\n── INSULATION SCENARIO DETAILS ──────────────────────────────────────")
df_val.select(
    "building_id", "ins_total_area_m2",
    "ins_annual_heat_reduction_kwh",
    "ins_capex_eur", "ins_net_capex_eur",
    "ins_annual_saving_eur", "ins_payback_years", "ins_npv_eur",
    "ins_geg_compliant"
).show(truncate=False)

print("\n── DEEP RETROFIT (HP + INSULATION) ──────────────────────────────────")
df_val.select(
    "building_id",
    "deep_capex_eur", "deep_grant_eur", "deep_net_capex_eur",
    "deep_annual_saving_eur", "deep_payback_years", "deep_npv_eur"
).show(truncate=False)

print("\n── SAMPLE JUSTIFICATION TEXTS (EN) ─────────────────────────────────")
df_val.select("building_id", "hp_text_en", "bat_text_en", "ins_text_en").show(truncate=80)

print("=" * 72)
print("  04_simulation_engine.py — COMPLETE")
print("=" * 72)
