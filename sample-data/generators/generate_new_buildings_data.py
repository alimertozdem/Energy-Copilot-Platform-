"""
=============================================================================
ENERGY COPILOT PLATFORM — Raw Data Generator (New Buildings B007-B010)
=============================================================================
Generates synthetic raw data for 4 new buildings:
  - B007 Copenhagen Net-Plus HQ (DK, Office, GSHP, PV+Battery)
  - B008 Leipzig Plattenbau (DE, Office, gas_boiler, no PV/battery)
  - B009 Frankfurt Datacenter (DE, Datacenter, chiller, PV only)
  - B010 Stockholm Karolinska Lab (SE, Lab, GSHP, PV only)

OUTPUT: sample-data/_new_buildings/<csv_per_building_per_type>.csv

Range: 2023-01-01 to 2026-04-30, 15-minute intervals
Approx output: ~115,000 rows per (building, data type)

REALISTIC PATTERNS:
  - Temperature: sinusoidal annual + diurnal + Gaussian noise
  - HDD/CDD: per-interval, city-specific base temperatures
  - Solar: latitude-aware peak elevation × cloud cover factor
  - Energy: building-type-specific Mon-Fri/weekend patterns + HDD/CDD-driven
  - Battery: self_consumption pattern (charge midday from PV, discharge evening)

USAGE:
  python generate_new_buildings_data.py
  → produces ~14 CSV files in sample-data/_new_buildings/

THEN MANUAL APPEND:
  Each new CSV has same schema as existing raw_*.csv → append rows manually
  (or use cat / Excel / pandas concat — see README in _new_buildings/)
=============================================================================
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# ============================================================================
# CONFIG
# ============================================================================

START_DATE = datetime(2023, 1, 1, 0, 0, 0)
END_DATE   = datetime(2026, 4, 30, 23, 45, 0)
INTERVAL_MIN = 15

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "_new_buildings")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Reproducibility
np.random.seed(2026)


# ============================================================================
# BUILDING SPECIFICATIONS
# ============================================================================
# Each building's energy + weather + PV + battery model parameters.
# Annual kWh/m² → 15-minute baseline load derived in code.

BUILDINGS = {
    # ── B007 Copenhagen Net-Plus HQ ─────────────────────────────────────
    "B007": {
        "city": "Copenhagen", "country": "DK", "latitude": 55.7,
        "type": "Office",
        "conditioned_m2": 5800,
        "annual_kwh_per_m2": 95,          # Passive House Plus level
        "system": "gshp",
        "cop_rated": 5.5,                  # Used for HP electricity calc
        "tier": "Copilot",
        "weather_source": "DMI",
        # Operational ramp: 2023-Q1 to Q2 commissioning (30-50% load)
        "commission_date": datetime(2023, 7, 1),
        "commission_factor": 0.4,
        # Climate base temperatures
        "heating_base_c": 15.5,
        "cooling_base_c": 22.0,
        "annual_temp_mean_c": 9.0,
        "annual_temp_amplitude_c": 11.0,
        # PV
        "has_pv": True, "pv_kwp": 380, "pv_tilt": 28, "pv_orient_az": 0,
        # Battery
        "has_battery": True, "battery_kwh": 450, "battery_strategy": "self_consumption",
        "battery_eff_charge": 0.95, "battery_eff_discharge": 0.95,
        "battery_min_soc": 15, "battery_max_soc": 95,
    },

    # ── B008 Leipzig Plattenbau (worst case) ────────────────────────────
    "B008": {
        "city": "Leipzig", "country": "DE", "latitude": 51.3,
        "type": "Office",
        "conditioned_m2": 8400,
        "annual_kwh_per_m2": 280,          # Very high — uninsulated 1968
        "system": "gas_boiler",
        "cop_rated": None,
        "tier": "Monitor",
        "weather_source": "DWD",
        "commission_date": None,            # Already operational since 1968
        "commission_factor": 1.0,
        "heating_base_c": 17.0,            # Heats earlier due to poor insulation
        "cooling_base_c": 25.0,             # No AC — only ventilation in summer
        "annual_temp_mean_c": 9.5,
        "annual_temp_amplitude_c": 11.5,
        "has_pv": False,
        "has_battery": False,
    },

    # ── B009 Frankfurt Datacenter ───────────────────────────────────────
    "B009": {
        "city": "Frankfurt", "country": "DE", "latitude": 50.1,
        "type": "Datacenter",
        "conditioned_m2": 8200,
        "annual_kwh_per_m2": 1850,         # Very high — IT + cooling load
        "system": "chiller",
        "cop_rated": 4.5,                   # Chiller COP
        "tier": "Copilot",
        "weather_source": "DWD",
        "commission_date": datetime(2020, 6, 1),
        "commission_factor": 1.0,
        "heating_base_c": 8.0,              # Datacenter only heats below this (free cooling above)
        "cooling_base_c": 18.0,             # Cooling starts early — IT load dominant
        "annual_temp_mean_c": 10.5,
        "annual_temp_amplitude_c": 10.5,
        "has_pv": True, "pv_kwp": 250, "pv_tilt": 15, "pv_orient_az": 0,
        "has_battery": False,
    },

    # ── B010 Stockholm Karolinska BioLab ────────────────────────────────
    "B010": {
        "city": "Stockholm", "country": "SE", "latitude": 59.3,
        "type": "Lab",
        "conditioned_m2": 4200,
        "annual_kwh_per_m2": 320,           # High — lab equipment + HEPA
        "system": "gshp",
        "cop_rated": 4.8,
        "tier": "Copilot",
        "weather_source": "SMHI",
        "commission_date": None,
        "commission_factor": 1.0,
        "heating_base_c": 16.0,
        "cooling_base_c": 21.0,
        "annual_temp_mean_c": 7.5,
        "annual_temp_amplitude_c": 12.0,
        "has_pv": True, "pv_kwp": 120, "pv_tilt": 30, "pv_orient_az": 0,
        "has_battery": False,
    },
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def make_timestamps():
    """Generate 15-min timestamp range."""
    return pd.date_range(START_DATE, END_DATE, freq=f"{INTERVAL_MIN}min")


def day_of_year_fraction(ts):
    """Day of year normalised 0-1 for seasonal modelling."""
    return ts.dayofyear / 365.25


def hour_fraction(ts):
    """Hour of day as float (0-24)."""
    return ts.hour + ts.minute / 60.0


def synthetic_temperature(ts, params):
    """Annual sinusoidal + diurnal cycle + noise."""
    doy = ts.dayofyear.values
    hod = ts.hour.values + ts.minute.values / 60.0
    annual = params["annual_temp_mean_c"] - params["annual_temp_amplitude_c"] * np.cos(2 * np.pi * (doy - 15) / 365.25)
    diurnal_amp = 4.5  # °C diurnal swing
    diurnal = diurnal_amp * np.sin(2 * np.pi * (hod - 6) / 24.0)
    noise = np.random.normal(0, 1.4, len(ts))
    return annual + diurnal + noise


def synthetic_solar_irradiance(ts, latitude):
    """Compute approximate solar irradiance (W/m²) by hour and season.
    Simplified: peak ~900 W/m² summer noon, 100 W/m² winter noon, 0 at night.
    Cloud cover applied as multiplicative random factor 0.4-1.0.
    """
    doy = ts.dayofyear.values
    hod = ts.hour.values + ts.minute.values / 60.0
    # Solar elevation peak depends on latitude and day-of-year
    declination = 23.45 * np.sin(np.deg2rad(360 / 365 * (doy - 81)))
    hour_angle = 15 * (hod - 12)
    sin_elev = (
        np.sin(np.deg2rad(latitude)) * np.sin(np.deg2rad(declination))
        + np.cos(np.deg2rad(latitude)) * np.cos(np.deg2rad(declination)) * np.cos(np.deg2rad(hour_angle))
    )
    solar_elev = np.degrees(np.arcsin(np.clip(sin_elev, -1, 1)))
    # No sun below horizon
    irr_clear = np.where(solar_elev > 0, 1000 * np.sin(np.deg2rad(solar_elev)) ** 1.15, 0)
    # Cloud factor
    cloud = 0.4 + 0.6 * np.random.beta(3, 2, len(ts))
    return np.clip(irr_clear * cloud, 0, 1100)


def add_weekly_pattern(ts, weekday_factor, weekend_factor, lab_pattern=False, dc_constant=False):
    """Return per-timestamp factor based on weekday/hour."""
    is_weekend = ts.dayofweek.values >= 5
    hod = ts.hour.values + ts.minute.values / 60.0

    if dc_constant:
        # Datacenter: 24/7 high baseline. Small dip 2-5am, slight peak 14-18 in summer (handled via CDD).
        base = np.ones(len(ts)) * weekday_factor
        return base
    elif lab_pattern:
        # Lab: Mon-Fri 7-19 high (1.0×), 5-7 ramp (0.5×), 19-22 cooldown (0.4×), other 0.25 idle
        weekday_load = np.where(
            (hod >= 7) & (hod < 19), 1.0,
            np.where((hod >= 5) & (hod < 7), 0.5,
                np.where((hod >= 19) & (hod < 22), 0.4, 0.25))
        )
        weekend_load = 0.25  # idle (equipment standby)
        return np.where(is_weekend, weekend_load * weekend_factor, weekday_load * weekday_factor)
    else:
        # Office standard: Mon-Fri 8-18 high (1.0), 6-8 ramp (0.5), 18-21 cooldown (0.4), other 0.2
        weekday_load = np.where(
            (hod >= 8) & (hod < 18), 1.0,
            np.where((hod >= 6) & (hod < 8), 0.5,
                np.where((hod >= 18) & (hod < 21), 0.4, 0.2))
        )
        weekend_load = 0.2
        return np.where(is_weekend, weekend_load * weekend_factor, weekday_load * weekday_factor)


# ============================================================================
# WEATHER DATA GENERATOR
# ============================================================================

def generate_weather(building_id, params):
    ts = make_timestamps()
    n = len(ts)

    temperature = synthetic_temperature(ts, params)
    humidity = np.clip(70 - 0.8 * (temperature - params["annual_temp_mean_c"]) + np.random.normal(0, 6, n), 25, 98)
    solar_irr = synthetic_solar_irradiance(ts, params["latitude"])
    wind = np.clip(np.random.gamma(2, 3, n), 0.5, 25)  # m/s

    # HDD/CDD per 15-min interval (divide daily HDD by 96 intervals)
    hdd_interval = np.maximum(0, params["heating_base_c"] - temperature) / 96
    cdd_interval = np.maximum(0, temperature - params["cooling_base_c"]) / 96

    ingestion_ids = [f"{building_id}-W-{i:08d}" for i in range(n)]
    ingested_at = ts + pd.Timedelta(minutes=3)

    df = pd.DataFrame({
        "ingestion_id": ingestion_ids,
        "building_id": building_id,
        "timestamp_utc": ts.strftime("%Y-%m-%d %H:%M:%S"),
        "temperature_raw": np.round(temperature, 1),
        "humidity_raw": np.round(humidity, 1),
        "solar_irradiance": np.round(solar_irr, 1),
        "wind_speed_raw": np.round(wind, 1),
        "hdd_interval": np.round(hdd_interval, 5),
        "cdd_interval": np.round(cdd_interval, 5),
        "source_api": params["weather_source"],
        "ingested_at": ingested_at.strftime("%Y-%m-%d %H:%M:%S"),
    })

    return df


# ============================================================================
# ENERGY READINGS GENERATOR
# ============================================================================

def generate_energy(building_id, params, weather_df):
    """Generate 15-min electricity consumption (kWh per interval)."""
    ts = make_timestamps()
    n = len(ts)

    # Re-derive temperature from weather_df (or recompute)
    temperature = weather_df["temperature_raw"].values
    hdd = weather_df["hdd_interval"].values
    cdd = weather_df["cdd_interval"].values

    # Annual baseline per 15-min interval
    annual_kwh = params["annual_kwh_per_m2"] * params["conditioned_m2"]
    base_kwh_per_15min = annual_kwh / (365.25 * 96)  # average kWh per 15-min interval

    # Weekly/hourly pattern multiplier
    if params["type"] == "Datacenter":
        pattern_factor = add_weekly_pattern(ts, weekday_factor=1.0, weekend_factor=1.0, dc_constant=True)
    elif params["type"] == "Lab":
        pattern_factor = add_weekly_pattern(ts, weekday_factor=1.0, weekend_factor=0.4, lab_pattern=True)
    else:  # Office
        pattern_factor = add_weekly_pattern(ts, weekday_factor=1.0, weekend_factor=0.3)

    # HVAC contribution: HDD-driven heating, CDD-driven cooling
    # For HP/GSHP: heating energy = thermal demand / COP
    if params["system"] in ("heat_pump", "gshp", "wshp"):
        # HP electricity = thermal_HDD / cop_rated (simplified)
        # Convert per-interval HDD to thermal kWh: scale factor calibrated for building
        cop = params["cop_rated"] or 4.0
        thermal_per_hdd = (params["conditioned_m2"] * 0.08)  # rough kWh thermal per HDD per m2 / 96
        heating_elec = hdd * thermal_per_hdd / cop
        cooling_elec = cdd * thermal_per_hdd * 0.6 / cop  # cooling COP slightly lower
    elif params["system"] == "gas_boiler":
        # Gas boiler → electricity is mostly lighting + plug. Heating is GAS (separate)
        # We still record electric meter — gas tracked indirectly via ghg_scope
        # Heating electricity = small (pumps, controls)
        heating_elec = hdd * params["conditioned_m2"] * 0.005
        cooling_elec = cdd * params["conditioned_m2"] * 0.04  # AC if any
    elif params["system"] == "chiller":
        # Datacenter chiller — cooling-led
        cop = params["cop_rated"] or 4.0
        cooling_elec = cdd * params["conditioned_m2"] * 0.35 / cop + base_kwh_per_15min * 0.5
        heating_elec = hdd * params["conditioned_m2"] * 0.001  # negligible heating in DC
    else:
        heating_elec = hdd * params["conditioned_m2"] * 0.05
        cooling_elec = cdd * params["conditioned_m2"] * 0.04

    # Non-HVAC baseline (lights, plug loads, equipment)
    non_hvac_baseline = base_kwh_per_15min * 0.5 * pattern_factor

    # Total per interval
    total_kwh = non_hvac_baseline + heating_elec + cooling_elec

    # Apply commissioning ramp for B007
    if params.get("commission_date"):
        comm_dt = pd.Timestamp(params["commission_date"])
        is_pre_commission = ts < comm_dt
        ramp_factor = np.where(is_pre_commission, params["commission_factor"], 1.0)
        total_kwh = total_kwh * ramp_factor

    # Add measurement noise (±3%)
    total_kwh = total_kwh * (1 + np.random.normal(0, 0.03, n))
    total_kwh = np.clip(total_kwh, 0.1, None)

    # Spike events for Lab (autoclave/centrifuge): random 1% of intervals get 2-3× spike
    if params["type"] == "Lab":
        spike_mask = np.random.random(n) < 0.01
        total_kwh = np.where(spike_mask, total_kwh * np.random.uniform(2.0, 3.0, n), total_kwh)

    ingestion_ids = [f"{building_id}-E-{i:08d}" for i in range(n)]
    ingested_at = ts + pd.Timedelta(minutes=2)

    df = pd.DataFrame({
        "ingestion_id": ingestion_ids,
        "building_id": building_id,
        "source_system": "SmartMeter",
        "sensor_id": f"{building_id}_MAIN_METER",
        "timestamp_utc": ts.strftime("%Y-%m-%d %H:%M:%S"),
        "raw_value": np.round(total_kwh, 3),
        "raw_unit": "kWh",
        "ingested_at": ingested_at.strftime("%Y-%m-%d %H:%M:%S"),
        "tier": params["tier"],
    })

    return df


# ============================================================================
# SOLAR GENERATION (for buildings with PV)
# ============================================================================

def generate_solar(building_id, params, weather_df):
    if not params.get("has_pv"):
        return None

    ts = make_timestamps()
    n = len(ts)
    irr = weather_df["solar_irradiance"].values

    # Simplified PV power: irr/1000 × kWp × efficiency (0.92) × temperature_derate (0.95 avg)
    pv_kwp = params["pv_kwp"]
    pv_efficiency = 0.92 * 0.95
    pv_power_kw = (irr / 1000.0) * pv_kwp * pv_efficiency
    # Generation per 15-min interval (kWh = kW × 0.25 hr)
    generated_kwh = pv_power_kw * 0.25
    # Export = generated - on-site consumption (simplified: 60% exported)
    exported_kwh = generated_kwh * 0.6
    # Apply commissioning ramp for B007 (PV active from commission_date)
    if params.get("commission_date"):
        comm_dt = pd.Timestamp(params["commission_date"])
        is_pre_commission = ts < comm_dt
        generated_kwh = np.where(is_pre_commission, 0, generated_kwh)
        exported_kwh = np.where(is_pre_commission, 0, exported_kwh)

    ingestion_ids = [f"{building_id}-S-{i:08d}" for i in range(n)]
    ingested_at = ts + pd.Timedelta(minutes=2)

    df = pd.DataFrame({
        "ingestion_id": ingestion_ids,
        "building_id": building_id,
        "timestamp_utc": ts.strftime("%Y-%m-%d %H:%M:%S"),
        "generated_raw": np.round(generated_kwh, 3),
        "exported_raw": np.round(exported_kwh, 3),
        "raw_unit": "kWh",
        "inverter_id": f"{building_id}_INV_01",
        "ingested_at": ingested_at.strftime("%Y-%m-%d %H:%M:%S"),
    })
    return df


# ============================================================================
# BATTERY STATUS (only B007 with battery)
# ============================================================================

def generate_battery(building_id, params, solar_df, energy_df):
    if not params.get("has_battery"):
        return None

    ts = make_timestamps()
    n = len(ts)

    # Self-consumption strategy: charge when PV > load, discharge when load > PV (peak hours)
    cap_kwh = params["battery_kwh"]
    eff_c = params["battery_eff_charge"]
    eff_d = params["battery_eff_discharge"]
    min_soc = params["battery_min_soc"]
    max_soc = params["battery_max_soc"]

    pv_kwh = solar_df["generated_raw"].values
    load_kwh = energy_df["raw_value"].values

    soc_pct = np.zeros(n)
    charge_kw = np.zeros(n)
    discharge_kw = np.zeros(n)
    soc = 30.0  # Starting SOC %

    # Apply commissioning: battery offline until commission_date
    comm_dt = pd.Timestamp(params["commission_date"])
    timestamps_arr = ts.to_numpy()

    for i in range(n):
        if timestamps_arr[i] < np.datetime64(comm_dt):
            soc_pct[i] = soc  # frozen
            continue

        surplus = pv_kwh[i] - load_kwh[i]  # positive = excess PV
        max_charge_kwh = (max_soc - soc) / 100 * cap_kwh
        max_discharge_kwh = (soc - min_soc) / 100 * cap_kwh

        if surplus > 0:  # Charge
            charge = min(surplus, max_charge_kwh, cap_kwh * 0.25 * 0.5)  # max C/2 rate per interval
            stored = charge * eff_c
            soc += (stored / cap_kwh) * 100
            charge_kw[i] = charge / 0.25  # convert kWh/15min → kW
        elif surplus < 0:  # Discharge
            need = -surplus
            discharge = min(need, max_discharge_kwh, cap_kwh * 0.25 * 0.5)
            delivered = discharge * eff_d
            soc -= (discharge / cap_kwh) * 100
            discharge_kw[i] = delivered / 0.25
        soc = np.clip(soc, min_soc, max_soc)
        soc_pct[i] = soc

    ingestion_ids = [f"{building_id}-B-{i:08d}" for i in range(n)]
    ingested_at = ts + pd.Timedelta(minutes=2)

    df = pd.DataFrame({
        "ingestion_id": ingestion_ids,
        "building_id": building_id,
        "timestamp_utc": ts.strftime("%Y-%m-%d %H:%M:%S"),
        "soc_raw": np.round(soc_pct, 1),
        "charge_power_raw": np.round(charge_kw, 2),
        "discharge_power_raw": np.round(discharge_kw, 2),
        "battery_id": f"{building_id}_BATT_01",
        "ingested_at": ingested_at.strftime("%Y-%m-%d %H:%M:%S"),
    })
    return df


# ============================================================================
# MAIN ORCHESTRATOR
# ============================================================================

def main():
    print(f"Generating raw data for 4 new buildings")
    print(f"Range: {START_DATE} → {END_DATE}, interval: {INTERVAL_MIN} min")
    print(f"Output: {OUTPUT_DIR}\n")

    for bid, params in BUILDINGS.items():
        print(f"=== {bid} {params['city']} ({params['type']}, {params['system']}) ===")

        # 1) Weather
        weather_df = generate_weather(bid, params)
        weather_path = os.path.join(OUTPUT_DIR, f"{bid}_weather.csv")
        weather_df.to_csv(weather_path, index=False)
        print(f"  ✓ weather: {len(weather_df):,} rows → {weather_path}")

        # 2) Energy
        energy_df = generate_energy(bid, params, weather_df)
        energy_path = os.path.join(OUTPUT_DIR, f"{bid}_energy.csv")
        energy_df.to_csv(energy_path, index=False)
        print(f"  ✓ energy: {len(energy_df):,} rows, annual={energy_df['raw_value'].sum() / (END_DATE.year - START_DATE.year + 1):,.0f} kWh/yr → {energy_path}")

        # 3) Solar (if PV)
        solar_df = generate_solar(bid, params, weather_df)
        if solar_df is not None:
            solar_path = os.path.join(OUTPUT_DIR, f"{bid}_solar.csv")
            solar_df.to_csv(solar_path, index=False)
            print(f"  ✓ solar: {len(solar_df):,} rows, annual={solar_df['generated_raw'].sum() / (END_DATE.year - START_DATE.year + 1):,.0f} kWh/yr → {solar_path}")

        # 4) Battery (if has battery)
        battery_df = generate_battery(bid, params, solar_df, energy_df) if solar_df is not None else None
        if battery_df is not None:
            battery_path = os.path.join(OUTPUT_DIR, f"{bid}_battery.csv")
            battery_df.to_csv(battery_path, index=False)
            avg_soc = battery_df["soc_raw"].mean()
            print(f"  ✓ battery: {len(battery_df):,} rows, avg SOC={avg_soc:.1f}% → {battery_path}")

        print()

    # ── Write README ────────────────────────────────────────────────────
    readme_path = os.path.join(OUTPUT_DIR, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("""# Generated Raw Data — 4 New Buildings (B007-B010)

