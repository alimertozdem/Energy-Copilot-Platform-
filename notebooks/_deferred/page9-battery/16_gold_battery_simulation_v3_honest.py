# =============================================================================
# NOTEBOOK 16 — gold_battery_simulation v3 (HONEST: Measured + Modeled + Prospect)
# File   : 16_gold_battery_simulation_v3_honest.py
# Date   : 2026-06-22  (rev2: re-add pv_sc_adjustment + strategy_factor columns
#                        that the published model still references — without them
#                        DirectLake reframe fails: "cannot access source column
#                        pv_sc_adjustment". They are kept with meaningful values.)
# Replaces: notebook 14 (anchor x heuristic-factor approach — fabricated savings)
#
# WHY:
#   Verified against live Fabric (2026-06-22): gold_battery_dispatch contains REAL
#   economics for only the INSTALLED strategy of 3 buildings (B001 self_consumption,
#   B003 peak_shaving, B005 backup). There is NO dispatch for alternative strategies,
#   and B004/B006 have no battery at all. The old simulation invented all of it via
#   anchor x fixed factors (e.g. backup->peak 4.55x), and its capacities did not even
#   match dispatch (B003 sim=5600 kWh vs real=800 kWh). Payback/IRR were then masked
#   with 25yr / 35% display caps.
#
# THIS NOTEBOOK — every row is labelled by `data_basis`:
#   "Measured"  -> the building's installed strategy, annualised from real dispatch.
#   "Modeled"   -> alternative strategies for a building that HAS a battery,
#                  estimated from that building's OWN physics (price, power, capacity,
#                  PV). Transparent, no magic factor.
#   "Prospect"  -> buildings with NO battery yet (B004, B006): pure physics estimate,
#                  flagged so the report can show "if installed" without faking it.
#
#   No display caps. Real screening numbers; payback can be long where it should be.
# =============================================================================

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (StructType, StructField, StringType, DoubleType)
from datetime import datetime, timezone

spark = SparkSession.builder.getOrCreate()

# =============================================================================
# ENERGY ASSUMPTIONS  ---  PRODUCT-OWNER REVIEW SURFACE (Mert, energy reviewer)
# Screening-grade. Change a NUMBER here; do not touch the logic below.
# Plausible ranges in [ ]. These drive every "Modeled"/"Prospect" euro.
# =============================================================================
DOD = {"LFP": 0.90, "NMC": 0.80}                 # usable depth-of-discharge   [LFP .80-.95, NMC .70-.85]
CYCLES_PER_YR = {                                # full-equivalent cycles / year, by strategy
    "peak_shaving":     250,                     #   [200-300] daily-ish, demand-driven
    "tou":              330,                     #   [300-350] near-daily arbitrage
    "self_consumption": 300,                     #   [250-330] PV-driven
    "backup":           120,                     #   [80-160] mostly idle, opportunistic
}
COINCIDENCE   = 0.45      # share of billing-demand peak the battery actually shaves [0.30-0.60]
PV_YIELD      = 950.0     # kWh per kWp per year (DE/EU avg; DK/NL similar)          [850-1050]
PV_SURPLUS_FRAC = 0.40    # share of PV generation that is exportable surplus        [0.25-0.55]
BACKUP_UTIL   = 0.50      # backup runs shallow -> fraction of arbitrage realised    [0.30-0.70]
COST_PER_KWH  = {"LFP": 135.0, "NMC": 125.0}     # battery hardware EUR/kWh, DE 2026  [LFP 130-180, NMC 120-160]
INSTALL_OVERHEAD = 0.08   # install / balance-of-system on top of hardware           [0.05-0.15]

# Financials
DISCOUNT_RATE  = 0.05     # 5% EU energy-investment discount rate
INFLATION_RATE = 0.025    # 2.5% energy-price inflation
NPV_HORIZON_YR = 10
SALVAGE_PCT    = 0.15     # residual value at year 10

