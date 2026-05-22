"""
battery_simulator.py
====================
Energy Copilot Platform — Page 9: Battery Dispatch Strategies & Financial Simulation
Generates gold-layer CSVs from raw_battery_status.csv + raw_solar_generation.csv + raw_energy_readings.csv

OUTPUT FILES:
  - gold_battery_dispatch.csv       (daily dispatch per building per strategy)
  - gold_battery_simulation.csv     (scenario comparison per building)
  - gold_battery_daily_summary.csv  (aggregated KPIs per building per day)
  - gold_battery_technologies.csv   (already exists — reference only)

ASSUMPTIONS (energy domain, approved 2026-05-08):
  - Solar + Battery systems only (battery without PV excluded)
  - Buildings with battery: B001 (200kWh LFP DE), B003 (800kWh LFP DE), B005 (400kWh NMC DE)
  - Buildings without battery: B004 (PV only, AT), B006 (PV only, NL) → scenario simulation
  - B002 (Istanbul, no PV, no battery) → excluded from Page 9
  - Pricing: country-specific (DE/AT/NL), realistic 2026 market rates
  - Date range: 2023-01-01 → 2026-04-18 (3.5 years = full dataset)
  - Round-trip efficiency: LFP 93-95%, NMC 90-91%
  - SoC bounds: min 10%, max 95% (battery safety limits)
  - Degradation: LFP 1.8%/1000 cycles, NMC 3.5%/1000 cycles
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import warnings
warnings.filterwarnings('ignore')

# ── PATHS ──────────────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))
RAW_BATTERY   = os.path.join(BASE, "raw_battery_status.csv")
RAW_SOLAR     = os.path.join(BASE, "raw_solar_generation.csv")
RAW_ENERGY    = os.path.join(BASE, "raw_energy_readings.csv")

OUT_DISPATCH  = os.path.join(BASE, "gold_battery_dispatch.csv")
OUT_SIMULATION= os.path.join(BASE, "gold_battery_simulation.csv")
OUT_DAILY_SUM = os.path.join(BASE, "gold_battery_daily_summary.csv")

np.random.seed(42)

# ── BUILDING CONFIGURATION ─────────────────────────────────────────────────────
BUILDINGS = {
    "B001": {
        "name": "Berliner Bürogebäude Alpha",
        "country": "DE", "city": "Berlin",
        "battery_id": "B001_BATT_01",
        "battery_tech": "CATL_LFP_200",
        "battery_type": "LFP",
        "capacity_kwh": 200.0,
        "power_kw": 100.0,
        "active_strategy": "self_consumption",
        "pv_capacity_kwp": 120.0,
        "battery_cost_eur": 27600,     # 200kWh × €138/kWh
        "eu_compliant": True,
        "has_battery": True,
        "rte": 0.945,                  # round-trip efficiency
        "degradation_per_1000c": 0.018,
        "install_year": 2022,
    },
    "B003": {
        "name": "Hamburg Logistics Hub Gamma",
        "country": "DE", "city": "Hamburg",
        "battery_id": "B003_BATT_01",
        "battery_tech": "FLUENCE_LFP_800",
        "battery_type": "LFP",
        "capacity_kwh": 800.0,
        "power_kw": 400.0,
        "active_strategy": "peak_shaving",
        "pv_capacity_kwp": 500.0,
        "battery_cost_eur": 104000,    # 800kWh × €130/kWh
        "eu_compliant": True,
        "has_battery": True,
        "rte": 0.950,
        "degradation_per_1000c": 0.015,
        "install_year": 2021,
    },
    "B005": {
        "name": "Frankfurt Klinikum Epsilon",
        "country": "DE", "city": "Frankfurt",
        "battery_id": "B005_BATT_01",
        "battery_tech": "SAMSUNG_NMC_400",
        "battery_type": "NMC",
        "capacity_kwh": 400.0,
        "power_kw": 180.0,
        "active_strategy": "backup",
        "pv_capacity_kwp": 200.0,
        "battery_cost_eur": 50000,     # 400kWh × €125/kWh
        "eu_compliant": False,         # NMC not EU compliant!
        "has_battery": True,
        "rte": 0.905,                  # NMC lower efficiency
        "degradation_per_1000c": 0.035,
        "install_year": 2020,
    },
    # Scenario-only buildings (PV exists, no battery yet → simulation)
    "B004": {
        "name": "Wien Grand Hotel Delta",
        "country": "AT", "city": "Vienna",
        "battery_id": None,
        "battery_tech": "CATL_LFP_200",   # recommended scenario
        "battery_type": "LFP",
        "capacity_kwh": 200.0,
        "power_kw": 100.0,
        "active_strategy": None,           # no active battery
        "pv_capacity_kwp": 80.0,
        "battery_cost_eur": 27600,
        "eu_compliant": True,
        "has_battery": False,
        "rte": 0.945,
        "degradation_per_1000c": 0.018,
        "install_year": None,
    },
    "B006": {
        "name": "Amsterdam Universiteit Zeta",
        "country": "NL", "city": "Amsterdam",
        "battery_id": None,
        "battery_tech": "SUNGROW_LFP_150",  # recommended scenario
        "battery_type": "LFP",
        "capacity_kwh": 150.0,
        "power_kw": 75.0,
        "active_strategy": None,
        "pv_capacity_kwp": 150.0,
        "battery_cost_eur": 19800,           # 150kWh × €132/kWh
        "eu_compliant": True,
        "has_battery": False,
        "rte": 0.935,
        "degradation_per_1000c": 0.020,
        "install_year": None,
    },
}

# ── COUNTRY PRICING (EUR/kWh, 2026 market rates) ───────────────────────────────
# Sources: EPEX Spot (DE), EXAA (AT), APX (NL) — typical 2026 day-ahead averages
PRICING = {
    "DE": {
        "offpeak_eur_kwh": 0.062,   # 23:00-06:00 — typical German off-peak
        "midpeak_eur_kwh": 0.182,   # 06:00-17:00 and 21:00-23:00
        "peak_eur_kwh":    0.285,   # 17:00-21:00 — EPEX day-ahead peak
        "demand_charge_eur_kw_month": 13.50,  # German commercial demand tariff
        "feed_in_tariff_eur_kwh": 0.082,      # EEG 2023 reduced rate
        "co2_intensity_g_kwh": 380,           # German grid 2026 (improving)
    },
    "AT": {
        "offpeak_eur_kwh": 0.055,
        "midpeak_eur_kwh": 0.165,
        "peak_eur_kwh":    0.248,
        "demand_charge_eur_kw_month": 11.20,
        "feed_in_tariff_eur_kwh": 0.075,
        "co2_intensity_g_kwh": 210,           # Austria — high hydro share
    },
    "NL": {
        "offpeak_eur_kwh": 0.071,
        "midpeak_eur_kwh": 0.195,
        "peak_eur_kwh":    0.302,
        "demand_charge_eur_kw_month": 14.80,
        "feed_in_tariff_eur_kwh": 0.095,
        "co2_intensity_g_kwh": 320,
    },
}

# ── DISPATCH STRATEGY PARAMETERS ───────────────────────────────────────────────
STRATEGIES = {
    "self_consumption": {
        "soc_target_morning": 0.20,    # morning reserve (20%)
        "soc_max_charge": 0.95,
        "soc_min_discharge": 0.10,
        "charge_window": (6, 12),      # PV peak window
        "discharge_window": (17, 23),  # evening peak
        "grid_charge_enabled": False,  # only charge from PV
        "description": "Maximize PV self-consumption. Discharge during evening peak.",
    },
    "peak_shaving": {
        "soc_target_morning": 0.80,    # need full charge for peak shaving
        "soc_max_charge": 0.95,
        "soc_min_discharge": 0.10,
        "charge_window": (23, 6),      # overnight cheap grid charge
        "discharge_window": (17, 21),  # peak demand hours only
        "grid_charge_enabled": True,
        "description": "Reduce demand charge. Charge off-peak (grid), discharge peak.",
    },
    "tou": {
        "soc_target_morning": 0.30,
        "soc_max_charge": 0.95,
        "soc_min_discharge": 0.10,
        "charge_window": (23, 6),      # cheapest hours
        "discharge_window": (17, 21),  # most expensive hours
        "grid_charge_enabled": True,
        "description": "Maximize arbitrage. Buy cheap, sell/avoid expensive grid.",
    },
    "backup": {
        "soc_target_morning": 0.65,    # maintain high reserve
        "soc_max_charge": 0.95,
        "soc_min_discharge": 0.55,     # never below 55% (backup reserve)
        "charge_window": (6, 16),      # daytime PV + grid top-up
        "discharge_window": (17, 22),
        "grid_charge_enabled": True,
        "description": "Maintain emergency backup reserve. Opportunistic PV use.",
    },
}

# ── SEASONAL PV FACTORS (simplified monthly profile) ──────────────────────────
# Factor × pv_capacity_kwp → daily kWh generation (per kWp)
PV_MONTHLY_KWPH_PER_KWP = {
    1: 1.1, 2: 1.8, 3: 3.2, 4: 4.5, 5: 5.2, 6: 5.6,
    7: 5.4, 8: 4.8, 9: 3.6, 10: 2.2, 11: 1.3, 12: 0.9
}  # average daily sun hours equivalent (Central Europe)


def get_daily_price_profile(country: str, date: datetime) -> dict:
    """Return pricing for the given country, adjusted for weekends and season."""
    p = PRICING[country]
    is_weekend = date.weekday() >= 5
    is_winter = date.month in [11, 12, 1, 2, 3]

    # Weekend: lower peak price (less commercial demand)
    peak_mod = 0.85 if is_weekend else 1.0
    # Winter: higher overall prices in EU (heating demand)
    season_mod = 1.12 if is_winter else 1.0

    return {
        "offpeak": p["offpeak_eur_kwh"] * season_mod,
        "midpeak": p["midpeak_eur_kwh"] * season_mod * peak_mod,
        "peak":    p["peak_eur_kwh"] * season_mod * peak_mod,
        "demand":  p["demand_charge_eur_kw_month"],
        "feed_in": p["feed_in_tariff_eur_kwh"],
        "co2_g_kwh": p["co2_intensity_g_kwh"],
    }


def simulate_daily_dispatch(
    building_id: str, cfg: dict, strategy: str,
    date: datetime, pv_daily_kwh: float, consumption_daily_kwh: float,
    soc_start: float, cumulative_cycles: float
) -> dict:
    """
    Simulate one day of battery dispatch for a given strategy.
    Returns a dict matching gold_battery_dispatch schema.

    Energy balance (simplified daily model):
    - PV generation → first covers building load, surplus → battery charge
    - Battery → discharges to cover load deficit during discharge window
    - Grid → covers any remaining deficit
    """
    capacity  = cfg["capacity_kwh"]
    power_kw  = cfg["power_kw"]
    rte       = cfg["rte"]                     # round-trip efficiency
    strat_cfg = STRATEGIES[strategy]
    country   = cfg["country"]
    prices    = get_daily_price_profile(country, date)

    # SoC bounds
    soc_min  = strat_cfg["soc_min_discharge"]
    soc_max  = strat_cfg["soc_max_charge"]
    soc_curr = soc_start

    # ── PV → Load → Battery logic (daily simplified) ──────────────────────────
    # Step 1: PV directly covers load
    pv_to_load = min(pv_daily_kwh, consumption_daily_kwh)
    pv_surplus = max(0, pv_daily_kwh - pv_to_load)
    load_deficit = max(0, consumption_daily_kwh - pv_to_load)

    # Step 2: PV surplus charges battery
    pv_charge_available = pv_surplus
    soc_headroom = (soc_max - soc_curr) * capacity  # kWh space
    pv_charge_kwh = min(pv_charge_available, soc_headroom, power_kw * 8.0)  # max 8h charge
    pv_charge_kwh = max(0, pv_charge_kwh)

    soc_after_pv_charge = soc_curr + (pv_charge_kwh * np.sqrt(rte)) / capacity

    # Step 3: Strategy-specific grid charge (peak_shaving / tou / backup)
    grid_charge_kwh = 0.0
    if strat_cfg["grid_charge_enabled"] and strategy != "self_consumption":
        # Grid charge to reach target SoC
        target_soc = strat_cfg["soc_target_morning"] if date.hour < 6 else strat_cfg["soc_max_charge"]
        target_soc = min(target_soc, soc_max)
        if soc_after_pv_charge < target_soc:
            grid_charge_needed = (target_soc - soc_after_pv_charge) * capacity
            # Scale by available off-peak hours (6h overnight window typical)
            grid_charge_kwh = min(grid_charge_needed, power_kw * 6.0)
            grid_charge_kwh = max(0, grid_charge_kwh)
        soc_after_grid = soc_after_pv_charge + (grid_charge_kwh * np.sqrt(rte)) / capacity
    else:
        soc_after_grid = soc_after_pv_charge

    soc_after_grid = min(soc_after_grid, soc_max)

    # Step 4: Discharge to cover load deficit during discharge window
    discharge_window_hours = 4.0  # simplified: 4h peak discharge window
    max_discharge = min(
        (soc_after_grid - soc_min) * capacity,
        power_kw * discharge_window_hours
    )
    discharge_kwh = min(load_deficit, max(0, max_discharge))
    # Backup strategy: protect reserve
    if strategy == "backup":
        reserve_kwh = soc_min * capacity
        available_for_discharge = max(0, (soc_after_grid * capacity) - reserve_kwh)
        discharge_kwh = min(discharge_kwh, available_for_discharge)

    discharge_kwh = max(0, discharge_kwh)
    soc_end = soc_after_grid - (discharge_kwh / (capacity * np.sqrt(rte)))
    soc_end = max(soc_min, min(soc_max, soc_end))

    # ── Add natural variation (±8% noise) ──────────────────────────────────────
    noise = np.random.normal(1.0, 0.08)
    discharge_kwh = max(0, discharge_kwh * noise)
    grid_charge_kwh = max(0, grid_charge_kwh * np.random.normal(1.0, 0.05))

    total_charge_kwh = pv_charge_kwh + grid_charge_kwh

    # ── Cycle counting ─────────────────────────────────────────────────────────
    # 1 full cycle = 100% DOD. Count partial cycles by energy throughput
    cycle_depth = discharge_kwh / capacity
    new_cycles = cycle_depth
    total_cycles = cumulative_cycles + new_cycles

    # ── Financial calculations ─────────────────────────────────────────────────
    # Cost avoided = discharge replaces grid purchase at peak price
    cost_avoided_eur = discharge_kwh * prices["peak"]

    # Grid charge cost (at off-peak rate)
    grid_charge_cost_eur = grid_charge_kwh * prices["offpeak"]

    # Net daily savings = avoided peak - grid charge cost
    net_savings_eur = cost_avoided_eur - grid_charge_cost_eur

    # For peak_shaving: add demand charge reduction benefit
    # Demand charge reduction = power dispatched × monthly demand rate / 30
    demand_reduction_eur = 0.0
    if strategy == "peak_shaving":
        peak_power_dispatched_kw = min(discharge_kwh / 4.0, power_kw)  # avg over 4h
        demand_reduction_eur = (peak_power_dispatched_kw * prices["demand"]) / 30.0
        net_savings_eur += demand_reduction_eur

    # CO₂ avoided: discharge replaces grid electricity
    co2_avoided_kg = (discharge_kwh * prices["co2_g_kwh"]) / 1000.0

    # ── Battery health ─────────────────────────────────────────────────────────
    years_elapsed = max(0.1, (date - datetime(cfg["install_year"] or 2022, 1, 1)).days / 365.0)
    degradation = (total_cycles / 1000.0) * cfg["degradation_per_1000c"]
    health_score = max(0.60, 1.0 - degradation)  # floor at 60% (EOL threshold)

    # Round-trip efficiency (degrades slightly over time)
    rte_current = rte * (0.97 + 0.03 * health_score)  # slight efficiency loss with age

    return {
        "date": date.strftime("%Y-%m-%d"),
        "building_id": building_id,
        "building_name": cfg["name"],
        "country": cfg["country"],
        "battery_id": cfg["battery_id"] or f"{building_id}_BATT_SIM",
        "battery_tech": cfg["battery_tech"],
        "battery_type": cfg["battery_type"],
        "eu_compliant": cfg["eu_compliant"],
        "strategy": strategy,
        "capacity_kwh": capacity,
        "pv_capacity_kwp": cfg["pv_capacity_kwp"],
        "pv_generation_kwh": round(pv_daily_kwh, 2),
        "pv_to_load_kwh": round(pv_to_load, 2),
        "pv_charge_kwh": round(pv_charge_kwh, 2),
        "grid_charge_kwh": round(grid_charge_kwh, 2),
        "charge_kwh": round(total_charge_kwh, 2),
        "discharge_kwh": round(discharge_kwh, 2),
        "soc_start_percent": round(soc_start * 100, 1),
        "soc_end_percent": round(soc_end * 100, 1),
        "soc_target_percent": round(strat_cfg["soc_target_morning"] * 100, 1),
        "round_trip_efficiency_percent": round(rte_current * 100, 2),
        "cycle_depth_percent": round(cycle_depth * 100, 2),
        "cumulative_cycles": round(total_cycles, 3),
        "cost_avoided_eur": round(max(0, cost_avoided_eur), 4),
        "grid_charge_cost_eur": round(grid_charge_cost_eur, 4),
        "demand_reduction_eur": round(demand_reduction_eur, 4),
        "net_savings_eur": round(net_savings_eur, 4),
        "co2_avoided_kg": round(co2_avoided_kg, 4),
        "battery_health_percent": round(health_score * 100, 2),
        "grid_price_peak_eur_kwh": round(prices["peak"], 4),
        "grid_price_offpeak_eur_kwh": round(prices["offpeak"], 4),
        "is_simulated": not cfg["has_battery"],
    }


def generate_dispatch(buildings: dict) -> tuple:
    """Generate full dispatch table for all buildings, all strategies, full date range."""
    print("Loading raw data...")
    df_solar = pd.read_csv(RAW_SOLAR, parse_dates=["timestamp_utc"])
    df_energy = pd.read_csv(RAW_ENERGY, parse_dates=["timestamp_utc"])

    # Daily aggregates from raw data
    df_solar["date"] = df_solar["timestamp_utc"].dt.date
    df_energy["date"] = df_energy["timestamp_utc"].dt.date

    solar_daily = (
        df_solar.groupby(["building_id", "date"])["generated_raw"]
        .sum()
        .reset_index()
        .rename(columns={"generated_raw": "pv_kwh"})
    )
    # raw_energy_readings uses raw_value (kWh per 15-min interval)
    energy_col = (
        "consumption_kwh" if "consumption_kwh" in df_energy.columns
        else "total_consumption_kwh" if "total_consumption_kwh" in df_energy.columns
        else "raw_value"
    )
    energy_daily = (
        df_energy.groupby(["building_id", "date"])[energy_col]
        .sum()
        .reset_index()
        .rename(columns={energy_col: "consumption_kwh"})
    )

    # Determine full date range
    all_dates = sorted(solar_daily["date"].unique())
    print(f"  Date range: {all_dates[0]} → {all_dates[-1]} ({len(all_dates)} days)")

    dispatch_rows = []
    strategies_per_building = {
        "B001": ["self_consumption", "peak_shaving", "tou"],
        "B003": ["peak_shaving", "self_consumption", "tou"],
        "B005": ["backup", "self_consumption", "tou"],
        "B004": ["self_consumption", "tou"],      # simulation scenarios
        "B006": ["self_consumption", "tou"],
    }

    for bld_id, cfg in buildings.items():
        print(f"  Simulating {bld_id} ({cfg['name']})...")
        strategies = strategies_per_building.get(bld_id, ["self_consumption"])

        # Get solar data for this building
        bld_solar = solar_daily[solar_daily["building_id"] == bld_id].copy()
        bld_energy = energy_daily[energy_daily["building_id"] == bld_id].copy()
        bld_solar["date_dt"] = pd.to_datetime(bld_solar["date"])
        bld_energy["date_dt"] = pd.to_datetime(bld_energy["date"])

        for strategy in strategies:
            soc = STRATEGIES[strategy]["soc_target_morning"]  # starting SoC
            cumulative_cycles = 0.0

            for date in all_dates:
                date_dt = pd.Timestamp(date)
                month = date_dt.month

                # Get daily PV generation (from raw data or seasonal estimate)
                solar_row = bld_solar[bld_solar["date_dt"].dt.date == date]
                if len(solar_row) > 0:
                    pv_kwh = float(solar_row["pv_kwh"].values[0])
                else:
                    # Estimate from capacity + monthly solar factor
                    sun_hours = PV_MONTHLY_KWPH_PER_KWP[month]
                    pv_kwh = cfg["pv_capacity_kwp"] * sun_hours * np.random.normal(1.0, 0.15)
                    pv_kwh = max(0, pv_kwh)

                # Get daily consumption
                energy_row = bld_energy[bld_energy["date_dt"].dt.date == date]
                if len(energy_row) > 0:
                    consumption_kwh = float(energy_row["consumption_kwh"].values[0])
                else:
                    # Estimate: typical commercial profile (kWh/m²/day)
                    consumption_kwh = (cfg["pv_capacity_kwp"] * 3.5) * np.random.normal(1.0, 0.10)

                row = simulate_daily_dispatch(
                    bld_id, cfg, strategy, date_dt,
                    pv_kwh, consumption_kwh, soc, cumulative_cycles
                )
                soc = row["soc_end_percent"] / 100.0  # carry SoC forward
                cumulative_cycles = row["cumulative_cycles"]
                dispatch_rows.append(row)

    df_dispatch = pd.DataFrame(dispatch_rows)
    print(f"  Total dispatch rows: {len(df_dispatch):,}")
    return df_dispatch


def generate_simulation_scenarios(dispatch_df: pd.DataFrame, buildings: dict) -> pd.DataFrame:
    """
    Generate scenario comparison table (gold_battery_simulation).
    For each building × strategy, compute 10-year NPV, IRR, payback.
    """
    DISCOUNT_RATE = 0.05   # 5% discount rate (EU standard for energy investments)
    INFLATION_RATE = 0.03  # 3% energy price inflation per year
    LIFESPAN_YR    = 10    # NPV horizon

    rows = []

    # Get annualized metrics from dispatch
    # Use last 12 months for annualization to get stable estimate
    dispatch_df["date_dt"] = pd.to_datetime(dispatch_df["date"])
    cutoff = dispatch_df["date_dt"].max() - pd.DateOffset(years=1)
    recent = dispatch_df[dispatch_df["date_dt"] >= cutoff]

    for bld_id, cfg in buildings.items():
        bld_recent = recent[recent["building_id"] == bld_id]
        if bld_recent.empty:
            continue

        strategies = bld_recent["strategy"].unique()
        for strategy in strategies:
            strat_data = bld_recent[bld_recent["strategy"] == strategy]
            if strat_data.empty:
                continue

            # Annualize from recent 12-month data
            n_days = len(strat_data)
            if n_days < 10:
                continue

            annual_savings = (strat_data["net_savings_eur"].sum() / n_days) * 365
            annual_co2_kg  = (strat_data["co2_avoided_kg"].sum() / n_days) * 365
            avg_rte        = strat_data["round_trip_efficiency_percent"].mean()
            avg_health     = strat_data["battery_health_percent"].mean()
            total_cycles   = strat_data["cumulative_cycles"].max()

            battery_cost = cfg["battery_cost_eur"]
            # Add installation cost (~8% of hardware)
            total_capex = battery_cost * 1.08

            # Simple payback
            payback_years = total_capex / max(annual_savings, 1)

            # NPV (10-year, inflation-adjusted cash flows)
            cash_flows = [-total_capex]
            for yr in range(1, LIFESPAN_YR + 1):
                inflated_savings = annual_savings * ((1 + INFLATION_RATE) ** yr)
                cash_flows.append(inflated_savings)
            # Add salvage value (20% of battery cost at end of life)
            cash_flows[-1] += battery_cost * 0.20

            npv = sum(cf / ((1 + DISCOUNT_RATE) ** i) for i, cf in enumerate(cash_flows))

            # IRR (Newton-Raphson approximation)
            irr = None
            if annual_savings > 0:
                # Rough IRR estimate: savings growth covers CAPEX over lifespan
                irr_guess = annual_savings / total_capex
                for _ in range(50):
                    f  = sum(cf / ((1 + irr_guess) ** i) for i, cf in enumerate(cash_flows))
                    df = sum(-i * cf / ((1 + irr_guess) ** (i + 1)) for i, cf in enumerate(cash_flows))
                    if abs(df) < 1e-10:
                        break
                    irr_guess -= f / df
                    irr_guess = max(-0.5, min(2.0, irr_guess))
                irr = irr_guess * 100

            # EU compliance affects comparison score (penalty for non-compliant)
            eu_penalty = 0 if cfg["eu_compliant"] else 15

            # Comparison score (0-100): composite of IRR, payback, CO₂, EU compliance
            irr_score   = min(40, max(0, (irr or 0) * 200))       # IRR 0-20% → 0-40pts
            payback_sc  = max(0, 30 - (payback_years - 3) * 2)    # <3yr=30, >18yr=0
            co2_score   = min(20, annual_co2_kg / 500)             # up to 20pts
            eu_score    = 10 if cfg["eu_compliant"] else 0         # 10pts bonus
            comparison_score = max(0, min(100,
                irr_score + payback_sc + co2_score + eu_score - eu_penalty
            ))

            # Strategy label
            strategy_labels = {
                "self_consumption": "Self-Consumption",
                "peak_shaving": "Peak-Shaving",
                "tou": "Time-of-Use (ToU)",
                "backup": "Backup + Opportunistic",
            }

            scenario_id = f"{bld_id}_{strategy.upper()[:3]}_{int(cfg['capacity_kwh'])}kWh"

            rows.append({
                "scenario_id": scenario_id,
                "building_id": bld_id,
                "building_name": cfg["name"],
                "country": cfg["country"],
                "battery_tech": cfg["battery_tech"],
                "battery_type": cfg["battery_type"],
                "eu_compliant": cfg["eu_compliant"],
                "battery_capacity_kwh": cfg["capacity_kwh"],
                "battery_power_kw": cfg["power_kw"],
                "pv_capacity_kwp": cfg["pv_capacity_kwp"],
                "battery_cost_eur": battery_cost,
                "total_capex_eur": round(total_capex, 0),
                "battery_lifespan_years": 12 if cfg["battery_type"] == "LFP" else 8,
                "strategy": strategy,
                "strategy_label": strategy_labels.get(strategy, strategy),
                "is_active_strategy": (cfg["active_strategy"] == strategy),
                "is_simulated": not cfg["has_battery"],
                "annual_savings_eur": round(annual_savings, 2),
                "annual_co2_avoided_kg": round(annual_co2_kg, 2),
                "payback_years": round(min(payback_years, 25), 2),
                "npv_10yr_eur": round(npv, 2),
                "irr_percent": round(irr or 0, 2),
                "avg_round_trip_efficiency_pct": round(avg_rte, 2),
                "avg_battery_health_pct": round(avg_health, 2),
                "total_cycles_to_date": round(total_cycles, 1),
                "comparison_score": round(comparison_score, 1),
            })

    df_sim = pd.DataFrame(rows)
    df_sim.sort_values(["building_id", "comparison_score"], ascending=[True, False], inplace=True)
    print(f"  Simulation scenarios: {len(df_sim)}")
    return df_sim


def generate_daily_summary(dispatch_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate gold_battery_daily_summary:
    Best strategy per building per day + cumulative KPIs.
    """
    dispatch_df["date_dt"] = pd.to_datetime(dispatch_df["date"])

    # For each building+date, pick the best-performing strategy (by net_savings)
    best_per_day = (
        dispatch_df
        .sort_values("net_savings_eur", ascending=False)
        .groupby(["date", "building_id"])
        .first()
        .reset_index()
    )

    # Cumulative totals per building
    best_per_day.sort_values(["building_id", "date"], inplace=True)
    best_per_day["total_cycles_cumulative"] = best_per_day.groupby("building_id")["cycle_depth_percent"].cumsum() / 100.0
    best_per_day["total_cost_avoided_eur"]  = best_per_day.groupby("building_id")["net_savings_eur"].cumsum()
    best_per_day["total_co2_avoided_kg"]    = best_per_day.groupby("building_id")["co2_avoided_kg"].cumsum()

    summary = best_per_day[[
        "date", "building_id", "building_name", "country",
        "strategy", "battery_type", "eu_compliant",
        "soc_start_percent", "soc_end_percent",
        "charge_kwh", "discharge_kwh", "pv_generation_kwh",
        "round_trip_efficiency_percent",
        "net_savings_eur", "co2_avoided_kg", "battery_health_percent",
        "total_cycles_cumulative", "total_cost_avoided_eur", "total_co2_avoided_kg",
    ]].copy()

    summary.rename(columns={
        "soc_start_percent": "avg_soc_start_percent",
        "soc_end_percent":   "avg_soc_end_percent",
        "net_savings_eur":   "daily_net_savings_eur",
        "co2_avoided_kg":    "daily_co2_avoided_kg",
    }, inplace=True)

    print(f"  Daily summary rows: {len(summary):,}")
    return summary


