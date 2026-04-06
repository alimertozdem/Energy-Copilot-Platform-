"""
Sample Data Generator — Energy Copilot Platform
Generates realistic synthetic building energy data for development and testing.

Buildings:
  - B001: Office building, Berlin, Germany — Tier 2 (Monitor), has PV + Battery + Heat Pump
  - B002: Retail building, Istanbul, Turkey — Tier 1 (Insight), standard HVAC only
  - B003: Logistics center, Hamburg, Germany — Tier 3 (Copilot), has PV + Battery

Usage:
    python generate_sample_data.py

Output:
    sample-data/
        raw_energy_readings.csv
        raw_solar_generation.csv
        raw_battery_status.csv
        raw_weather_data.csv
        building_master.csv
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import math

# ── Configuration ────────────────────────────────────────────────────────────

SEED = 42
np.random.seed(SEED)

START_DATE = datetime(2024, 1, 1)
END_DATE   = datetime(2024, 12, 31, 23, 45)
FREQ_MIN   = 15  # 15-minute intervals

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Building Master Data ──────────────────────────────────────────────────────

BUILDINGS = [
    {
        "building_id": "B001",
        "organization_id": "ORG001",
        "building_name": "Berliner Bürogebäude Alpha",
        "country_code": "DE",
        "city": "Berlin",
        "climate_zone": "Cfb",
        "gross_floor_area_m2": 5200.0,
        "conditioned_area_m2": 4800.0,
        "year_built": 2005,
        "building_type": "Office",
        "subscription_tier": "Monitor",
        "has_pv": True,
        "pv_capacity_kwp": 120.0,
        "roof_area_m2": 1100.0,
        "roof_orientation": "S",
        "roof_tilt_deg": 30.0,
        "has_battery": True,
        "battery_capacity_kwh": 200.0,
        "battery_technology": "LFP",
        "battery_strategy": "self_consumption",
        "has_heat_pump": True,
        "heat_pump_cop_rated": 3.8,
        "heat_pump_capacity_kw": 90.0,
        "has_hvac_traditional": False,
        "has_ev_charging": False,
        "has_led_lighting": True,
        "wall_u_value": 0.28,
        "roof_u_value": 0.18,
        "floor_u_value": 0.30,
        "window_u_value": 1.1,
        "window_to_wall_ratio": 0.35,
        "air_tightness_ach": 1.2,
        "thermal_mass_level": "MEDIUM",
        "insulation_year": 2015,
        "has_thermal_bridge": False,
        "energy_certificate": "B",
        "energy_certificate_year": 2022,
        "regulatory_profile_id": "REG_DE",
        "iso50001_certified": False,
    },
    {
        "building_id": "B002",
        "organization_id": "ORG002",
        "building_name": "Istanbul Ticaret Merkezi Beta",
        "country_code": "TR",
        "city": "Istanbul",
        "climate_zone": "Csa",
        "gross_floor_area_m2": 8500.0,
        "conditioned_area_m2": 7200.0,
        "year_built": 1998,
        "building_type": "Retail",
        "subscription_tier": "Insight",
        "has_pv": False,
        "pv_capacity_kwp": None,
        "roof_area_m2": 2000.0,
        "roof_orientation": None,
        "roof_tilt_deg": None,
        "has_battery": False,
        "battery_capacity_kwh": None,
        "battery_technology": None,
        "battery_strategy": None,
        "has_heat_pump": False,
        "heat_pump_cop_rated": None,
        "heat_pump_capacity_kw": None,
        "has_hvac_traditional": True,
        "has_ev_charging": False,
        "has_led_lighting": False,
        "wall_u_value": 0.80,
        "roof_u_value": 0.55,
        "floor_u_value": 0.70,
        "window_u_value": 2.8,
        "window_to_wall_ratio": 0.25,
        "air_tightness_ach": 3.5,
        "thermal_mass_level": "HIGH",
        "insulation_year": None,
        "has_thermal_bridge": True,
        "energy_certificate": "E",
        "energy_certificate_year": 2018,
        "regulatory_profile_id": "REG_TR",
        "iso50001_certified": False,
    },
    {
        "building_id": "B003",
        "organization_id": "ORG001",
        "building_name": "Hamburg Logistics Hub Gamma",
        "country_code": "DE",
        "city": "Hamburg",
        "climate_zone": "Cfb",
        "gross_floor_area_m2": 12000.0,
        "conditioned_area_m2": 10000.0,
        "year_built": 2018,
        "building_type": "Logistics",
        "subscription_tier": "Copilot",
        "has_pv": True,
        "pv_capacity_kwp": 500.0,
        "roof_area_m2": 6000.0,
        "roof_orientation": "S",
        "roof_tilt_deg": 10.0,
        "has_battery": True,
        "battery_capacity_kwh": 800.0,
        "battery_technology": "LFP",
        "battery_strategy": "peak_shaving",
        "has_heat_pump": False,
        "heat_pump_cop_rated": None,
        "heat_pump_capacity_kw": None,
        "has_hvac_traditional": True,
        "has_ev_charging": True,
        "has_led_lighting": True,
        "wall_u_value": 0.22,
        "roof_u_value": 0.15,
        "floor_u_value": 0.25,
        "window_u_value": 0.9,
        "window_to_wall_ratio": 0.10,
        "air_tightness_ach": 0.8,
        "thermal_mass_level": "LOW",
        "insulation_year": 2018,
        "has_thermal_bridge": False,
        "energy_certificate": "A",
        "energy_certificate_year": 2023,
        "regulatory_profile_id": "REG_DE",
        "iso50001_certified": True,
    },
]

# ── Helper Functions ──────────────────────────────────────────────────────────

def is_weekend(dt):
    return dt.weekday() >= 5

def is_occupied(dt, building_type):
    """Returns True if building is occupied at given datetime."""
    hour = dt.hour
    wday = dt.weekday()
    if building_type == "Office":
        return (wday < 5) and (7 <= hour < 20)
    elif building_type == "Retail":
        return (wday < 6) and (9 <= hour < 22)
    elif building_type == "Logistics":
        return (6 <= hour < 22)  # 7 days
    return True

def outdoor_temp_berlin(dt):
    """Synthetic Berlin outdoor temperature (seasonal + daily variation)."""
    day_of_year = dt.timetuple().tm_yday
    seasonal = -8 * math.cos(2 * math.pi * day_of_year / 365)  # -8°C winter, +8°C summer offset
    base = 10  # Berlin annual average ~10°C
    daily = -3 * math.cos(2 * math.pi * dt.hour / 24)  # colder at night
    noise = np.random.normal(0, 1.5)
    return round(base + seasonal + daily + noise, 1)

def outdoor_temp_istanbul(dt):
    """Synthetic Istanbul outdoor temperature."""
    day_of_year = dt.timetuple().tm_yday
    seasonal = -7 * math.cos(2 * math.pi * day_of_year / 365)
    base = 14  # Istanbul annual average ~14°C
    daily = -2.5 * math.cos(2 * math.pi * dt.hour / 24)
    noise = np.random.normal(0, 1.5)
    return round(base + seasonal + daily + noise, 1)

def solar_irradiance(dt, city):
    """Synthetic solar irradiance W/m²."""
    hour = dt.hour
    day_of_year = dt.timetuple().tm_yday
    if hour < 5 or hour > 21:
        return 0.0
    # Peak irradiance varies seasonally
    if city in ["Berlin", "Hamburg"]:
        peak = 600 * math.sin(math.pi * day_of_year / 365) + 200
    else:  # Istanbul
        peak = 800 * math.sin(math.pi * day_of_year / 365) + 300
    # Daily bell curve (peak at solar noon ~13:00)
    irr = peak * math.sin(math.pi * (hour - 5) / 16)
    irr = max(0, irr + np.random.normal(0, 30))
    # Cloudy days: randomly reduce
    if np.random.random() < 0.3:
        irr *= np.random.uniform(0.1, 0.6)
    return round(irr, 1)


# ── Data Generators ───────────────────────────────────────────────────────────

def generate_energy_readings(building, timestamps):
    """Generate synthetic energy consumption data."""
    rows = []
    b = building
    area = b["conditioned_area_m2"]
    btype = b["building_type"]

    # Base load (kW) — always-on equipment
    base_load = area * 0.003  # ~3W per m²

    for i, ts in enumerate(timestamps):
        occupied = is_occupied(ts, btype)

        if btype == "Office":
            peak_density = 0.020  # 20 W/m² occupied
        elif btype == "Retail":
            peak_density = 0.035  # 35 W/m² occupied (lighting heavy)
        elif btype == "Logistics":
            peak_density = 0.025

        # Demand
        if occupied:
            demand_kw = area * peak_density * np.random.uniform(0.7, 1.1)
        else:
            demand_kw = base_load * np.random.uniform(0.9, 1.1)

        # Temperature effect on HVAC
        if b["country_code"] == "DE":
            temp = outdoor_temp_berlin(ts)
        else:
            temp = outdoor_temp_istanbul(ts)

        # Heating/cooling adjustment
        if temp < 15 and occupied:
            demand_kw *= 1 + (15 - temp) * 0.015
        elif temp > 25 and occupied:
            demand_kw *= 1 + (temp - 25) * 0.012

        # Inject a realistic anomaly: consumption spike in March for B002
        if b["building_id"] == "B002" and ts.month == 3 and ts.day == 15:
            if 9 <= ts.hour <= 14:
                demand_kw *= 1.8  # ~80% spike

        consumption_kwh = round(demand_kw * (FREQ_MIN / 60), 3)

        rows.append({
            "ingestion_id": f"{b['building_id']}-E-{i:08d}",
            "building_id": b["building_id"],
            "source_system": "SmartMeter",
            "sensor_id": f"{b['building_id']}_MAIN_METER",
            "timestamp_utc": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "raw_value": consumption_kwh,
            "raw_unit": "kWh",
            "ingested_at": (ts + timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M:%S"),
            "tier": b["subscription_tier"],
        })
    return rows


def generate_solar_generation(building, timestamps):
    """Generate synthetic PV solar generation data."""
    if not building.get("has_pv"):
        return []
    rows = []
    b = building
    kwp = b["pv_capacity_kwp"]
    city = b["city"]
    pr = 0.80  # Performance Ratio

    for i, ts in enumerate(timestamps):
        irr = solar_irradiance(ts, city)
        # Generation: kWp × irradiance (kWh/m²) × PR / 1000 × (15min/60)
        generated = kwp * (irr / 1000) * pr * (FREQ_MIN / 60)
        generated = max(0, round(generated + np.random.normal(0, generated * 0.02 if generated > 0 else 0), 3))

        # Simulate panel soiling in summer: PR drops for B001 in August
        if b["building_id"] == "B001" and ts.month == 8:
            generated *= 0.72  # PR drops to 0.72

        # Exported = portion not used by building (simplified)
        export_ratio = np.random.uniform(0.20, 0.45) if generated > 0 else 0
        exported = round(generated * export_ratio, 3)

        rows.append({
            "ingestion_id": f"{b['building_id']}-S-{i:08d}",
            "building_id": b["building_id"],
            "timestamp_utc": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "generated_raw": generated,
            "exported_raw": exported,
            "raw_unit": "kWh",
            "inverter_id": f"{b['building_id']}_INV_01",
            "ingested_at": (ts + timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M:%S"),
        })
    return rows


def generate_battery_status(building, timestamps):
    """Generate synthetic battery state of charge data."""
    if not building.get("has_battery"):
        return []
    rows = []
    b = building
    capacity = b["battery_capacity_kwh"]
    strategy = b["battery_strategy"]

    soc = 50.0  # Start at 50%

    for i, ts in enumerate(timestamps):
        hour = ts.hour

        if strategy == "self_consumption":
            # Charge during solar hours, discharge evenings
            if 10 <= hour <= 16:
                soc = min(90, soc + np.random.uniform(0.5, 2.0))
                charge_kw = np.random.uniform(5, 20)
                discharge_kw = 0
            elif 18 <= hour <= 22:
                soc = max(15, soc - np.random.uniform(0.5, 1.5))
                charge_kw = 0
                discharge_kw = np.random.uniform(5, 15)
            else:
                charge_kw = 0
                discharge_kw = 0
        else:  # peak_shaving
            if 0 <= hour <= 6:
                soc = min(85, soc + np.random.uniform(1.0, 3.0))
                charge_kw = np.random.uniform(20, 60)
                discharge_kw = 0
            elif 8 <= hour <= 18:
                soc = max(20, soc - np.random.uniform(0.3, 1.0))
                charge_kw = 0
                discharge_kw = np.random.uniform(10, 40)
            else:
                charge_kw = 0
                discharge_kw = 0

        # Inject anomaly for B001: SoC drops below 10% in November (over-discharge)
        if b["building_id"] == "B001" and ts.month == 11 and ts.day in range(5, 10):
            soc = max(5, soc - 3)

        rows.append({
            "ingestion_id": f"{b['building_id']}-B-{i:08d}",
            "building_id": b["building_id"],
            "timestamp_utc": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "soc_raw": round(soc + np.random.normal(0, 0.3), 1),
            "charge_power_raw": round(charge_kw, 2),
            "discharge_power_raw": round(discharge_kw, 2),
            "battery_id": f"{b['building_id']}_BATT_01",
            "ingested_at": (ts + timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M:%S"),
        })
    return rows


def generate_weather_data(building, timestamps):
    """Generate synthetic weather data per building location."""
    rows = []
    b = building
    city = b["city"]
    country = b["country_code"]

    for i, ts in enumerate(timestamps):
        if country == "DE":
            temp = outdoor_temp_berlin(ts)
        else:
            temp = outdoor_temp_istanbul(ts)

        irr = solar_irradiance(ts, city)
        humidity = round(np.random.uniform(40, 85), 1)
        wind = round(max(0, np.random.normal(4, 2)), 1)

        # HDD / CDD (per 15-min interval, scaled)
        hdd_interval = max(0, 15 - temp) * (FREQ_MIN / (60 * 24))
        cdd_interval = max(0, temp - 22) * (FREQ_MIN / (60 * 24))

        rows.append({
            "ingestion_id": f"{b['building_id']}-W-{i:08d}",
            "building_id": b["building_id"],
            "timestamp_utc": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "temperature_raw": temp,
            "humidity_raw": humidity,
            "solar_irradiance": irr,
            "wind_speed_raw": wind,
            "source_api": "DWD" if country == "DE" else "MGM",
            "ingested_at": (ts + timedelta(minutes=3)).strftime("%Y-%m-%d %H:%M:%S"),
        })
    return rows


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Generating timestamps...")
    timestamps = []
    current = START_DATE
    while current <= END_DATE:
        timestamps.append(current)
        current += timedelta(minutes=FREQ_MIN)
    print(f"  {len(timestamps):,} intervals ({START_DATE.date()} to {END_DATE.date()})")

    all_energy, all_solar, all_battery, all_weather = [], [], [], []

    for b in BUILDINGS:
        bid = b["building_id"]
        print(f"\nGenerating data for {bid} — {b['building_name']} ({b['subscription_tier']})...")

        energy = generate_energy_readings(b, timestamps)
        all_energy.extend(energy)
        print(f"  Energy readings: {len(energy):,} rows")

        solar = generate_solar_generation(b, timestamps)
        all_solar.extend(solar)
        if solar:
            print(f"  Solar generation: {len(solar):,} rows")

        battery = generate_battery_status(b, timestamps)
        all_battery.extend(battery)
        if battery:
            print(f"  Battery status: {len(battery):,} rows")

        weather = generate_weather_data(b, timestamps)
        all_weather.extend(weather)
        print(f"  Weather data: {len(weather):,} rows")

    # Save files
    print("\nSaving CSV files...")

    pd.DataFrame(BUILDINGS).to_csv(
        os.path.join(OUTPUT_DIR, "building_master.csv"), index=False
    )
    print("  building_master.csv")

    pd.DataFrame(all_energy).to_csv(
        os.path.join(OUTPUT_DIR, "raw_energy_readings.csv"), index=False
    )
    print(f"  raw_energy_readings.csv — {len(all_energy):,} rows")

    if all_solar:
        pd.DataFrame(all_solar).to_csv(
            os.path.join(OUTPUT_DIR, "raw_solar_generation.csv"), index=False
        )
        print(f"  raw_solar_generation.csv — {len(all_solar):,} rows")

    if all_battery:
        pd.DataFrame(all_battery).to_csv(
            os.path.join(OUTPUT_DIR, "raw_battery_status.csv"), index=False
        )
        print(f"  raw_battery_status.csv — {len(all_battery):,} rows")

    pd.DataFrame(all_weather).to_csv(
        os.path.join(OUTPUT_DIR, "raw_weather_data.csv"), index=False
    )
    print(f"  raw_weather_data.csv — {len(all_weather):,} rows")

    print("\nDone. Sample data ready for ingestion.")


if __name__ == "__main__":
    main()