# =============================================================================
# BUILDING CONFIG  ---  physical reality.
#   capacity_kwh: matches gold_battery_dispatch (NOT the old inflated sim).
#   has_battery=False -> Prospect (B004 Wien, B006 Amsterdam: no install yet).
#   active: installed strategy (from dispatch). None for prospects.
#   B007 has a battery but its dispatch net_savings is NULL (generator bug) -> until
#   notebook 12/15 is fixed it is treated as Modeled (no Measured anchor yet).
# =============================================================================
BUILDINGS = [
    {"building_id": "B001", "building_name": "Berliner Bürogebäude Alpha", "country": "DE",
     "chem": "LFP", "capacity_kwh": 200.0, "power_kw": 100.0, "pv_kwp": 120.0, "rte": 0.945,
     "has_battery": True,  "active": "self_consumption"},
    {"building_id": "B003", "building_name": "Hamburg Logistics Hub Gamma", "country": "DE",
     "chem": "LFP", "capacity_kwh": 800.0, "power_kw": 400.0, "pv_kwp": 500.0, "rte": 0.950,
     "has_battery": True,  "active": "peak_shaving"},
    {"building_id": "B004", "building_name": "Wien Grand Hotel Delta", "country": "AT",
     "chem": "LFP", "capacity_kwh": 400.0, "power_kw": 200.0, "pv_kwp": 80.0,  "rte": 0.940,
     "has_battery": False, "active": None},
    {"building_id": "B005", "building_name": "Frankfurt Klinikum Epsilon", "country": "DE",
     "chem": "NMC", "capacity_kwh": 400.0, "power_kw": 180.0, "pv_kwp": 200.0, "rte": 0.900,
     "has_battery": True,  "active": "backup"},
    {"building_id": "B006", "building_name": "Amsterdam Universiteit Zeta", "country": "NL",
     "chem": "LFP", "capacity_kwh": 600.0, "power_kw": 300.0, "pv_kwp": 150.0, "rte": 0.935,
     "has_battery": False, "active": None},
    {"building_id": "B007", "building_name": "Copenhagen Net-Plus HQ Eta", "country": "DK",
     "chem": "LFP", "capacity_kwh": 450.0, "power_kw": 225.0, "pv_kwp": 380.0, "rte": 0.950,
     "has_battery": True,  "active": "self_consumption"},
]

STRATEGIES = ["peak_shaving", "tou", "self_consumption", "backup"]
STRATEGY_LABELS = {
    "peak_shaving": "Peak-Shaving", "tou": "Time-of-Use (ToU)",
    "self_consumption": "Self-Consumption", "backup": "Backup + Opportunistic",
}
EU_COMPLIANT = {"LFP": True, "NMC": False}   # EU 2023/1542: LFP ok, NMC fails carbon/recycled thresholds

# --- prices from gold_country_regulations (fallback dict if the read fails) ---
PRICE_FALLBACK = {
    "DE": {"peak": 0.285, "off": 0.062, "demand": 13.50, "feed_in": 0.082, "co2": 338.0},
    "AT": {"peak": 0.248, "off": 0.055, "demand": 11.20, "feed_in": 0.075, "co2": 162.0},
    "NL": {"peak": 0.302, "off": 0.071, "demand": 14.80, "feed_in": 0.108, "co2": 355.0},
    "DK": {"peak": 0.198, "off": 0.048, "demand":  8.90, "feed_in": 0.068, "co2": 135.0},
}
try:
    _regs = {r["country_code"]: r for r in spark.table("gold_country_regulations").collect()}
    def price(cc):
        r = _regs.get(cc)
        if r is None:
            return PRICE_FALLBACK[cc]
        return {"peak": float(r["grid_price_peak_eur_per_kwh"]),
                "off": float(r["grid_price_offpeak_eur_per_kwh"]),
                "demand": float(r["demand_charge_eur_per_kw_month"]),
                "feed_in": float(r["feed_in_tariff_eur_per_kwh"]),
                "co2": float(r["co2_intensity_grid_g_per_kwh"])}
    print("[prices] loaded from gold_country_regulations")
except Exception as e:
    print(f"[prices] fallback dict ({e})")
    def price(cc):
        return PRICE_FALLBACK[cc]

# --- measured annual savings + CO2 per building, from REAL dispatch -----------
disp = spark.table("gold_battery_dispatch").filter("is_simulated = false")
measured = {}
for r in (disp.groupBy("building_id")
              .agg(F.sum("net_savings_eur").alias("net"),
                   F.sum("co2_avoided_kg").alias("co2"),
                   F.countDistinct("date").alias("days")).collect()):
    days = r["days"] or 0
    yrs = days / 365.25 if days else 0.0
    if r["net"] is not None and yrs > 0:
        measured[r["building_id"]] = {"sav": float(r["net"]) / yrs,
                                      "co2": float(r["co2"] or 0.0) / yrs}
print(f"[measured] buildings with real dispatch economics: {sorted(measured.keys())}")

# --- physics: annual EUR savings for one strategy at one building -------------
def model_strategy(b, strat, p):
    usable = b["capacity_kwh"] * DOD[b["chem"]]
    rte    = b["rte"]
    spread = max(0.0, p["peak"] - p["off"])
    arbitrage = usable * CYCLES_PER_YR[strat] * spread * rte
    if strat == "peak_shaving":
        demand = b["power_kw"] * p["demand"] * 12.0 * COINCIDENCE
        return demand + arbitrage
    if strat == "tou":
        return arbitrage
    if strat == "self_consumption":
        pv_surplus_kwh = b["pv_kwp"] * PV_YIELD * PV_SURPLUS_FRAC
        captured = min(pv_surplus_kwh, usable * CYCLES_PER_YR["self_consumption"])
        return captured * max(0.0, p["peak"] - p["feed_in"]) * rte
    if strat == "backup":
        return arbitrage * BACKUP_UTIL
    return 0.0

