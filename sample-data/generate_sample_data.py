"""
Sample Data Generator v3 — Energy Copilot Platform
=====================================================
3+ Years : 2023-01-01 → 2026-04-18 (15-min intervals)
6 Buildings: Office, Retail, Logistics, Hotel, Healthcare, Education
6 Countries: DE, TR, AT, NL

WHY 3+ YEARS?
  Power BI time-intelligence (PREVIOUSYEAR, SAMEPERIODLASTYEAR) requires at
  least 2 full calendar years of DATA to show a non-blank prior-year value.
  Since today is 2026, the report's "current year" context is 2025/2026.
  Without 2025 data, all KPI cards with PY targets show BLANK.

  Timeline logic:
    2023 → reference / baseline year
    2024 → prior year (PY for 2025 comparisons)
    2025 → last full year (current year in most views)
    Q1 2026 → partial current year (most recent data)

  When user opens Power BI with no date filter:
    • Date table max = 2026-04-18 → "current" = Q1 2026
    • PREVIOUSYEAR = 2025 → data exists → KPI cards show values ✅
    • YoY = 2025 vs 2024 → both exist → trend lines work ✅

Building design philosophy:
  Each building type has ONE representative example — covering a spectrum
  from "underperforming" to "best practice", so customers can benchmark
  themselves against the portfolio. The CRREM pathway (gold_crrem_pathway)
  provides the sector-level ideal target.

Building summary:
  B001 Office      Berlin   DE  2005 — Modern: heat pump + PV + battery. Reference performer.
  B002 Retail      Istanbul TR  1998 — Old: gas heating, no PV. Underperformer (high EUI).
  B003 Logistics   Hamburg  DE  2018 — Large: PV + battery + gas backup. Best in class.
  B004 Hotel       Vienna   AT  2008 — Mid: gas + partial PV + backup gen. Typical hotel.
  B005 Healthcare  Frankfurt DE  2000 — Hospital: gas + critical diesel gen + PV. High baseline.
  B006 Education   Amsterdam NL  1985 — University: gas + old HVAC. Seasonal demand.

Injected anomalies (for demo):
  B001 Aug (all years)   : Solar panel soiling → PV yield drops to 72% PR
  B001 Nov 2023          : Battery over-discharge (SoC < 10% for several days)
  B001 Feb 2025          : Heat pump fault → COP drops to 1.8 for 2 weeks
  B002 Mar 15 (all years): Consumption spike +80% (equipment malfunction, recurring)
  B002 Jul–Aug 2023      : Extended AC surge (Istanbul heat wave 2023)
  B002 Jun–Jul 2025      : Istanbul heat wave 2025 (repeat pattern, +35% cooling)
  B003 Dec 5-7 2023      : Peak shaving failure → 2-day consumption spike
  B003 Nov 2025          : Battery degradation → peak shaving efficiency drops 20%
  B004 Jan 8-10 2024     : Heating system fault → 3-day heating energy spike
  B004 Mar 2026          : Boiler replacement → consumption reduces ~12% from Mar 15
  B005 Every Wed night   : After-hours baseline anomaly (lights/equipment left on, ongoing)
  B005 Sep 2025          : New MRI wing → baseline consumption increases +18%
  B006 Jul 2023          : Heating valve fault → unexpected heat load during summer vacation
  B006 Jan 2026          : Insulation upgrade completed → heating consumption -15%

Usage:
    python generate_sample_data.py

Output:  sample-data/
    building_master.csv
    raw_energy_readings.csv      (~1.4M rows)
    raw_solar_generation.csv     (~580K rows, PV buildings only)
    raw_battery_status.csv       (~350K rows, battery buildings only)
    raw_weather_data.csv         (~1.4M rows)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import math

SEED = 42
np.random.seed(SEED)

START_DATE = datetime(2023, 1, 1)
END_DATE   = datetime(2026, 4, 18, 23, 45)   # Extended: covers 2023→2024→2025→Q1-2026
FREQ_MIN   = 15
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Climate Parameters ────────────────────────────────────────────────────────
# base_temp  : annual mean outdoor temperature (°C)
# seasonal   : amplitude of seasonal variation (°C, cosine curve)
# daily      : amplitude of daily variation (°C, cosine curve)
# noise_sd   : random noise standard deviation (°C)
# solar_peak : max solar irradiance W/m² (summer noon, clear sky)
# solar_base : min solar irradiance W/m² (winter noon, clear sky)

CITY_CLIMATE = {
    # latitude: used for seasonal sunrise/sunset calculation
    # solar_peak: max clear-sky irradiance W/m² (summer noon)
    # solar_base: min clear-sky irradiance W/m² (winter noon)
    "Berlin":    {"base_temp": 10.0, "seasonal": 9.0,  "daily": 3.0, "noise_sd": 1.5, "solar_peak": 750, "solar_base": 200, "latitude": 52.5},
    "Hamburg":   {"base_temp": 10.0, "seasonal": 8.5,  "daily": 2.8, "noise_sd": 1.6, "solar_peak": 700, "solar_base": 180, "latitude": 53.6},
    "Istanbul":  {"base_temp": 14.0, "seasonal": 8.0,  "daily": 2.5, "noise_sd": 1.8, "solar_peak": 950, "solar_base": 350, "latitude": 41.0},
    "Vienna":    {"base_temp": 11.0, "seasonal": 9.5,  "daily": 3.5, "noise_sd": 1.4, "solar_peak": 850, "solar_base": 250, "latitude": 48.2},
    "Frankfurt": {"base_temp": 11.0, "seasonal": 9.0,  "daily": 3.2, "noise_sd": 1.5, "solar_peak": 780, "solar_base": 210, "latitude": 50.1},
    "Amsterdam": {"base_temp": 10.0, "seasonal": 7.5,  "daily": 2.5, "noise_sd": 1.7, "solar_peak": 700, "solar_base": 170, "latitude": 52.4},
}

# Monthly cloud cover probability per city (Jan–Dec, index 0–11)
# Source: Climatological averages — fraction of intervals that are cloud-reduced
# Higher values → more cloud cover → less solar generation
CITY_CLOUD_PROB = {
    # Berlin: Cfb climate — very cloudy winters, moderate summers
    "Berlin":    [0.74, 0.71, 0.65, 0.58, 0.55, 0.50, 0.45, 0.44, 0.54, 0.65, 0.72, 0.75],
    # Hamburg: even cloudier than Berlin (coastal, North Sea influence)
    "Hamburg":   [0.76, 0.73, 0.68, 0.61, 0.58, 0.53, 0.48, 0.47, 0.57, 0.67, 0.74, 0.77],
    # Istanbul: Csa climate — sunny summers, moderately cloudy winters
    "Istanbul":  [0.62, 0.60, 0.55, 0.47, 0.36, 0.25, 0.15, 0.15, 0.28, 0.44, 0.57, 0.65],
    # Vienna: Cfb — similar to Berlin, slightly less coastal influence
    "Vienna":    [0.71, 0.68, 0.61, 0.55, 0.52, 0.47, 0.42, 0.40, 0.50, 0.61, 0.68, 0.72],
    # Frankfurt: Cfb — similar to Berlin
    "Frankfurt": [0.72, 0.70, 0.64, 0.58, 0.55, 0.50, 0.45, 0.44, 0.54, 0.64, 0.70, 0.73],
    # Amsterdam: Cfb — cloudiest of the set (marine west coast, Atlantic)
    "Amsterdam": [0.76, 0.74, 0.68, 0.62, 0.59, 0.54, 0.50, 0.49, 0.58, 0.67, 0.74, 0.77],
}

# ── Building Master Data ──────────────────────────────────────────────────────

BUILDINGS = [
    # -------------------------------------------------------------------------
    # B001 — Office, Berlin DE, 2005, Modern best-practice
    # EUI target: ~85 kWh/m²/yr | Scope 2 low (heat pump), Scope 1 = 0
    # -------------------------------------------------------------------------
    {
        "building_id": "B001", "organization_id": "ORG001",
        "building_name": "Berliner Bürogebäude Alpha",
        "country_code": "DE", "city": "Berlin", "climate_zone": "Cfb",
        "gross_floor_area_m2": 5200.0, "conditioned_area_m2": 4800.0,
        "year_built": 2005, "building_type": "Office",
        "max_occupants": 260,   # 1 person / 20m² open-plan office (EN 15232 reference)
        "subscription_tier": "Monitor",
        "has_pv": True,  "pv_capacity_kwp": 120.0,
        "roof_area_m2": 1100.0, "roof_orientation": "S", "roof_tilt_deg": 30.0,
        "has_battery": True, "battery_capacity_kwh": 200.0,
        "battery_technology": "LFP", "battery_strategy": "self_consumption",
        "has_heat_pump": True, "heat_pump_cop_rated": 3.8, "heat_pump_capacity_kw": 90.0,
        "has_hvac_traditional": False,
        "has_gas_heating": False, "has_diesel_generator": False,
        "primary_hvac_system": "heat_pump",
        "has_ev_charging": False, "has_led_lighting": True,
        "wall_u_value": 0.28, "roof_u_value": 0.18, "floor_u_value": 0.30,
        "window_u_value": 1.1, "window_to_wall_ratio": 0.35,
        "air_tightness_ach": 1.2, "thermal_mass_level": "MEDIUM",
        "insulation_year": 2015, "has_thermal_bridge": False,
        "energy_certificate": "B", "energy_certificate_year": 2022,
        "regulatory_profile_id": "REG_DE", "iso50001_certified": False,
    },
    # -------------------------------------------------------------------------
    # B002 — Retail, Istanbul TR, 1998, Underperformer
    # EUI target: ~210 kWh/m²/yr | High Scope 1 (gas), Scope 2 medium (TR grid)
    # -------------------------------------------------------------------------
    {
        "building_id": "B002", "organization_id": "ORG002",
        "building_name": "Istanbul Ticaret Merkezi Beta",
        "country_code": "TR", "city": "Istanbul", "climate_zone": "Csa",
        "gross_floor_area_m2": 8500.0, "conditioned_area_m2": 7200.0,
        "year_built": 1998, "building_type": "Retail",
        "max_occupants": 700,   # 1 person / ~10m² retail floor (staff + peak visitors)
        "subscription_tier": "Insight",
        "has_pv": False, "pv_capacity_kwp": None,
        "roof_area_m2": 2000.0, "roof_orientation": None, "roof_tilt_deg": None,
        "has_battery": False, "battery_capacity_kwh": None,
        "battery_technology": None, "battery_strategy": None,
        "has_heat_pump": False, "heat_pump_cop_rated": None, "heat_pump_capacity_kw": None,
        "has_hvac_traditional": True,
        "has_gas_heating": True, "has_diesel_generator": False,
        "primary_hvac_system": "gas_boiler",
        "has_ev_charging": False, "has_led_lighting": False,
        "wall_u_value": 0.80, "roof_u_value": 0.55, "floor_u_value": 0.70,
        "window_u_value": 2.8, "window_to_wall_ratio": 0.25,
        "air_tightness_ach": 3.5, "thermal_mass_level": "HIGH",
        "insulation_year": None, "has_thermal_bridge": True,
        "energy_certificate": "E", "energy_certificate_year": 2018,
        "regulatory_profile_id": "REG_TR", "iso50001_certified": False,
    },
    # -------------------------------------------------------------------------
    # B003 — Logistics, Hamburg DE, 2018, Large + best-in-class
    # EUI target: ~65 kWh/m²/yr | Low Scope 1 (some gas), high self-generation
    # -------------------------------------------------------------------------
    {
        "building_id": "B003", "organization_id": "ORG001",
        "building_name": "Hamburg Logistics Hub Gamma",
        "country_code": "DE", "city": "Hamburg", "climate_zone": "Cfb",
        "gross_floor_area_m2": 12000.0, "conditioned_area_m2": 10000.0,
        "year_built": 2018, "building_type": "Logistics",
        "max_occupants": 80,    # warehouse: ~1 person / 150m² operational staff
        "subscription_tier": "Copilot",
        "has_pv": True,  "pv_capacity_kwp": 500.0,
        "roof_area_m2": 6000.0, "roof_orientation": "S", "roof_tilt_deg": 10.0,
        "has_battery": True, "battery_capacity_kwh": 800.0,
        "battery_technology": "LFP", "battery_strategy": "peak_shaving",
        "has_heat_pump": False, "heat_pump_cop_rated": None, "heat_pump_capacity_kw": None,
        "has_hvac_traditional": True,
        "has_gas_heating": True, "has_diesel_generator": True,
        "primary_hvac_system": "gas_boiler",
        "has_ev_charging": True, "has_led_lighting": True,
        "wall_u_value": 0.22, "roof_u_value": 0.15, "floor_u_value": 0.25,
        "window_u_value": 0.9, "window_to_wall_ratio": 0.10,
        "air_tightness_ach": 0.8, "thermal_mass_level": "LOW",
        "insulation_year": 2018, "has_thermal_bridge": False,
        "energy_certificate": "A", "energy_certificate_year": 2023,
        "regulatory_profile_id": "REG_DE", "iso50001_certified": True,
    },
    # -------------------------------------------------------------------------
    # B004 — Hotel, Vienna AT, 2008, Mid-range typical
    # EUI target: ~280 kWh/m²/yr | High Scope 1 (gas, hot water), backup diesel
    # 24/7 occupancy, breakfast and dinner peaks
    # -------------------------------------------------------------------------
    {
        "building_id": "B004", "organization_id": "ORG003",
        "building_name": "Wien Grand Hotel Delta",
        "country_code": "AT", "city": "Vienna", "climate_zone": "Cfb",
        "gross_floor_area_m2": 7800.0, "conditioned_area_m2": 6500.0,
        "year_built": 2008, "building_type": "Hotel",
        "max_occupants": 230,   # ~130 rooms × 1.5 guests + 45 staff (4-star mid-size hotel)
        "subscription_tier": "Insight",
        "has_pv": True,  "pv_capacity_kwp": 80.0,
        "roof_area_m2": 900.0, "roof_orientation": "S", "roof_tilt_deg": 20.0,
        "has_battery": False, "battery_capacity_kwh": None,
        "battery_technology": None, "battery_strategy": None,
        "has_heat_pump": False, "heat_pump_cop_rated": None, "heat_pump_capacity_kw": None,
        "has_hvac_traditional": True,
        "has_gas_heating": False, "has_diesel_generator": True,
        "primary_hvac_system": "district",
        "has_ev_charging": True, "has_led_lighting": True,
        "wall_u_value": 0.45, "roof_u_value": 0.30, "floor_u_value": 0.45,
        "window_u_value": 1.8, "window_to_wall_ratio": 0.30,
        "air_tightness_ach": 2.0, "thermal_mass_level": "MEDIUM",
        "insulation_year": 2012, "has_thermal_bridge": True,
        "energy_certificate": "C", "energy_certificate_year": 2021,
        "regulatory_profile_id": "REG_AT", "iso50001_certified": False,
    },
    # -------------------------------------------------------------------------
    # B005 — Healthcare, Frankfurt DE, 2000 (refurb 2015)
    # EUI target: ~380 kWh/m²/yr | Very high baseline, critical loads 24/7
    # Diesel generator mandatory for life safety
    # -------------------------------------------------------------------------
    {
        "building_id": "B005", "organization_id": "ORG004",
        "building_name": "Frankfurt Klinikum Epsilon",
        "country_code": "DE", "city": "Frankfurt", "climate_zone": "Cfb",
        "gross_floor_area_m2": 15000.0, "conditioned_area_m2": 13000.0,
        "year_built": 2000, "building_type": "Healthcare",
        "max_occupants": 750,   # 1 per 20m²: ~500 staff (nurses, doctors, admin) + ~250 patients
        "subscription_tier": "Copilot",
        "has_pv": True,  "pv_capacity_kwp": 200.0,
        "roof_area_m2": 3000.0, "roof_orientation": "S", "roof_tilt_deg": 15.0,
        "has_battery": True, "battery_capacity_kwh": 400.0,
        "battery_technology": "NMC", "battery_strategy": "backup",
        "has_heat_pump": False, "heat_pump_cop_rated": None, "heat_pump_capacity_kw": None,
        "has_hvac_traditional": True,
        "has_gas_heating": True, "has_diesel_generator": True,
        "primary_hvac_system": "gas_boiler",
        "has_ev_charging": False, "has_led_lighting": True,
        "wall_u_value": 0.50, "roof_u_value": 0.35, "floor_u_value": 0.50,
        "window_u_value": 1.5, "window_to_wall_ratio": 0.20,
        "air_tightness_ach": 1.5, "thermal_mass_level": "HIGH",
        "insulation_year": 2015, "has_thermal_bridge": True,
        "energy_certificate": "C", "energy_certificate_year": 2020,
        "regulatory_profile_id": "REG_DE", "iso50001_certified": True,
    },
    # -------------------------------------------------------------------------
    # B006 — Education, Amsterdam NL, 1985, Old building high gas dependency
    # EUI target: ~125 kWh/m²/yr | High Scope 1, seasonal demand (term vs vacation)
    # University: empty July–Aug, Christmas. Full Mon–Fri during term.
    # -------------------------------------------------------------------------
    {
        "building_id": "B006", "organization_id": "ORG005",
        "building_name": "Amsterdam Universiteit Zeta",
        "country_code": "NL", "city": "Amsterdam", "climate_zone": "Cfb",
        "gross_floor_area_m2": 9500.0, "conditioned_area_m2": 8000.0,
        "year_built": 1985, "building_type": "Education",
        "max_occupants": 950,   # 1 per 10m²: ~800 students + 150 academic/admin staff (peak lecture)
        "subscription_tier": "Monitor",
        "has_pv": True,  "pv_capacity_kwp": 150.0,
        "roof_area_m2": 2200.0, "roof_orientation": "S", "roof_tilt_deg": 25.0,
        "has_battery": False, "battery_capacity_kwh": None,
        "battery_technology": None, "battery_strategy": None,
        "has_heat_pump": False, "heat_pump_cop_rated": None, "heat_pump_capacity_kw": None,
        "has_hvac_traditional": True,
        "has_gas_heating": False, "has_diesel_generator": False,
        "primary_hvac_system": "vrf",
        "has_ev_charging": False, "has_led_lighting": False,
        "wall_u_value": 0.90, "roof_u_value": 0.60, "floor_u_value": 0.80,
        "window_u_value": 2.5, "window_to_wall_ratio": 0.30,
        "air_tightness_ach": 4.0, "thermal_mass_level": "HIGH",
        "insulation_year": None, "has_thermal_bridge": True,
        "energy_certificate": "D", "energy_certificate_year": 2019,
        "regulatory_profile_id": "REG_NL", "iso50001_certified": False,
    },
]

# ── Vectorized Helper Functions ───────────────────────────────────────────────

def make_timestamps():
    """Generate pandas DatetimeIndex for the full 2-year period."""
    return pd.date_range(start=START_DATE, end=END_DATE, freq=f"{FREQ_MIN}min")


def compute_temperature(ts, city):
    """Vectorized outdoor temperature array for a city."""
    p = CITY_CLIMATE[city]
    doy  = ts.dayofyear.values
    hour = ts.hour.values
    n    = len(ts)
    seasonal = -p["seasonal"] * np.cos(2 * np.pi * doy  / 365)
    daily    = -p["daily"]    * np.cos(2 * np.pi * hour / 24)
    noise    = np.random.normal(0, p["noise_sd"], n)
    return p["base_temp"] + seasonal + daily + noise


def compute_irradiance(ts, city):
    """Vectorized solar irradiance array (W/m²). Zero at night.

    v4 fix: seasonal sunrise/sunset via astronomical formula + city-specific
    monthly cloud probability. Previously used fixed 16-hour daytime year-round
    which overstated winter generation by 2-3x for northern cities.
    """
    p       = CITY_CLIMATE[city]
    lat_rad = math.radians(p["latitude"])
    doy     = ts.dayofyear.values
    hour    = ts.hour.values
    month   = ts.month.values
    n       = len(ts)

    # ── Astronomical sunrise / sunset ────────────────────────────────────────
    # Solar declination (radians) — Spencer formula approximation
    dec_rad = np.radians(-23.45 * np.cos(np.radians(360.0 * (doy + 10) / 365.0)))

    # Hour angle at sunrise/sunset: cos(ha) = -tan(lat)*tan(dec)
    cos_ha = np.clip(-np.tan(lat_rad) * np.tan(dec_rad), -1.0, 1.0)
    ha_deg = np.degrees(np.arccos(cos_ha))   # 0–90° → half-day length in degrees
    ha_hrs = ha_deg / 15.0                   # convert to hours (15°/hr)

    sunrise = 12.0 - ha_hrs    # e.g. Berlin Dec ≈ 8:10, Jun ≈ 4:40
    sunset  = 12.0 + ha_hrs    # e.g. Berlin Dec ≈ 15:50, Jun ≈ 21:20
    day_len = np.maximum(sunset - sunrise, 0.5)   # guard against polar edge cases

    # ── Clear-sky irradiance (seasonal peak × sine arc during daylight) ──────
    # solar_peak: summer noon clear-sky irradiance W/m²
    # solar_base: winter noon clear-sky irradiance W/m²
    peak = (p["solar_peak"] - p["solar_base"]) * np.sin(np.pi * doy / 365.0) + p["solar_base"]

    # Midpoint of 15-min interval for irradiance calculation
    hour_mid = hour + 0.125
    daytime  = (hour_mid >= sunrise) & (hour_mid <= sunset)

    irr = np.where(
        daytime,
        peak * np.sin(np.pi * (hour_mid - sunrise) / day_len),
        0.0,
    )
    irr = np.maximum(0.0, irr + np.random.normal(0, 25, n))

    # ── City-specific monthly cloud probability ───────────────────────────────
    # Berlin/Hamburg winters: ~75% of intervals are cloud-reduced (realistic)
    # Istanbul summers: ~15% (Mediterranean dry season)
    cloud_probs   = CITY_CLOUD_PROB[city]
    cloud_prob_arr = np.array([cloud_probs[m - 1] for m in month])
    cloud_mask    = np.random.random(n) < cloud_prob_arr
    # Cloudy interval: irradiance reduced to 5–40% of clear-sky value
    irr = np.where(cloud_mask, irr * np.random.uniform(0.05, 0.40, n), irr)

    return np.maximum(0.0, irr)


def occupancy_mask(ts, building_type):
    """Vectorized occupancy boolean array."""
    hour  = ts.hour.values
    wday  = ts.dayofweek.values   # Mon=0, Sun=6
    month = ts.month.values
    day   = ts.day.values

    if building_type == "Office":
        return (wday < 5) & (hour >= 7) & (hour < 20)

    elif building_type == "Retail":
        return (wday < 6) & (hour >= 9) & (hour < 22)

    elif building_type == "Logistics":
        return (hour >= 6) & (hour < 22)

    elif building_type == "Hotel":
        # Hotels never truly empty — even at night there are guests
        return np.ones(len(ts), dtype=bool)

    elif building_type == "Healthcare":
        # Hospitals: always occupied (life-safety systems, patients, shifts)
        return np.ones(len(ts), dtype=bool)

    elif building_type == "Education":
        # Summer vacation: July + August → minimal occupancy
        is_summer   = (month >= 7) & (month <= 8)
        # Christmas break: Dec 22 – Jan 8
        is_xmas     = ((month == 12) & (day >= 22)) | ((month == 1) & (day <= 8))
        is_vacation  = is_summer | is_xmas
        return (~is_vacation) & (wday < 5) & (hour >= 8) & (hour < 18)

    return np.ones(len(ts), dtype=bool)


# ── Energy Consumption Generator ─────────────────────────────────────────────

def generate_energy_readings(building, ts):
    """Generate synthetic energy consumption. Returns DataFrame."""
    bid   = building["building_id"]
    btype = building["building_type"]
    city  = building["city"]
    area  = building["conditioned_area_m2"]
    n     = len(ts)

    # Building-type energy density (kW per m² during occupied hours)
    # Sources: Typical European commercial building benchmarks
    density = {
        "Office":     0.020,   # 20 W/m²  ~ EUI 85  kWh/m²/yr
        "Retail":     0.040,   # 40 W/m²  ~ EUI 210 kWh/m²/yr (heavy lighting, HVAC)
        "Logistics":  0.022,   # 22 W/m²  ~ EUI 65  kWh/m²/yr
        "Hotel":      0.035,   # 35 W/m²  ~ EUI 280 kWh/m²/yr (hot water, kitchen, 24/7)
        "Healthcare": 0.055,   # 55 W/m²  ~ EUI 380 kWh/m²/yr (medical equip, sterile HVAC)
        "Education":  0.018,   # 18 W/m²  ~ EUI 125 kWh/m²/yr
    }[btype]

    base_kw  = area * 0.003  # Always-on load: ~3 W/m²
    peak_kw  = area * density

    temp    = compute_temperature(ts, city)
    occ     = occupancy_mask(ts, btype)

    # Demand: occupied vs. unoccupied
    noise_f = np.random.uniform(0.85, 1.15, n)
    demand  = np.where(occ, peak_kw * noise_f, base_kw * np.random.uniform(0.90, 1.10, n))

    # Temperature-driven HVAC adjustment
    heat_eff = np.where((temp < 15) & occ, 1 + (15 - temp) * 0.015, 1.0)
    cool_eff = np.where((temp > 25) & occ, 1 + (temp - 25) * 0.013, 1.0)
    demand   = demand * heat_eff * cool_eff

    # Hotel-specific load shaping (breakfast, dinner, night)
    if btype == "Hotel":
        hour = ts.hour.values
        demand = np.where((hour >= 7)  & (hour <= 10), demand * 1.45, demand)  # breakfast
        demand = np.where((hour >= 18) & (hour <= 22), demand * 1.30, demand)  # dinner
        demand = np.where((hour >= 0)  & (hour <  6),  demand * 0.55, demand)  # deep night

    # Healthcare: day shift (7-19) vs. night (reduced but still high)
    if btype == "Healthcare":
        hour = ts.hour.values
        demand = np.where((hour >= 7) & (hour < 19), demand * 1.20, demand * 0.82)

    # Education: vacation minimal load (security, servers, heating control)
    if btype == "Education":
        month = ts.month.values
        day   = ts.day.values
        is_vac = ((month >= 7) & (month <= 8)) | \
                 ((month == 12) & (day >= 22)) | ((month == 1) & (day <= 8))
        demand = np.where(is_vac, base_kw * 0.35 * np.random.uniform(0.9, 1.1, n), demand)

    # ── Anomaly injection ─────────────────────────────────────────────────────

    year  = ts.year.values
    month = ts.month.values
    day   = ts.day.values
    hour  = ts.hour.values
    wday_arr = ts.dayofweek.values

    if bid == "B001":
        # Anomaly 1: Heat pump fault Feb 2025 — COP drops, consumption spikes
        # (HP works harder to compensate reduced efficiency in cold weather)
        hp_fault = (year == 2025) & (month == 2) & (day >= 5) & (day <= 20)
        demand   = np.where(hp_fault, demand * 1.35, demand)

    if bid == "B002":
        # Anomaly 1: March 15 consumption spike (equipment fault, recurring every year)
        spike_mask = (month == 3) & (day == 15) & (hour >= 9) & (hour < 14)
        demand = np.where(spike_mask, demand * 1.85, demand)
        # Anomaly 2: Istanbul 2023 heatwave — extended AC surge July–Aug
        heatwave_2023 = (year == 2023) & (month >= 7) & (month <= 8) & \
                        (hour >= 11) & (hour <= 18)
        demand = np.where(heatwave_2023, demand * 1.40, demand)
        # Anomaly 3: Istanbul 2025 heat wave (June–July, slightly milder)
        heatwave_2025 = (year == 2025) & (month >= 6) & (month <= 7) & \
                        (hour >= 11) & (hour <= 19)
        demand = np.where(heatwave_2025, demand * 1.35, demand)

    if bid == "B003":
        # Anomaly 1: Peak shaving failure Dec 5-7 2023 (battery unavailable)
        pf_fail = (year == 2023) & (month == 12) & (day >= 5) & (day <= 7) & \
                  (hour >= 8) & (hour <= 18)
        demand = np.where(pf_fail, demand * 1.65, demand)
        # Anomaly 2: Battery degradation Nov 2025 — peak shaving 20% less effective
        # (battery capacity reduced to ~80%, peak demand rises during discharge window)
        batt_deg = (year == 2025) & (month == 11) & (hour >= 8) & (hour <= 18)
        demand   = np.where(batt_deg, demand * 1.20, demand)

    if bid == "B004":
        # Anomaly 1: Heating system fault Jan 8-10 2024 (boiler overshoot)
        hf = (year == 2024) & (month == 1) & (day >= 8) & (day <= 10)
        demand = np.where(hf, demand * 1.75, demand)
        # Anomaly 2: Boiler replacement Mar 15 2026 — consumption drops 12% ongoing
        # (new condensing boiler replaces old unit, improved efficiency)
        boiler_new = (year == 2026) & (month >= 3) & (day >= 15)
        demand     = np.where(boiler_new, demand * 0.88, demand)

    if bid == "B005":
        # Anomaly 1: After-hours waste — Wednesday nights (ongoing, every year)
        ah = (wday_arr == 2) & (hour >= 21) & (hour <= 23)
        demand = np.where(ah, demand * 1.60, demand)
        # Anomaly 2: New MRI wing Sep 2025 — baseline consumption increases 18%
        # (new high-power medical imaging equipment added permanently)
        mri_wing = ((year == 2025) & (month >= 9)) | (year == 2026)
        demand   = np.where(mri_wing, demand * 1.18, demand)

    if bid == "B006":
        # Anomaly 1: Heating valve fault July 2023 — heating ON during summer vacation
        hv = (year == 2023) & (month == 7) & (day >= 5) & (day <= 20)
        demand = np.where(hv, demand * 1.50, demand)
        # Anomaly 2: Insulation upgrade completed Jan 2026 — heating load reduces 15%
        # (walls and roof retrofitted to GEG 2023 standard over Dec 2025 shutdown)
        insulation = (year == 2026)
        demand     = np.where(insulation, demand * 0.85, demand)

    demand = np.maximum(0.0, demand)
    consumption_kwh = np.round(demand * (FREQ_MIN / 60), 3)

    return pd.DataFrame({
        "ingestion_id":   [f"{bid}-E-{i:08d}" for i in range(n)],
        "building_id":    bid,
        "source_system":  "SmartMeter",
        "sensor_id":      f"{bid}_MAIN_METER",
        "timestamp_utc":  ts.strftime("%Y-%m-%d %H:%M:%S"),
        "raw_value":      consumption_kwh,
        "raw_unit":       "kWh",
        "ingested_at":    (ts + pd.Timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M:%S"),
        "tier":           building["subscription_tier"],
    })


# ── Solar Generation ──────────────────────────────────────────────────────────

def generate_solar_generation(building, ts):
    """Generate synthetic PV solar generation. Returns DataFrame or None.

    v4 fix: occupancy-based export ratio replaces flat random 20-45%.
    When building is occupied: load is high → little export (5-22%).
    When building is empty (nights, weekends, vacation): surplus → high export (55-88%).
    Buildings with battery storage export even less during occupied hours (battery absorbs).
    """
    if not building.get("has_pv"):
        return None

    bid      = building["building_id"]
    kwp      = building["pv_capacity_kwp"]
    city     = building["city"]
    btype    = building["building_type"]
    has_batt = building.get("has_battery", False)
    n        = len(ts)

    irr  = compute_irradiance(ts, city)
    pr   = 0.80  # Standard Performance Ratio

    # Panel soiling: August → PR drops to 0.72 (applies to all buildings)
    month_arr = ts.month.values
    soiling   = (month_arr == 8)
    pr_arr    = np.where(soiling, 0.72, pr)

    generated = np.round(
        kwp * (irr / 1000) * pr_arr * (FREQ_MIN / 60) + np.random.normal(0, 0.002, n),
        3
    )
    generated = np.maximum(0.0, generated)

    # ── Occupancy-based export ratio ─────────────────────────────────────────
    # Occupied hours: building load absorbs most of the solar → low export
    # Unoccupied hours: low load, surplus sent to grid (or battery if present)
    occ = occupancy_mask(ts, btype)

    if has_batt:
        # Battery-equipped buildings: during occupied+solar hours, battery charges
        # → export is very low even off-hours (battery absorbs first)
        export_ratio = np.where(
            occ,
            np.random.uniform(0.03, 0.15, n),   # occupied: 3-15% (battery + load)
            np.random.uniform(0.30, 0.65, n),   # unoccupied: 30-65% (battery may be full)
        )
    else:
        # No battery: off-hours solar goes directly to grid
        export_ratio = np.where(
            occ,
            np.random.uniform(0.05, 0.22, n),   # occupied: 5-22%
            np.random.uniform(0.60, 0.90, n),   # unoccupied: 60-90%
        )

    exported = np.round(np.minimum(generated, generated * export_ratio), 3)

    return pd.DataFrame({
        "ingestion_id":  [f"{bid}-S-{i:08d}" for i in range(n)],
        "building_id":   bid,
        "timestamp_utc": ts.strftime("%Y-%m-%d %H:%M:%S"),
        "generated_raw": generated,
        "exported_raw":  exported,
        "raw_unit":      "kWh",
        "inverter_id":   f"{bid}_INV_01",
        "ingested_at":   (ts + pd.Timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M:%S"),
    })


# ── Battery Status ────────────────────────────────────────────────────────────

def generate_battery_status(building, ts):
    """Generate synthetic battery state of charge. Returns DataFrame or None."""
    if not building.get("has_battery"):
        return None

    bid      = building["building_id"]
    capacity = building["battery_capacity_kwh"]
    strategy = building["battery_strategy"]
    n        = len(ts)

    hour_arr  = ts.hour.values
    month_arr = ts.month.values
    day_arr   = ts.day.values
    year_arr  = ts.year.values

    # Simulate SoC as a time-series (sequential)
    soc    = np.full(n, 50.0)
    charge = np.zeros(n)
    disch  = np.zeros(n)

    current_soc = 30.0   # start low so first-day charge is visible
    for i in range(n):
        h = hour_arr[i]
        if strategy == "self_consumption":
            # Charge when solar is producing (10-16h) — delta sized for 200kWh battery
            # Target: daily swing 30%→85% and back → avg (30+85)/2 ≈ 58%
            # 24 charge intervals × avg 2.3% = +55% → hits ~85%
            # 16 discharge intervals × avg 2.8% = -45% → back to ~40%
            if 10 <= h <= 16:
                delta = np.random.uniform(1.5, 3.5)   # was 0.5-2.0 → too small
                current_soc = min(90.0, current_soc + delta)
                charge[i]   = np.random.uniform(10, 40)
            elif 18 <= h <= 22:
                delta = np.random.uniform(1.5, 4.0)   # was 0.5-1.5 → too small
                current_soc = max(15.0, current_soc - delta)
                disch[i]    = np.random.uniform(10, 35)
        elif strategy in ("peak_shaving", "backup"):
            # Charge overnight from grid (0-6h) when tariff is low
            # Discharge during peak hours (8-18h) to shave demand peaks
            if 0 <= h <= 6:
                delta = np.random.uniform(3.0, 6.0)   # was 1.0-3.0
                current_soc = min(90.0, current_soc + delta)
                charge[i]   = np.random.uniform(30, 80)
            elif 8 <= h <= 18:
                delta = np.random.uniform(1.0, 2.5)   # was 0.3-1.0
                current_soc = max(20.0, current_soc - delta)
                disch[i]    = np.random.uniform(20, 60)

        # B001 Nov 2023: battery over-discharge event
        if bid == "B001" and year_arr[i] == 2023 and month_arr[i] == 11 and day_arr[i] in range(5, 10):
            current_soc = max(4.0, current_soc - 3.5)

        soc[i] = current_soc

    soc_noisy = np.round(soc + np.random.normal(0, 0.3, n), 1)

    return pd.DataFrame({
        "ingestion_id":         [f"{bid}-B-{i:08d}" for i in range(n)],
        "building_id":          bid,
        "timestamp_utc":        ts.strftime("%Y-%m-%d %H:%M:%S"),
        "soc_raw":              soc_noisy,
        "charge_power_raw":     np.round(charge, 2),
        "discharge_power_raw":  np.round(disch,  2),
        "battery_id":           f"{bid}_BATT_01",
        "ingested_at":          (ts + pd.Timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M:%S"),
    })


# ── Weather Data ──────────────────────────────────────────────────────────────

def generate_weather_data(building, ts):
    """Generate synthetic weather data. Returns DataFrame."""
    bid  = building["building_id"]
    city = building["city"]
    n    = len(ts)

    temp = compute_temperature(ts, city)
    irr  = compute_irradiance(ts, city)
    hum  = np.round(np.random.uniform(40, 85, n), 1)
    wind = np.round(np.maximum(0, np.random.normal(4, 2, n)), 1)

    # HDD / CDD per 15-min interval (base 15°C for heating, 22°C for cooling)
    hdd_int = np.maximum(0, 15 - temp) * (FREQ_MIN / (60 * 24))
    cdd_int = np.maximum(0, temp - 22) * (FREQ_MIN / (60 * 24))

    source_map = {"DE": "DWD", "TR": "MGM", "AT": "ZAMG", "NL": "KNMI"}
    src = source_map.get(building["country_code"], "DWD")

    return pd.DataFrame({
        "ingestion_id":      [f"{bid}-W-{i:08d}" for i in range(n)],
        "building_id":       bid,
        "timestamp_utc":     ts.strftime("%Y-%m-%d %H:%M:%S"),
        "temperature_raw":   np.round(temp, 1),
        "humidity_raw":      hum,
        "solar_irradiance":  np.round(irr, 1),
        "wind_speed_raw":    wind,
        "hdd_interval":      np.round(hdd_int, 5),
        "cdd_interval":      np.round(cdd_int, 5),
        "source_api":        src,
        "ingested_at":       (ts + pd.Timedelta(minutes=3)).strftime("%Y-%m-%d %H:%M:%S"),
    })


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Energy Copilot Platform — Sample Data Generator v4")
    print(f"Period : {START_DATE.date()} → {END_DATE.date()}")
    print(f"         {(END_DATE - START_DATE).days} days  |  ~{(END_DATE - START_DATE).days / 365.25:.1f} years")
    print(f"Buildings: {len(BUILDINGS)}")
    print("=" * 60)
    print("Fixes (v4): seasonal daylight hours, city cloud probability,")
    print("            occupancy-based export ratio, realistic battery cycling")

    ts = make_timestamps()
    print(f"\nTimestamps : {len(ts):,} intervals (15-min)")

    all_energy, all_solar, all_battery, all_weather = [], [], [], []

    for b in BUILDINGS:
        bid = b["building_id"]
        print(f"\n[{bid}] {b['building_name']} ({b['building_type']}, {b['city']} {b['country_code']})")

        print("  → Energy readings...", end=" ", flush=True)
        energy = generate_energy_readings(b, ts)
        all_energy.append(energy)
        print(f"{len(energy):,} rows")

        solar = generate_solar_generation(b, ts)
        if solar is not None:
            all_solar.append(solar)
            print(f"  → Solar generation... {len(solar):,} rows")

        battery = generate_battery_status(b, ts)
        if battery is not None:
            all_battery.append(battery)
            print(f"  → Battery status...   {len(battery):,} rows")

        print("  → Weather data...", end=" ", flush=True)
        weather = generate_weather_data(b, ts)
        all_weather.append(weather)
        print(f"{len(weather):,} rows")

    print("\n" + "=" * 60)
    print("Saving CSV files...")

    # Building master
    pd.DataFrame(BUILDINGS).to_csv(
        os.path.join(OUTPUT_DIR, "building_master.csv"), index=False
    )
    print("  ✅ building_master.csv — 6 buildings")

    # Energy readings
    df_energy = pd.concat(all_energy, ignore_index=True)
    df_energy.to_csv(os.path.join(OUTPUT_DIR, "raw_energy_readings.csv"), index=False)
    print(f"  ✅ raw_energy_readings.csv — {len(df_energy):,} rows")

    # Solar
    if all_solar:
        df_solar = pd.concat(all_solar, ignore_index=True)
        df_solar.to_csv(os.path.join(OUTPUT_DIR, "raw_solar_generation.csv"), index=False)
        print(f"  ✅ raw_solar_generation.csv — {len(df_solar):,} rows")

    # Battery
    if all_battery:
        df_bat = pd.concat(all_battery, ignore_index=True)
        df_bat.to_csv(os.path.join(OUTPUT_DIR, "raw_battery_status.csv"), index=False)
        print(f"  ✅ raw_battery_status.csv — {len(df_bat):,} rows")

    # Weather
    df_wx = pd.concat(all_weather, ignore_index=True)
    df_wx.to_csv(os.path.join(OUTPUT_DIR, "raw_weather_data.csv"), index=False)

    print("Solar annual estimates (v4 fix):")
    if all_solar:
        df_s = pd.concat(all_solar, ignore_index=True)
        years = (END_DATE - START_DATE).days / 365.25
        for bid2, total in df_s.groupby("building_id")["generated_raw"].sum().items():
            ann = total / years
            print(f"  {bid2}: {ann:,.0f} kWh/yr estimated")

    print("Energy totals by building:")
    print(df_energy.groupby("building_id")["raw_value"].agg(
        total_kwh="sum", avg_interval_kwh="mean", rows="count"
    ).round(2).to_string())
    print("Sample data generation complete.")
    print("Ready for bronze ingestion (01_bronze_ingestion.py)")


if __name__ == "__main__":
    main()
