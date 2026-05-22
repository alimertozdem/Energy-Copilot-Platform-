"""
patch_missing_data.py — Energy Copilot Platform
================================================
Appends missing battery and solar data to existing CSVs.

Root cause: the original generator was killed mid-run.
This script patches ONLY the missing segments — existing data is untouched.

Missing data:
  Battery: B001 truncated at row 8148 (2023-03-26 21:00)
           B003 missing entirely
           B005 missing entirely
  Solar:   B005 truncated at row 99145 (2025-10-29 18:15)
           B006 missing entirely

Run:
    python patch_missing_data.py

Output: appends to existing CSV files in the same directory.
"""

import pandas as pd
import numpy as np
import math
import os

SEED       = 99          # Different seed from original (42) to ensure non-duplication
FREQ_MIN   = 15
START_DATE = "2023-01-01"
END_DATE   = "2026-04-18 23:45"
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

np.random.seed(SEED)

# ── Climate params (same as generate_sample_data.py) ─────────────────────────
CITY_CLIMATE = {
    "Berlin":    {"base_temp": 10.0, "seasonal": 9.0,  "daily": 3.0, "noise_sd": 1.5, "solar_peak": 750, "solar_base": 200, "latitude": 52.5},
    "Hamburg":   {"base_temp": 10.0, "seasonal": 8.5,  "daily": 2.8, "noise_sd": 1.6, "solar_peak": 700, "solar_base": 180, "latitude": 53.6},
    "Frankfurt": {"base_temp": 11.0, "seasonal": 9.0,  "daily": 3.2, "noise_sd": 1.5, "solar_peak": 780, "solar_base": 210, "latitude": 50.1},
    "Amsterdam": {"base_temp": 10.0, "seasonal": 7.5,  "daily": 2.5, "noise_sd": 1.7, "solar_peak": 700, "solar_base": 170, "latitude": 52.4},
}

CITY_CLOUD_PROB = {
    "Berlin":    [0.74, 0.71, 0.65, 0.58, 0.55, 0.50, 0.45, 0.44, 0.54, 0.65, 0.72, 0.75],
    "Hamburg":   [0.76, 0.73, 0.68, 0.61, 0.58, 0.53, 0.48, 0.47, 0.57, 0.67, 0.74, 0.77],
    "Frankfurt": [0.72, 0.70, 0.64, 0.58, 0.55, 0.50, 0.45, 0.44, 0.54, 0.64, 0.70, 0.73],
    "Amsterdam": [0.76, 0.74, 0.68, 0.62, 0.59, 0.54, 0.50, 0.49, 0.58, 0.67, 0.74, 0.77],
}

# ── Helper functions (copied from generate_sample_data.py) ───────────────────

def compute_irradiance(ts, city):
    p       = CITY_CLIMATE[city]
    lat_rad = math.radians(p["latitude"])
    doy     = ts.dayofyear.values
    hour    = ts.hour.values
    month   = ts.month.values
    n       = len(ts)

    dec_rad  = np.radians(-23.45 * np.cos(np.radians(360.0 * (doy + 10) / 365.0)))
    cos_ha   = np.clip(-np.tan(lat_rad) * np.tan(dec_rad), -1.0, 1.0)
    ha_deg   = np.degrees(np.arccos(cos_ha))
    ha_hrs   = ha_deg / 15.0
    sunrise  = 12.0 - ha_hrs
    sunset   = 12.0 + ha_hrs
    day_len  = np.maximum(sunset - sunrise, 0.5)

    peak = (p["solar_peak"] - p["solar_base"]) * np.sin(np.pi * doy / 365.0) + p["solar_base"]
    hour_mid = hour + 0.125
    daytime  = (hour_mid >= sunrise) & (hour_mid <= sunset)

    irr = np.where(
        daytime,
        peak * np.sin(np.pi * (hour_mid - sunrise) / day_len),
        0.0,
    )
    irr = np.maximum(0.0, irr + np.random.normal(0, 25, n))

    cloud_probs    = CITY_CLOUD_PROB[city]
    cloud_prob_arr = np.array([cloud_probs[m - 1] for m in month])
    cloud_mask     = np.random.random(n) < cloud_prob_arr
    irr = np.where(cloud_mask, irr * np.random.uniform(0.05, 0.40, n), irr)
    return np.maximum(0.0, irr)