def model_co2_kg(b, strat, p):
    usable = b["capacity_kwh"] * DOD[b["chem"]]
    annual_throughput = usable * CYCLES_PER_YR[strat] * b["rte"]
    return annual_throughput * (p["co2"] / 1000.0)   # kWh shifted x gCO2/kWh -> kg

def npv(sav, capex):
    if sav <= 0 or capex <= 0:
        return -capex
    cfs = [-capex]
    for y in range(1, NPV_HORIZON_YR + 1):
        cf = sav * ((1 + INFLATION_RATE) ** y)
        if y == NPV_HORIZON_YR:
            cf += capex * SALVAGE_PCT
        cfs.append(cf)
    return sum(cf / ((1 + DISCOUNT_RATE) ** i) for i, cf in enumerate(cfs))

def irr_pct(sav, capex):
    if sav <= 0 or capex <= 0:
        return None
    cfs = [-capex]
    for y in range(1, NPV_HORIZON_YR + 1):
        cf = sav * ((1 + INFLATION_RATE) ** y)
        if y == NPV_HORIZON_YR:
            cf += capex * SALVAGE_PCT
        cfs.append(cf)
    r = sav / capex
    for _ in range(200):
        f  = sum(cf / ((1 + r) ** i) for i, cf in enumerate(cfs))
        df = sum(-i * cf / ((1 + r) ** (i + 1)) for i, cf in enumerate(cfs) if i > 0)
        if abs(df) < 1e-12:
            break
        r -= f / df
        if r <= -0.99:
            r = -0.99
    return round(r * 100.0, 1)   # NO display cap — show the real value

def comparison_score(irr_v, payback, co2_kg, eu_ok, basis):
    s_irr = min(40.0, max(0.0, (irr_v or 0.0) * 1.5))          # 27% IRR -> full 40
    s_pay = max(0.0, min(30.0, 30.0 - ((payback or 25.0) - 3.0) * 2.5))  # 3yr->30, 15yr->0
    s_co2 = min(20.0, (co2_kg or 0.0) / 5000.0)
    s_eu  = 10.0 if eu_ok else 0.0
    score = s_irr + s_pay + s_co2 + s_eu
    if basis == "Prospect (no battery yet)":
        score *= 0.80   # never let an un-installed prospect outrank a measured install
    return round(max(0.0, min(100.0, score)), 1)

# --- build rows ---------------------------------------------------------------
rows = []
for b in BUILDINGS:
    p = price(b["country"])
    capex = round(b["capacity_kwh"] * COST_PER_KWH[b["chem"]] * (1.0 + INSTALL_OVERHEAD), 0)
    eu_ok = EU_COMPLIANT[b["chem"]]
    has_meas = (b["building_id"] in measured) and b["has_battery"] and (b["active"] is not None)
    # legacy column kept for model compatibility: PV/battery ratio vs ideal 0.5 kWp/kWh
    pv_adj = round(min(1.0, (b["pv_kwp"] / max(b["capacity_kwh"], 1.0)) / 0.5), 3)

    # pass 1 — savings / co2 / basis per strategy
    per = {}
    for strat in STRATEGIES:
        if has_meas and strat == b["active"]:
            sav = round(measured[b["building_id"]]["sav"], 0)
            co2 = round(measured[b["building_id"]]["co2"], 0)
            basis = "Measured"
        elif b["has_battery"]:
            sav = round(model_strategy(b, strat, p), 0)
            co2 = round(model_co2_kg(b, strat, p), 0)
            basis = "Modeled"
        else:
            sav = round(model_strategy(b, strat, p), 0)
            co2 = round(model_co2_kg(b, strat, p), 0)
            basis = "Prospect (no battery yet)"
        per[strat] = {"sav": sav, "co2": co2, "basis": basis}
    max_sav = max((v["sav"] for v in per.values()), default=0.0)

    # pass 2 — emit
    for strat in STRATEGIES:
        sav   = per[strat]["sav"]
        co2   = per[strat]["co2"]
        basis = per[strat]["basis"]
        payback = round(capex / sav, 1) if sav and sav > 0 else None
        npv_v   = round(npv(sav, capex), 0)
        irr_v   = irr_pct(sav, capex)
        score   = comparison_score(irr_v, payback, co2, eu_ok, basis)
        is_active = (has_meas and strat == b["active"])
        # legacy column kept for model compatibility: this strategy's savings vs the
        # building's best strategy (1.0 = best). Replaces the old fixed 4.55x factors.
        strategy_factor = round(sav / max_sav, 3) if max_sav > 0 else 0.0

        rows.append({
            "scenario_id":       f"{b['building_id']}_{strat[:3].upper()}_{int(b['capacity_kwh'])}kWh",
            "scenario_label":    f"{b['building_name'].split()[0]} - {STRATEGY_LABELS[strat]} - {int(b['capacity_kwh'])} kWh {b['chem']}",
            "building_id":       b["building_id"],
            "building_name":     b["building_name"],
            "country_code":      b["country"],
            "battery_type":      b["chem"],
            "eu_compliant":      str(eu_ok),
            "battery_capacity_kwh": b["capacity_kwh"],
            "pv_capacity_kwp":   b["pv_kwp"],
            "battery_cost_eur":  round(b["capacity_kwh"] * COST_PER_KWH[b["chem"]], 0),
            "total_capex_eur":   capex,
            "strategy":          strat,
            "strategy_label":    STRATEGY_LABELS[strat],
            "annual_savings_eur": sav,
            "annual_co2_avoided_kg": co2,
            "payback_years":     payback,
            "npv_10yr_eur":      npv_v,
            "irr_percent":       irr_v,
            "avg_round_trip_efficiency_pct": round(b["rte"] * 100, 1),
            "comparison_score":  score,
            "is_active_strategy": str(is_active),
            "pv_sc_adjustment":  pv_adj,          # legacy col — model references it
            "strategy_factor":   strategy_factor, # legacy col — model references it
            "data_basis":        basis,           # NEW: Measured / Modeled / Prospect
            "processed_at":      datetime.now(timezone.utc).isoformat(),
        })