Generated by: `generators/generate_new_buildings_data.py`
Range: 2023-01-01 to 2026-04-30, 15-minute intervals

## Files

| File | Schema match | Append to |
|---|---|---|
| `B007_weather.csv` | ✓ same as raw_weather_data.csv | `sample-data/raw_weather_data.csv` |
| `B007_energy.csv` | ✓ same as raw_energy_readings.csv.csv | `sample-data/raw_energy_readings.csv.csv` |
| `B007_solar.csv` | ✓ same as raw_solar_generation.csv | `sample-data/raw_solar_generation.csv` |
| `B007_battery.csv` | ✓ same as raw_battery_status.csv | `sample-data/raw_battery_status.csv` |
| `B008_weather.csv` + `B008_energy.csv` | ✓ | (same as above) |
| `B009_weather.csv` + `B009_energy.csv` + `B009_solar.csv` | ✓ | (same as above) |
| `B010_weather.csv` + `B010_energy.csv` + `B010_solar.csv` | ✓ | (same as above) |

## Manual Append Procedure (Windows PowerShell)

```powershell
cd "C:\\Energy Management App\\Energy-copilot-platform\\sample-data"

# 1) BACKUP existing CSVs first!
Copy-Item raw_energy_readings.csv.csv raw_energy_readings.csv.csv.backup
Copy-Item raw_weather_data.csv raw_weather_data.csv.backup
Copy-Item raw_solar_generation.csv raw_solar_generation.csv.backup
Copy-Item raw_battery_status.csv raw_battery_status.csv.backup

# 2) Append energy (skip header row of new files)
Get-Content _new_buildings/B007_energy.csv | Select-Object -Skip 1 | Add-Content raw_energy_readings.csv.csv
Get-Content _new_buildings/B008_energy.csv | Select-Object -Skip 1 | Add-Content raw_energy_readings.csv.csv
Get-Content _new_buildings/B009_energy.csv | Select-Object -Skip 1 | Add-Content raw_energy_readings.csv.csv
Get-Content _new_buildings/B010_energy.csv | Select-Object -Skip 1 | Add-Content raw_energy_readings.csv.csv

# 3) Append weather
Get-Content _new_buildings/B007_weather.csv | Select-Object -Skip 1 | Add-Content raw_weather_data.csv
Get-Content _new_buildings/B008_weather.csv | Select-Object -Skip 1 | Add-Content raw_weather_data.csv
Get-Content _new_buildings/B009_weather.csv | Select-Object -Skip 1 | Add-Content raw_weather_data.csv
Get-Content _new_buildings/B010_weather.csv | Select-Object -Skip 1 | Add-Content raw_weather_data.csv

# 4) Append solar (only buildings with PV)
Get-Content _new_buildings/B007_solar.csv | Select-Object -Skip 1 | Add-Content raw_solar_generation.csv
Get-Content _new_buildings/B009_solar.csv | Select-Object -Skip 1 | Add-Content raw_solar_generation.csv
Get-Content _new_buildings/B010_solar.csv | Select-Object -Skip 1 | Add-Content raw_solar_generation.csv

# 5) Append battery (only B007)
Get-Content _new_buildings/B007_battery.csv | Select-Object -Skip 1 | Add-Content raw_battery_status.csv
```

## Validation

After append:
```powershell
# Count buildings in each file (should be 10)
(Get-Content raw_energy_readings.csv.csv | Select-Object -Skip 1 | ForEach-Object { ($_ -split ',')[1] } | Sort-Object -Unique).Count  # → 10
(Get-Content raw_weather_data.csv | Select-Object -Skip 1 | ForEach-Object { ($_ -split ',')[1] } | Sort-Object -Unique).Count  # → 10
```

## Rollback (if anything goes wrong)

```powershell
Copy-Item raw_energy_readings.csv.csv.backup raw_energy_readings.csv.csv
Copy-Item raw_weather_data.csv.backup raw_weather_data.csv
Copy-Item raw_solar_generation.csv.backup raw_solar_generation.csv
Copy-Item raw_battery_status.csv.backup raw_battery_status.csv
```
""")
    print(f"\n✓ README written: {readme_path}")
    print("\n✅ All raw data generated. See README for append procedure.")


if __name__ == "__main__":
    main()
