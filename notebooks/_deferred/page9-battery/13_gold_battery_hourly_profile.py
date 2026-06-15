# =============================================================================
# NOTEBOOK: 13 — Generate gold_battery_hourly_profile
# Purpose : Creates a representative 24-hour dispatch profile for each strategy.
#           This enables the "Hourly Battery Behavior" visual in Page 9.
#           Data is NOT from real meters — it is strategy-accurate simulation
#           based on German electricity market patterns (EPEX Spot profile).
#
# Run in  : Microsoft Fabric — PySpark (Python) Notebook
# Lakehouse: EnergyCopilotLakehouse (must be attached as default)
# Output  : gold_battery_hourly_profile (96 rows: 4 strategies × 24 hours)
#
# ENERGY LOGIC (approved):
#   Peak-Shaving : Charge 22h–07h (off-peak, night), discharge 07h–21h (demand peaks)
#   Self-Consumption: Charge 10h–15h (PV generation peak), discharge 17h–23h (evening load)
#   Time-of-Use  : Charge 00h–07h (cheapest EPEX hours), discharge 08h–20h (expensive hours)
#   Backup       : Maintain 80–90% SoC always — minimal cycling, reserve capacity
#
#   German EPEX Spot price curve: off-peak 00h–06h (~40–55 €/MWh),
#   morning ramp 06h–09h, business peak 09h–20h (85–115 €/MWh),
#   evening decline 21h–23h. Midday price dip 12h–14h (solar generation).
# =============================================================================

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import *
import pandas as pd

spark = SparkSession.builder.getOrCreate()

# ── CELL 1: Define 24-hour profiles ──────────────────────────────────────────

# German EPEX Spot day-ahead price (€/MWh), typical weekday
# Source: representative profile based on 2023–2025 EPEX averages
german_price_eur_mwh = [
    48, 44, 40, 36, 34, 38,     # 00–05h: cheapest (low demand, high wind)
    55, 72, 88, 95, 98, 90,     # 06–11h: morning ramp + business start
    82, 78, 80, 88, 96, 108,    # 12–17h: midday solar dip, afternoon rise
   115, 112, 105, 92, 78, 62    # 18–23h: evening peak then decline
]
daily_avg_price = sum(german_price_eur_mwh) / 24   # ~78 €/MWh

# ── PEAK-SHAVING ─────────────────────────────────────────────────────────────
# Goal: reduce building peak demand charge (Grundpreis/Leistungspreis)
# Charges at night when building is quiet and electricity is cheap
# Discharges during working hours when building demand is highest
peak_shaving = {
    "charge_rate":    [0.85, 0.90, 0.95, 1.00, 1.00, 0.95,   # 00–05h full charge
                       0.70, 0.30, 0.05, 0.00, 0.00, 0.00,   # 06–11h tapering off
                       0.00, 0.00, 0.00, 0.00, 0.00, 0.00,   # 12–17h no charge
                       0.00, 0.00, 0.00, 0.10, 0.45, 0.70],  # 18–23h recharging starts
    "discharge_rate": [0.00, 0.00, 0.00, 0.00, 0.00, 0.00,   # 00–05h no discharge
                       0.10, 0.55, 0.90, 1.00, 0.95, 0.85,   # 06–11h morning peak
                       0.70, 0.65, 0.78, 0.92, 1.00, 0.95,   # 12–17h afternoon peak
                       0.80, 0.60, 0.40, 0.15, 0.00, 0.00],  # 18–23h winding down
    "soc_percent":    [72, 80, 87, 93, 97, 99,                # 00–05h rising
                       96, 88, 73, 56, 41, 28,                # 06–11h falling fast
                       19, 13,  8,  8, 10, 16,                # 12–17h near minimum
                       23, 28, 31, 35, 45, 58],               # 18–23h recovering
}

# ── SELF-CONSUMPTION ─────────────────────────────────────────────────────────
# Goal: maximize use of own PV generation, reduce grid imports
# Charges when solar output exceeds building load (10h–15h)
# Discharges in evening when load is high and solar has stopped
self_consumption = {
    "charge_rate":    [0.00, 0.00, 0.00, 0.00, 0.00, 0.00,   # 00–05h no sun
                       0.05, 0.10, 0.28, 0.58, 0.88, 1.00,   # 06–11h PV ramping
                       1.00, 0.95, 0.80, 0.52, 0.22, 0.00,   # 12–17h PV peak then decline
                       0.00, 0.00, 0.00, 0.00, 0.00, 0.00],  # 18–23h no charge
    "discharge_rate": [0.15, 0.10, 0.05, 0.05, 0.05, 0.10,   # 00–05h low overnight use
                       0.15, 0.12, 0.08, 0.00, 0.00, 0.00,   # 06–11h PV covers load
                       0.00, 0.00, 0.00, 0.08, 0.25, 0.65,   # 12–17h evening starts
                       0.92, 1.00, 0.95, 0.80, 0.55, 0.30],  # 18–23h peak discharge
    "soc_percent":    [55, 48, 43, 39, 36, 33,                # 00–05h overnight drift
                       29, 25, 22, 30, 45, 63,                # 06–11h PV charging
                       78, 88, 92, 88, 80, 65,                # 12–17h high then decline
                       50, 36, 24, 15, 10,  8],               # 18–23h evening discharge
}