# --- schema + write -----------------------------------------------------------
schema = StructType([
    StructField("scenario_id", StringType(), False),
    StructField("scenario_label", StringType(), False),
    StructField("building_id", StringType(), False),
    StructField("building_name", StringType(), False),
    StructField("country_code", StringType(), False),
    StructField("battery_type", StringType(), False),
    StructField("eu_compliant", StringType(), False),
    StructField("battery_capacity_kwh", DoubleType(), False),
    StructField("pv_capacity_kwp", DoubleType(), False),
    StructField("battery_cost_eur", DoubleType(), False),
    StructField("total_capex_eur", DoubleType(), False),
    StructField("strategy", StringType(), False),
    StructField("strategy_label", StringType(), False),
    StructField("annual_savings_eur", DoubleType(), False),
    StructField("annual_co2_avoided_kg", DoubleType(), False),
    StructField("payback_years", DoubleType(), True),
    StructField("npv_10yr_eur", DoubleType(), True),
    StructField("irr_percent", DoubleType(), True),
    StructField("avg_round_trip_efficiency_pct", DoubleType(), False),
    StructField("comparison_score", DoubleType(), False),
    StructField("is_active_strategy", StringType(), False),
    StructField("pv_sc_adjustment", DoubleType(), False),
    StructField("strategy_factor", DoubleType(), False),
    StructField("data_basis", StringType(), False),
    StructField("processed_at", StringType(), False),
])

import pandas as pd
pdf = pd.DataFrame(rows)
sdf = spark.createDataFrame(pdf, schema=schema)

assert sdf.count() == len(BUILDINGS) * len(STRATEGIES), "row count mismatch"
assert sdf.filter("annual_savings_eur < 0").count() == 0, "negative savings"

print("\n[preview] building x strategy (sav / payback / basis):")
sdf.select("building_id", "strategy_label", "battery_type", "data_basis",
           "annual_savings_eur", "total_capex_eur", "payback_years", "irr_percent",
           "is_active_strategy").orderBy("building_id", F.col("comparison_score").desc()).show(40, truncate=False)

sdf.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
   .saveAsTable("gold_battery_simulation")
print("OK gold_battery_simulation rebuilt (Measured + Modeled + Prospect, no caps, legacy cols kept).")

# =============================================================================
# AFTER RUNNING:
#   1) Fabric Service -> semantic model EnergyCopilotModel -> Refresh now
#      (reframe now succeeds: pv_sc_adjustment + strategy_factor exist again).
#   2) Power BI -> the scenario table shows real per-building values (B003 800 kWh,
#      capex 116,640, etc.).
#   3) data_basis is a NEW column — add it to the model/table to show the
#      Measured/Modeled/Prospect badge.
#   4) B007 still Modeled until its dispatch net_savings NULL is fixed (nb 12/15).
# =============================================================================