# ── MAIN ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 65)
    print("Energy Copilot Platform — Battery Simulator")
    print("=" * 65)

    print("\n[1/4] Generating dispatch data (all buildings, full date range)...")
    df_dispatch = generate_dispatch(BUILDINGS)
    df_dispatch.to_csv(OUT_DISPATCH, index=False)
    print(f"  ✅ Saved: {OUT_DISPATCH} ({len(df_dispatch):,} rows)")

    print("\n[2/4] Generating simulation scenarios...")
    df_simulation = generate_simulation_scenarios(df_dispatch, BUILDINGS)
    df_simulation.to_csv(OUT_SIMULATION, index=False)
    print(f"  ✅ Saved: {OUT_SIMULATION} ({len(df_simulation):,} rows)")

    print("\n[3/4] Generating daily summary...")
    df_summary = generate_daily_summary(df_dispatch)
    df_summary.to_csv(OUT_DAILY_SUM, index=False)
    print(f"  ✅ Saved: {OUT_DAILY_SUM} ({len(df_summary):,} rows)")

    print("\n[4/4] Validation checks:")
    print(f"  Buildings in dispatch: {df_dispatch['building_id'].nunique()}")
    print(f"  Strategies in dispatch: {df_dispatch['strategy'].nunique()}")
    print(f"  Date range: {df_dispatch['date'].min()} → {df_dispatch['date'].max()}")
    print(f"  Avg daily savings (€): {df_dispatch['net_savings_eur'].mean():.2f}")
    print(f"  Avg battery health (%): {df_dispatch['battery_health_percent'].mean():.1f}")
    print(f"  EU compliant rows: {df_dispatch['eu_compliant'].sum():,} / {len(df_dispatch):,}")
    print("\n  Scenarios by building:")
    for _, row in df_simulation.iterrows():
        eu_flag = "EU OK" if bool(row["eu_compliant"]) else "NON-EU"
        score = int(row["comparison_score"])
        payback = row["payback_years"]
        irr = row["irr_percent"]
        label = row["strategy_label"]
        bid = row["building_id"]
        lbl = str(label).ljust(28)
        line = "    " + str(bid) + " | " + lbl + " | Payback: " + str(round(payback, 1)) + "yr | IRR: " + str(round(irr, 1)) + "% | Score: " + str(score) + "/100 | " + str(eu_flag)
        print(line)

    print("\nBattery simulation complete.")
    print("=" * 65)
