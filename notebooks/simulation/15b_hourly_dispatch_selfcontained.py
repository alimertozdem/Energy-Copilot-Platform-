# 15b — gold_battery_hourly_dispatch (SELF-CONTAINED).
# Root cause of the empty 24h chart: notebook 15 read gold_battery_hourly_profile,
# which we removed (orphan). This version EMBEDS the 24h pattern inline (from
# notebook 13, EPEX-based) so it has NO dependency on that table. It reads only
# gold_battery_dispatch (per-building daily volumes + capacity) and writes the
# 15-column gold_battery_hourly_dispatch. Standalone, idempotent (overwrite),
# ~110 lines -> pastes into Fabric without truncation. Run -> Refresh.

from pyspark.sql import functions as F
import pandas as pd

# ── 24h reference (German EPEX weekday; from notebook 13) ─────────────────
PRICE = [48,44,40,36,34,38, 55,72,88,95,98,90, 82,78,80,88,96,108, 115,112,105,92,78,62]
AVGP  = sum(PRICE) / 24.0

PATTERNS = {
  "peak_shaving": {"label": "Peak-Shaving",
    "charge":    [0.85,0.90,0.95,1.00,1.00,0.95, 0.70,0.30,0.05,0.00,0.00,0.00, 0.00,0.00,0.00,0.00,0.00,0.00, 0.00,0.00,0.00,0.10,0.45,0.70],
    "discharge": [0.00,0.00,0.00,0.00,0.00,0.00, 0.10,0.55,0.90,1.00,0.95,0.85, 0.70,0.65,0.78,0.92,1.00,0.95, 0.80,0.60,0.40,0.15,0.00,0.00],
    "soc":       [72,80,87,93,97,99, 96,88,73,56,41,28, 19,13,8,8,10,16, 23,28,31,35,45,58]},
  "self_consumption": {"label": "Self-Consumption",
    "charge":    [0.00,0.00,0.00,0.00,0.00,0.00, 0.05,0.10,0.28,0.58,0.88,1.00, 1.00,0.95,0.80,0.52,0.22,0.00, 0.00,0.00,0.00,0.00,0.00,0.00],
    "discharge": [0.15,0.10,0.05,0.05,0.05,0.10, 0.15,0.12,0.08,0.00,0.00,0.00, 0.00,0.00,0.00,0.08,0.25,0.65, 0.92,1.00,0.95,0.80,0.55,0.30],
    "soc":       [55,48,43,39,36,33, 29,25,22,30,45,63, 78,88,92,88,80,65, 50,36,24,15,10,8]},
  "tou": {"label": "Time-of-Use (ToU)",
    "charge":    [1.00,1.00,1.00,1.00,1.00,1.00, 0.90,0.55,0.00,0.00,0.00,0.00, 0.00,0.00,0.00,0.00,0.00,0.00, 0.00,0.00,0.00,0.00,0.52,1.00],
    "discharge": [0.00,0.00,0.00,0.00,0.00,0.00, 0.00,0.22,0.72,1.00,1.00,0.95, 0.90,0.90,0.95,1.00,1.00,0.95, 0.88,0.72,0.52,0.25,0.00,0.00],
    "soc":       [56,66,76,84,91,97, 99,95,82,63,45,29, 17,9,6,5,7,12, 18,22,26,29,37,50]},
  "backup": {"label": "Backup + Opportunistic",
    "charge":    [0.30,0.30,0.30,0.30,0.30,0.30, 0.20,0.10,0.00,0.00,0.00,0.00, 0.00,0.00,0.00,0.10,0.20,0.30, 0.30,0.20,0.20,0.20,0.30,0.30],
    "discharge": [0.00,0.00,0.00,0.00,0.00,0.00, 0.00,0.00,0.12,0.18,0.18,0.12, 0.12,0.12,0.10,0.05,0.00,0.00, 0.00,0.00,0.00,0.00,0.00,0.00],
    "soc":       [83,85,87,88,89,90, 89,88,86,84,82,81, 81,82,83,84,85,86, 86,86,86,86,85,84]},
}

# strategy volume factors relative to the building's active strategy (from notebook 15)
FACTORS = {
  "peak_shaving":     {"peak_shaving":1.00,"tou":0.92,"self_consumption":0.78,"backup":0.22},
  "self_consumption": {"self_consumption":1.00,"peak_shaving":1.18,"tou":1.08,"backup":0.25},
  "tou":              {"tou":1.00,"peak_shaving":1.09,"self_consumption":0.82,"backup":0.24},
  "backup":           {"backup":1.00,"peak_shaving":3.20,"tou":2.80,"self_consumption":2.10},
}

# ── per-building daily volumes + capacity from gold_battery_dispatch ──────
disp = spark.table("gold_battery_dispatch")
daily = (disp.groupBy("building_id", "building_name", "strategy")
    .agg(F.avg("charge_kwh").alias("dch"),
         F.avg("discharge_kwh").alias("ddis"),
         F.last("capacity_kwh").alias("cap"))
).toPandas()
print("buildings(active-strategy) from dispatch:", len(daily))

rows = []
for _, b in daily.iterrows():
    active = b["strategy"]
    cap = float(b["cap"]) if b["cap"] and b["cap"] > 0 else 400.0
    # observed daily volume; fall back to a capacity-based cycle if dispatch had 0
    dch_base  = float(b["dch"])  if b["dch"]  and b["dch"]  > 0 else cap * 0.80
    ddis_base = float(b["ddis"]) if b["ddis"] and b["ddis"] > 0 else cap * 0.75
    fmap = FACTORS.get(active, {})
    for strat, pat in PATTERNS.items():
        factor = fmap.get(strat, 1.0)
        dch = dch_base * factor
        ddis = ddis_base * factor
        csum = float(sum(pat["charge"])); dsum = float(sum(pat["discharge"]))
        for h in range(24):
            price = PRICE[h]
            rows.append({
                "building_id":          b["building_id"],
                "building_name":        b["building_name"],
                "strategy":             strat,
                "strategy_label":       pat["label"],
                "is_active_strategy":   str(strat == active),
                "hour_of_day":          h,
                "hour_label":           f"{h:02d}:00",
                "charge_kwh":           round(pat["charge"][h] / csum * dch, 2) if csum > 0 else 0.0,
                "discharge_kwh":        round(pat["discharge"][h] / dsum * ddis, 2) if dsum > 0 else 0.0,
                "soc_percent":          float(pat["soc"][h]),
                "grid_price_eur_mwh":   float(price),
                "grid_price_index":     round(price / AVGP * 100.0, 1),
                "is_cheap_hour":        "Yes" if price < AVGP * 0.80 else "No",
                "is_peak_price_hour":   "Yes" if price > AVGP * 1.20 else "No",
                "battery_capacity_kwh": cap,
            })

pdf = pd.DataFrame(rows)
sdf = spark.createDataFrame(pdf)
sdf.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("gold_battery_hourly_dispatch")
print("gold_battery_hourly_dispatch rewritten:", sdf.count(), "rows")
print("sample (peak_shaving, one building):")
sdf.filter(F.col("strategy") == "peak_shaving").select(
    "building_name","hour_label","charge_kwh","discharge_kwh","soc_percent","grid_price_eur_mwh"
).orderBy("building_name","hour_of_day").show(24, truncate=False)
print("DONE — Refresh DirectLake. V6 Charge/Discharge/SoC + price now populate the 24h chart.")