# ── TIME-OF-USE (ToU) ─────────────────────────────────────────────────────────
# Goal: buy electricity at cheapest hours, use stored energy during expensive hours
# Very responsive to German EPEX Spot price signal
# Cheapest: 00h–06h (~36–48 €/MWh). Most expensive: 17h–20h (~108–115 €/MWh)
tou = {
    "charge_rate":    [1.00, 1.00, 1.00, 1.00, 1.00, 1.00,   # 00–05h max charge (cheapest)
                       0.90, 0.55, 0.00, 0.00, 0.00, 0.00,   # 06–11h prices rising, stop
                       0.00, 0.00, 0.00, 0.00, 0.00, 0.00,   # 12–17h expensive, no charge
                       0.00, 0.00, 0.00, 0.00, 0.52, 1.00],  # 18–23h prices easing
    "discharge_rate": [0.00, 0.00, 0.00, 0.00, 0.00, 0.00,   # 00–05h no discharge
                       0.00, 0.22, 0.72, 1.00, 1.00, 0.95,   # 06–11h prices rising
                       0.90, 0.90, 0.95, 1.00, 1.00, 0.95,   # 12–17h expensive hours
                       0.88, 0.72, 0.52, 0.25, 0.00, 0.00],  # 18–23h decline
    "soc_percent":    [56, 66, 76, 84, 91, 97,                # 00–05h charging
                       99, 95, 82, 63, 45, 29,                # 06–11h discharge begins
                       17,  9,  6,  5,  7, 12,                # 12–17h near minimum
                       18, 22, 26, 29, 37, 50],               # 18–23h recovering
}

# ── BACKUP + OPPORTUNISTIC ───────────────────────────────────────────────────
# Goal: maintain 80–90% SoC always for backup power in case of grid outage
# Opportunistic: small ToU arbitrage when SoC is above target (85%+)
# Never deep-discharges — always ready for emergency
backup = {
    "charge_rate":    [0.30, 0.30, 0.30, 0.30, 0.30, 0.30,   # 00–05h maintenance charge
                       0.20, 0.10, 0.00, 0.00, 0.00, 0.00,   # 06–11h tapering
                       0.00, 0.00, 0.00, 0.10, 0.20, 0.30,   # 12–17h slow recharge
                       0.30, 0.20, 0.20, 0.20, 0.30, 0.30],  # 18–23h maintaining
    "discharge_rate": [0.00, 0.00, 0.00, 0.00, 0.00, 0.00,   # 00–05h no discharge
                       0.00, 0.00, 0.12, 0.18, 0.18, 0.12,   # 06–11h opportunistic only
                       0.12, 0.12, 0.10, 0.05, 0.00, 0.00,   # 12–17h minimal
                       0.00, 0.00, 0.00, 0.00, 0.00, 0.00],  # 18–23h back to reserve
    "soc_percent":    [83, 85, 87, 88, 89, 90,                # 00–05h rising slightly
                       89, 88, 86, 84, 82, 81,                # 06–11h small discharge
                       81, 82, 83, 84, 85, 86,                # 12–17h recovering
                       86, 86, 86, 86, 85, 84],               # 18–23h stable
}

print("✅ Strategy profiles defined")

# ── CELL 2: Build DataFrame ───────────────────────────────────────────────────

strategies_data = {
    "peak_shaving":     ("Peak-Shaving",              peak_shaving),
    "self_consumption": ("Self-Consumption",           self_consumption),
    "tou":              ("Time-of-Use (ToU)",          tou),
    "backup":           ("Backup + Opportunistic",     backup),
}

rows = []
for strategy_key, (strategy_label, profile) in strategies_data.items():
    for hour in range(24):
        hour_label = f"{hour:02d}:00"
        price = german_price_eur_mwh[hour]
        price_index = round((price / daily_avg_price) * 100, 1)

        rows.append({
            "strategy":          strategy_key,
            "strategy_label":    strategy_label,
            "hour_of_day":       hour,
            "hour_label":        hour_label,
            "charge_rate":       round(profile["charge_rate"][hour], 3),
            "discharge_rate":    round(profile["discharge_rate"][hour], 3),
            "soc_percent":       profile["soc_percent"][hour],
            "grid_price_eur_mwh":   price,
            "grid_price_index":  price_index,  # 100 = daily average
            "is_cheap_hour":     "Yes" if price < daily_avg_price * 0.80 else "No",
            "is_peak_price_hour":"Yes" if price > daily_avg_price * 1.20 else "No",
        })