def occupancy_mask_logistics(ts):
    hour = ts.hour.values
    return (hour >= 6) & (hour < 22)

def occupancy_mask_healthcare(ts):
    return np.ones(len(ts), dtype=bool)

def occupancy_mask_education(ts):
    month = ts.month.values
    day   = ts.day.values
    wday  = ts.dayofweek.values
    is_summer  = (month >= 7) & (month <= 8)
    is_xmas    = ((month == 12) & (day >= 22)) | ((month == 1) & (day <= 8))
    is_vacation = is_summer | is_xmas
    return (~is_vacation) & (wday < 5) & (ts.hour.values >= 8) & (ts.hour.values < 18)


# ── Battery generator ─────────────────────────────────────────────────────────

def generate_battery_segment(bid, capacity, strategy, ts, id_offset, init_soc=30.0, anomaly_fn=None):
    """
    Generate battery SoC time-series for a segment of timestamps.
    id_offset: first ingestion_id integer (e.g. 8149 for B001 continuation)
    init_soc:  starting SoC (%) — use last known value for continuations
    anomaly_fn: callable(i, year, month, day, soc) → modified soc (optional)
    """
    n         = len(ts)
    hour_arr  = ts.hour.values
    month_arr = ts.month.values
    day_arr   = ts.day.values
    year_arr  = ts.year.values

    soc    = np.full(n, 50.0)
    charge = np.zeros(n)
    disch  = np.zeros(n)

    current_soc = init_soc
    for i in range(n):
        h = hour_arr[i]
        if strategy == "self_consumption":
            if 10 <= h <= 16:
                delta = np.random.uniform(1.5, 3.5)
                current_soc = min(90.0, current_soc + delta)
                charge[i]   = np.random.uniform(10, 40)
            elif 18 <= h <= 22:
                delta = np.random.uniform(1.5, 4.0)
                current_soc = max(15.0, current_soc - delta)
                disch[i]    = np.random.uniform(10, 35)
        elif strategy in ("peak_shaving", "backup"):
            if 0 <= h <= 6:
                delta = np.random.uniform(3.0, 6.0)
                current_soc = min(90.0, current_soc + delta)
                charge[i]   = np.random.uniform(30, 80)
            elif 8 <= h <= 18:
                delta = np.random.uniform(1.0, 2.5)
                current_soc = max(20.0, current_soc - delta)
                disch[i]    = np.random.uniform(20, 60)

        # B001-specific: over-discharge Nov 2023
        if bid == "B001" and year_arr[i] == 2023 and month_arr[i] == 11 and day_arr[i] in range(5, 10):
            current_soc = max(4.0, current_soc - 3.5)

        # B003-specific: battery degradation Nov 2025 (peak_shaving less effective)
        if bid == "B003" and year_arr[i] == 2025 and month_arr[i] == 11:
            if 8 <= h <= 18:
                current_soc = max(20.0, current_soc - np.random.uniform(0.3, 0.8))

        soc[i] = current_soc

    soc_noisy = np.round(soc + np.random.normal(0, 0.3, n), 1)

    battery_id_map = {"B001": "B001_BATT_01", "B003": "B003_BATT_01", "B005": "B005_BATT_01"}

    return pd.DataFrame({
        "ingestion_id":         [f"{bid}-B-{i + id_offset:08d}" for i in range(n)],
        "building_id":          bid,
        "timestamp_utc":        ts.strftime("%Y-%m-%d %H:%M:%S"),
        "soc_raw":              soc_noisy,
        "charge_power_raw":     np.round(charge, 2),
        "discharge_power_raw":  np.round(disch,  2),
        "battery_id":           battery_id_map[bid],
        "ingested_at":          (ts + pd.Timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M:%S"),
    })


# ── Solar generator ───────────────────────────────────────────────────────────

def generate_solar_segment(bid, kwp, city, btype, has_batt, ts, id_offset):
    """Generate solar generation for a timestamp segment."""
    n         = len(ts)
    irr       = compute_irradiance(ts, city)
    pr        = 0.80
    month_arr = ts.month.values
    soiling   = (month_arr == 8)
    pr_arr    = np.where(soiling, 0.72, pr)

    generated = np.round(
        kwp * (irr / 1000) * pr_arr * (FREQ_MIN / 60) + np.random.normal(0, 0.002, n),
        3
    )
    generated = np.maximum(0.0, generated)

    # Occupancy-based export ratio
    if btype == "Logistics":
        occ = occupancy_mask_logistics(ts)
    elif btype == "Healthcare":
        occ = occupancy_mask_healthcare(ts)
    elif btype == "Education":
        occ = occupancy_mask_education(ts)
    else:
        occ = np.ones(n, dtype=bool)

    if has_batt:
        export_ratio = np.where(
            occ,
            np.random.uniform(0.03, 0.15, n),
            np.random.uniform(0.30, 0.65, n),
        )
    else:
        export_ratio = np.where(
            occ,
            np.random.uniform(0.05, 0.22, n),
            np.random.uniform(0.60, 0.90, n),
        )

    exported = np.round(np.minimum(generated, generated * export_ratio), 3)

    inverter_map = {"B003": "B003_INV_01", "B004": "B004_INV_01", "B005": "B005_INV_01", "B006": "B006_INV_01"}

    return pd.DataFrame({
        "ingestion_id":  [f"{bid}-S-{i + id_offset:08d}" for i in range(n)],
        "building_id":   bid,
        "timestamp_utc": ts.strftime("%Y-%m-%d %H:%M:%S"),
        "generated_raw": generated,
        "exported_raw":  exported,
        "raw_unit":      "kWh",
        "inverter_id":   inverter_map.get(bid, f"{bid}_INV_01"),
        "ingested_at":   (ts + pd.Timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M:%S"),
    })


# ── Fix truncated last lines ──────────────────────────────────────────────────

def fix_truncated_file(filepath):
    """Remove any incomplete (truncated) last line from a CSV file."""
    with open(filepath, "rb") as f:
        content = f.read()
    # Find the last complete newline
    last_nl = content.rfind(b"\n")
    second_last_nl = content.rfind(b"\n", 0, last_nl)
    last_line = content[last_nl + 1:]
    # If the last line has no newline at end AND looks like a partial row, remove it
    if last_line and not last_line.endswith(b"\n"):
        print(f"  ⚠️  Truncated last line found and removed: {last_line[:80]!r}...")
        with open(filepath, "wb") as f:
            f.write(content[:last_nl + 1])
        return True
    return False


# ── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Energy Copilot Platform — Data Patcher")
    print("Appending missing battery + solar data")
    print("=" * 60)

    BATTERY_CSV = os.path.join(OUTPUT_DIR, "raw_battery_status.csv")
    SOLAR_CSV   = os.path.join(OUTPUT_DIR, "raw_solar_generation.csv")

    full_ts = pd.date_range(start=START_DATE, end=END_DATE, freq=f"{FREQ_MIN}min")
    print(f"\nFull period: {len(full_ts):,} intervals")

    # ── Fix truncated files ───────────────────────────────────────────────────
    print("\n[STEP 1] Fixing truncated last lines...")
    fix_truncated_file(BATTERY_CSV)
    fix_truncated_file(SOLAR_CSV)

    # ── Battery: B001 (continuation from row 8149, 2023-03-26 21:15) ─────────
    print("\n[STEP 2] Battery — B001 continuation (row 8149 → 115583)...")
    b001_start = pd.Timestamp("2023-03-26 21:15:00")
    ts_b001    = full_ts[full_ts >= b001_start]
    df_b001_batt = generate_battery_segment(
        bid="B001", capacity=200, strategy="self_consumption",
        ts=ts_b001, id_offset=8149, init_soc=46.6  # last known SoC
    )
    df_b001_batt.to_csv(BATTERY_CSV, mode="a", header=False, index=False)
    print(f"  ✅ B001 battery appended: {len(df_b001_batt):,} rows")

    # ── Battery: B003 (all rows, peak_shaving) ────────────────────────────────
    print("\n[STEP 3] Battery — B003 full generation (800 kWh LFP, peak_shaving)...")
    df_b003_batt = generate_battery_segment(
        bid="B003", capacity=800, strategy="peak_shaving",
        ts=full_ts, id_offset=0, init_soc=30.0
    )
    df_b003_batt.to_csv(BATTERY_CSV, mode="a", header=False, index=False)
    print(f"  ✅ B003 battery appended: {len(df_b003_batt):,} rows")

    # ── Battery: B005 (all rows, backup) ─────────────────────────────────────
    print("\n[STEP 4] Battery — B005 full generation (400 kWh NMC, backup)...")
    df_b005_batt = generate_battery_segment(
        bid="B005", capacity=400, strategy="backup",
        ts=full_ts, id_offset=0, init_soc=30.0
    )
    df_b005_batt.to_csv(BATTERY_CSV, mode="a", header=False, index=False)
    print(f"  ✅ B005 battery appended: {len(df_b005_batt):,} rows")

    # ── Solar: B005 continuation (from row 99146, 2025-10-29 18:30) ──────────
    print("\n[STEP 5] Solar — B005 continuation (row 99146 → 115583)...")
    b005_solar_start = pd.Timestamp("2025-10-29 18:30:00")
    ts_b005_solar    = full_ts[full_ts >= b005_solar_start]
    df_b005_solar    = generate_solar_segment(
        bid="B005", kwp=200, city="Frankfurt", btype="Healthcare",
        has_batt=True, ts=ts_b005_solar, id_offset=99146
    )
    df_b005_solar.to_csv(SOLAR_CSV, mode="a", header=False, index=False)
    print(f"  ✅ B005 solar appended: {len(df_b005_solar):,} rows")

    # ── Solar: B006 (all rows, Education, Amsterdam, no battery) ─────────────
    print("\n[STEP 6] Solar — B006 full generation (150 kWp, Amsterdam)...")
    df_b006_solar = generate_solar_segment(
        bid="B006", kwp=150, city="Amsterdam", btype="Education",
        has_batt=False, ts=full_ts, id_offset=0
    )
    df_b006_solar.to_csv(SOLAR_CSV, mode="a", header=False, index=False)
    print(f"  ✅ B006 solar appended: {len(df_b006_solar):,} rows")

    # ── Verification ──────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)

    import subprocess
    from collections import Counter

    def count_by_building(filepath, col_idx=1):
        result = subprocess.run(
            ["awk", f"-F,", f"NR>1{{print ${col_idx}}}", filepath],
            capture_output=True, text=True
        )
        return Counter(result.stdout.strip().split("\n"))

    print("\nBattery status:")
    batt_counts = count_by_building(BATTERY_CSV)
    for b, c in sorted(batt_counts.items()):
        status = "✅" if c == 115584 else f"⚠️  expected 115584"
        print(f"  {b}: {c:,} rows {status}")

    print("\nSolar generation:")
    solar_counts = count_by_building(SOLAR_CSV)
    for b, c in sorted(solar_counts.items()):
        status = "✅" if c == 115584 else f"⚠️  expected 115584"
        print(f"  {b}: {c:,} rows {status}")

    print("\n✅ Patch complete. Re-run Fabric pipeline: 01 → 02 → 03 → 11")


if __name__ == "__main__":
    main()
