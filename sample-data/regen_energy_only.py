"""
v5 quick regenerator — energy readings only.

WHY: Full generate_sample_data.py also rebuilds solar/battery/weather (~3 min).
For Page 1 EUI fix we only need fresh raw_energy_readings.csv. This runs in
~45s and writes only the energy CSV. Solar/battery/weather unchanged.
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generate_sample_data as g
import pandas as pd

t0 = time.time()
ts = g.make_timestamps()
print(f"[regen-energy] timestamps={len(ts):,}  buildings={len(g.BUILDINGS)}")

frames = []
for b in g.BUILDINGS:
    print(f"[regen-energy] {b['building_id']} {b['building_name'][:30]}", flush=True)
    frames.append(g.generate_energy_readings(b, ts))

df = pd.concat(frames, ignore_index=True)
out = os.path.join(g.OUTPUT_DIR, "raw_energy_readings.csv")
df.to_csv(out, index=False)
print(f"[regen-energy] WROTE {out}  rows={len(df):,}  elapsed={time.time()-t0:.1f}s")

# EUI validation
df["ts"]   = pd.to_datetime(df["timestamp_utc"])
df["year"] = df["ts"].dt.year
yr2025 = df[df["year"] == 2025].groupby("building_id")["raw_value"].sum()
print("\n[regen-energy] EUI validation (annualized 2025, kWh/m²/yr):")
for b in g.BUILDINGS:
    bid  = b["building_id"]
    area = b["gross_floor_area_m2"]
    kwh  = yr2025.get(bid, 0)
    eui  = kwh / area if area else 0
    print(f"  {bid} {b['building_name'][:30]:30s}  {kwh:>12,.0f} kWh   EUI={eui:>6.1f}")