pdf = pd.DataFrame(rows)

# Sort for readability
pdf = pdf.sort_values(["strategy", "hour_of_day"]).reset_index(drop=True)

print(f"Total rows: {len(pdf)}")
print(pdf[["strategy", "hour_label", "charge_rate", "discharge_rate", "soc_percent", "grid_price_eur_mwh"]].head(12))

# ── CELL 3: Convert to Spark and save to Lakehouse ───────────────────────────

schema = StructType([
    StructField("strategy",            StringType(),  False),
    StructField("strategy_label",      StringType(),  False),
    StructField("hour_of_day",         IntegerType(), False),
    StructField("hour_label",          StringType(),  False),
    StructField("charge_rate",         DoubleType(),  False),
    StructField("discharge_rate",      DoubleType(),  False),
    StructField("soc_percent",         IntegerType(), False),
    StructField("grid_price_eur_mwh",  DoubleType(),  False),
    StructField("grid_price_index",    DoubleType(),  False),
    StructField("is_cheap_hour",       StringType(),  False),
    StructField("is_peak_price_hour",  StringType(),  False),
])

sdf = spark.createDataFrame(pdf, schema=schema)

sdf.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("gold_battery_hourly_profile")

print("✅ gold_battery_hourly_profile saved to Lakehouse")

# ── CELL 4: Verify ────────────────────────────────────────────────────────────

df_check = spark.table("gold_battery_hourly_profile")
print(f"Row count: {df_check.count()}")
print(f"Strategies: {[r[0] for r in df_check.select('strategy_label').distinct().collect()]}")
print("\nPeak-Shaving sample (night vs day):")
df_check.filter("strategy = 'peak_shaving'") \
        .select("hour_label", "charge_rate", "discharge_rate", "soc_percent", "grid_price_eur_mwh") \
        .show(24, truncate=False)

print("\nBackup sample:")
df_check.filter("strategy = 'backup'") \
        .select("hour_label", "soc_percent", "charge_rate", "discharge_rate") \
        .show(24, truncate=False)

# =============================================================================
# AFTER RUNNING THIS NOTEBOOK:
#
# In Power BI Desktop:
# 1. Home → Refresh  (gold_battery_hourly_profile appears in model)
#
# 2. Add new visual — Line and Clustered Column Chart:
#    Position: Replace V1 SoC Monthly Trend (or add below V2)
#    Title: "Hourly Battery Behavior by Strategy"
#
#    Shared X-axis : gold_battery_hourly_profile[hour_label]  (Categorical)
#    Column Y      : gold_battery_hourly_profile[charge_rate]   (label: Charge ↑)
#    Column Y      : gold_battery_hourly_profile[discharge_rate] (label: Discharge ↓)
#    Line Y        : gold_battery_hourly_profile[soc_percent]    (right axis, label: SoC %)
#    Secondary line: gold_battery_hourly_profile[grid_price_index] (label: Price Index)
#
#    Legend/Filter : Add gold_battery_hourly_profile[strategy_label] as Legend
#                   OR add as page slicer (synced with S2 Strategy slicer)
#
#    Format tips:
#    - charge_rate bars: blue (#00B4D8)
#    - discharge_rate bars: amber (#F4A261)
#    - soc_percent line: green (#2DC653), right Y-axis 0–100
#    - grid_price_index line: grey dashed, right Y-axis
#    - X-axis: font 8pt (24 labels)
#    - Sort: by hour_of_day column (Modeling → Sort by Column)
#
# 3. Add a Slicer for gold_battery_hourly_profile[strategy_label]
#    OR sync with existing S2 (if same field name — otherwise separate slicer)
#
# 4. Reference line on SoC axis at 10% (Min SoC) and 80% (optimal charge target)
#
# WHAT THE VISUAL SHOWS (for energy manager):
#   Peak-Shaving  : Night charging 00h–06h, discharge 07h–20h → saves peak demand charge
#   Self-Consumption: PV charging 10h–15h, evening discharge → solar self-use
#   ToU           : Cheap-hour charging, expensive-hour discharge → arbitrage
#   Backup        : Flat 82–90% all day → always ready for outage
#   Price overlay : Shows WHY each strategy charges/discharges when it does
# =============================================================================
