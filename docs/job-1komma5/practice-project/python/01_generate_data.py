"""
01_generate_data.py — build a realistic, DELIBERATELY DIRTY dataset for a
German dynamic-tariff retail business.

Every defect injected here is a real failure mode from European energy retail.
The list of defects is printed at the end and mirrored in the README.

Output: 4 CSVs in ../data/
"""
import numpy as np, pandas as pd, random
from pathlib import Path

RNG = np.random.default_rng(42)
random.seed(42)
OUT = Path(__file__).resolve().parent.parent / "data"
OUT.mkdir(exist_ok=True, parents=True)

# ---------------------------------------------------------------- 1. PRICES
# Full year 2025, 15-minute MTU (96/day) in LOCAL German time.
# 2025-03-30 is the DST spring-forward day -> that day has only 92 MTUs (23h).
# 2025-10-26 is the autumn day -> 100 MTUs (25h).
# We build in UTC then convert, which is the CORRECT way, so the file is honest
# about DST -- and the learner must handle 92/100-MTU days downstream.
utc_index = pd.date_range("2024-12-31 23:00", "2025-12-31 23:00", freq="15min", tz="UTC")
local = utc_index.tz_convert("Europe/Berlin")
local = local[(local.year == 2025)]
utc_index = local.tz_convert("UTC")

n = len(local)
hour = local.hour + local.minute / 60
doy = local.dayofyear

# Solar-driven "duck curve": deep midday trough, sharp evening peak.
solar_strength = 0.45 + 0.55 * np.sin(np.pi * np.clip((doy - 60) / 245, 0, 1))  # peaks in summer
midday_dip = -48 * solar_strength * np.exp(-((hour - 13.0) ** 2) / 7.0)
morning_peak = 22 * np.exp(-((hour - 8.0) ** 2) / 2.5)
evening_peak = 38 * np.exp(-((hour - 19.0) ** 2) / 3.5)
night_base = -8 * np.exp(-((hour - 3.5) ** 2) / 6.0)
winter_lift = 22 * np.cos(2 * np.pi * (doy - 10) / 365)          # higher in winter
weekend = np.where(local.dayofweek >= 5, -9.0, 0.0)
noise = RNG.normal(0, 9.5, n)
spikes = np.where(RNG.random(n) < 0.0015, RNG.uniform(90, 320, n), 0.0)   # scarcity hours

price = 82 + winter_lift + midday_dip + morning_peak + evening_peak + night_base + weekend + noise + spikes
# Force realistic negative-price clusters on sunny low-demand spring/summer weekends
neg_mask = (solar_strength > 0.72) & (hour > 10.5) & (hour < 15.5) & (local.dayofweek >= 5)
price = np.where(neg_mask & (RNG.random(n) < 0.55), RNG.uniform(-95, -2, n), price)
price = np.round(price, 2)   # EUR / MWh

prices = pd.DataFrame({
    # DEFECT 6: local time WITHOUT offset -> the classic DST ambiguity trap
    "ts_local": local.strftime("%Y-%m-%d %H:%M"),
    "ts_utc": utc_index.strftime("%Y-%m-%dT%H:%M:%SZ"),
    "bidding_zone": "DE-LU",
    "price_eur_mwh": price,
    "resolution": "PT15M",
})

# DEFECT 1a: duplicated rows (exchange re-publication)
dupes = prices.sample(180, random_state=7)
prices = pd.concat([prices, dupes], ignore_index=True)
# DEFECT 2a: missing MTUs (publication gap)
drop_idx = prices.sample(120, random_state=11).index
prices = prices.drop(index=drop_idx)
prices = prices.sample(frac=1, random_state=3).reset_index(drop=True)  # unsorted on purpose
prices.to_csv(OUT / "raw_day_ahead_prices.csv", index=False)

# ------------------------------------------------------------- 2. CUSTOMERS
CITIES = ["Berlin", "Hamburg", "Muenchen", "Koeln", "Leipzig", "Stuttgart"]
DSOS   = ["Stromnetz Berlin", "Stromnetz Hamburg", "SWM Infrastruktur",
          "Rheinnetz", "Netz Leipzig", "Netze BW"]
SEGMENTS = ["PV_only", "PV_battery", "PV_battery_HP", "PV_battery_HP_EV", "no_hardware"]
SEG_W    = [0.16, 0.24, 0.26, 0.20, 0.14]

rows = []
for i in range(30):
    seg = random.choices(SEGMENTS, weights=SEG_W)[0]
    ci = random.randrange(len(CITIES))
    pv   = 0 if seg == "no_hardware" else round(RNG.uniform(6.5, 13.5), 1)
    batt = 0 if seg in ("no_hardware", "PV_only") else float(random.choice([5, 7.5, 10, 12.5, 15]))
    hp   = 1 if "HP" in seg else 0
    ev   = 1 if "EV" in seg else 0
    base = RNG.uniform(2300, 3800)
    if hp: base += RNG.uniform(3500, 6000)
    if ev: base += RNG.uniform(2200, 4200)
    # every 7th customer gets an id that genuinely starts with 0, so the
    # Excel damage below is reproducible rather than luck-dependent
    if i % 7 == 3:
        malo_true = f"{RNG.integers(1, 9999999999):011d}"
    else:
        malo_true = f"{RNG.integers(10000000000, 99999999999):011d}"
    # DEFECT 9: the CRM export went through Excel, which stripped leading zeros.
    # The meter data (machine-to-machine) keeps the correct 11 digits, so a naive
    # join on the raw strings SILENTLY LOSES these customers.
    malo_master = malo_true
    if i % 7 == 3:
        malo_master = malo_true.lstrip("0") or "1"
    rows.append({
        "malo_id": malo_master,
        "_malo_true": malo_true,
        "customer_ref": f"C{1000+i}",
        # DEFECT 10: inconsistent case / stray whitespace in categoricals
        "city": random.choice([CITIES[ci], CITIES[ci].upper(), CITIES[ci].lower(), CITIES[ci] + " "]),
        "dso_name": DSOS[ci],
        "segment": seg,
        "pv_kwp": pv,
        "battery_kwh": batt,
        "has_heat_pump": hp,
        "has_ev": ev,
        "annual_kwh_expected": int(base),
        "tariff_type": random.choices(["DYNAMIC", "FIXED"], weights=[0.68, 0.32])[0],
        "contract_start": (pd.Timestamp("2024-09-01") + pd.Timedelta(days=int(RNG.integers(0, 200)))).strftime("%Y-%m-%d"),
        # DEFECT 11: two customers exist in the meter file but NOT here (orphans) -> handled below
        "reporting_unit": "KWH",
    })
cust = pd.DataFrame(rows)
# DEFECT 7: three customers report average POWER (kW) not ENERGY (kWh) per interval
cust.loc[cust.index[[2, 13, 21]], "reporting_unit"] = "KW"
# DEFECT 11: remove 2 customers from master so the meter file has orphan MaLos
orphans = cust.iloc[[27, 28]].copy()
cust = cust.drop(index=cust.index[[27, 28]]).reset_index(drop=True)
cust.drop(columns=["_malo_true"]).to_csv(OUT / "raw_customers.csv", index=False)

# --------------------------------------------------------- 3. METER READINGS
# 2025-02-01 .. 2025-04-30 (includes the 23-hour DST day 2025-03-30)
all_cust = pd.concat([cust, orphans], ignore_index=True)
m_utc = pd.date_range("2025-01-31 23:00", "2025-04-30 22:45", freq="15min", tz="UTC")
m_loc = m_utc.tz_convert("Europe/Berlin")
mh = m_loc.hour + m_loc.minute / 60
mdoy = m_loc.dayofyear
mdow = m_loc.dayofweek

frames = []
for _, c in all_cust.iterrows():
    k = len(m_loc)
    annual = c["annual_kwh_expected"]
    per_interval = annual / 35040.0
    # household shape: morning + evening peaks, weekend flatter
    shape = (0.55
             + 0.85 * np.exp(-((mh - 7.5) ** 2) / 3.0)
             + 1.35 * np.exp(-((mh - 19.5) ** 2) / 5.0)
             + 0.20 * np.exp(-((mh - 12.5) ** 2) / 8.0))
    shape = shape * np.where(mdow >= 5, 1.10, 1.0)
    seasonal = 1.0 + 0.32 * np.cos(2 * np.pi * (mdoy - 15) / 365)   # winter heavier
    load = per_interval * shape * seasonal * RNG.normal(1.0, 0.16, k)
    if c["has_heat_pump"]:
        load += per_interval * 1.5 * np.clip((10 - (mdoy / 12)), 0.4, 1.5) * np.where((mh < 8) | (mh > 16), 1.25, 0.55)
    if c["has_ev"]:
        charging = (RNG.random(k) < 0.055) & (mh > 21.5) | (RNG.random(k) < 0.02) & (mh < 6)
        load += np.where(charging, 11 * 0.25 * RNG.uniform(0.7, 1.0, k), 0.0)
    load = np.clip(load, 0.0005, None)
    if c["reporting_unit"] == "KW":
        load = load / 0.25   # DEFECT 7: reported as average kW over the interval

    df = pd.DataFrame({
        "malo_id": c["_malo_true"],
        # DEFECT 6: naive local timestamps, no offset -> DST gap/overlap unresolved
        "interval_start_local": m_loc.strftime("%Y-%m-%d %H:%M"),
        "value": np.round(load, 4),
        "unit": c["reporting_unit"],
        "status": np.where(RNG.random(k) < 0.965, "V", np.where(RNG.random(k) < 0.6, "E", "")),
        "source": "MSCONS",
    })
    frames.append(df)

meter = pd.concat(frames, ignore_index=True)

# DEFECT 5: German timestamp format on a subset of rows (DD.MM.YYYY HH:MM)
alt = meter.sample(frac=0.09, random_state=5).index
meter.loc[alt, "interval_start_local"] = pd.to_datetime(
    meter.loc[alt, "interval_start_local"]).dt.strftime("%d.%m.%Y %H:%M")

# DEFECT 4: German decimal comma on a subset -> column becomes text
meter["value"] = meter["value"].astype(str)
comma = meter.sample(frac=0.11, random_state=6).index
meter.loc[comma, "value"] = meter.loc[comma, "value"].str.replace(".", ",", regex=False)

# DEFECT 8: PV export leaked into the consumption register as negatives
neg = meter.sample(frac=0.004, random_state=8).index
meter.loc[neg, "value"] = ("-" + meter.loc[neg, "value"].str.lstrip("-"))

# DEFECT 3: hard NULLs
nul = meter.sample(frac=0.006, random_state=9).index
meter.loc[nul, "value"] = ""

# DEFECT 1b: duplicated MSCONS re-sends
d = meter.sample(frac=0.012, random_state=10)
meter = pd.concat([meter, d], ignore_index=True)

# DEFECT 2b: missing intervals (transmission gaps), clustered per customer
gap_idx = meter.sample(frac=0.009, random_state=12).index
meter = meter.drop(index=gap_idx)

meter = meter.sample(frac=1, random_state=13).reset_index(drop=True)
meter.to_csv(OUT / "raw_meter_readings.csv", index=False)

# ------------------------------------------------------------ 4. MaKo EVENTS
# The supplier-switching funnel. Realistic failure distribution by DSO.
REJECTS = {
    "E_0001": "MaLo-ID unknown at DSO",
    "E_0018": "Master data mismatch (name/address)",
    "E_0025": "Existing supply contract not terminated",
    "E_0099": "Requested supply start date not permitted",
    "E_0031": "Metering point not yet commissioned",
}
DSO_QUALITY = {  # probability the first UTILMD is rejected
    "Stromnetz Berlin": 0.14, "Stromnetz Hamburg": 0.11, "SWM Infrastruktur": 0.19,
    "Rheinnetz": 0.34, "Netz Leipzig": 0.22, "Netze BW": 0.16,
}
ev = []
for _, c in cust.iterrows():
    t0 = pd.Timestamp(c["contract_start"])
    malo, dso = c["_malo_true"], c["dso_name"]
    def add(stage, ts, code="", note=""):
        ev.append({"malo_id": malo, "dso_name": dso, "stage": stage,
                   "event_ts": ts.strftime("%Y-%m-%d %H:%M:%S"),
                   "message_type": {"CONTRACT_SIGNED": "", "UTILMD_SENT": "UTILMD",
                                    "CONTRL_ACK": "CONTRL", "APERAK_REJECT": "APERAK",
                                    "SUPPLY_START": "UTILMD", "FIRST_INVOICE": "INVOIC"}[stage],
                   "error_code": code, "note": note})
    add("CONTRACT_SIGNED", t0)
    t = t0 + pd.Timedelta(days=int(RNG.integers(1, 5)))
    add("UTILMD_SENT", t)
    attempts, rejected_once = 0, False
    while attempts < 3:
        attempts += 1
        if RNG.random() < DSO_QUALITY[dso]:
            rejected_once = True
            code = random.choices(list(REJECTS), weights=[0.30, 0.28, 0.18, 0.14, 0.10])[0]
            t = t + pd.Timedelta(days=int(RNG.integers(2, 9)))
            add("APERAK_REJECT", t, code, REJECTS[code])
            t = t + pd.Timedelta(days=int(RNG.integers(1, 12)))   # manual clearing latency
            add("UTILMD_SENT", t)
        else:
            t = t + pd.Timedelta(days=int(RNG.integers(1, 4)))
            add("CONTRL_ACK", t)
            break
    else:
        continue   # never acknowledged -> stuck in limbo, no supply start
    t = t + pd.Timedelta(days=int(RNG.integers(9, 26)))
    add("SUPPLY_START", t)
    if RNG.random() > 0.06:      # a few first invoices never go out
        t = t + pd.Timedelta(days=int(RNG.integers(28, 62)))
        add("FIRST_INVOICE", t)
mako = pd.DataFrame(ev).sample(frac=1, random_state=14).reset_index(drop=True)
mako.to_csv(OUT / "raw_mako_events.csv", index=False)

print("=" * 74)
for f in ["raw_day_ahead_prices.csv", "raw_customers.csv",
          "raw_meter_readings.csv", "raw_mako_events.csv"]:
    p = OUT / f
    print(f"{f:34s} {len(pd.read_csv(p, dtype=str)):>9,d} rows  {p.stat().st_size/1e6:6.2f} MB")
print("=" * 74)
print("""INJECTED DEFECTS (each one is a real energy-retail failure mode)
 1  Duplicate rows            re-published prices / re-sent MSCONS
 2  Missing intervals         publication + transmission gaps
 3  Hard NULL values          empty value field
 4  German decimal comma      "0,2513" -> column parses as TEXT
 5  Mixed timestamp formats   ISO vs DD.MM.YYYY HH:MM
 6  Naive local timestamps    DST: 2025-03-30 has 92 MTUs, not 96
 7  kW vs kWh confusion       3 customers report average POWER
 8  Negative consumption      PV export leaked into import register
 9  Broken MaLo-ID            Excel stripped the leading zero in the CRM export
                              -> a naive join SILENTLY drops those customers
10  Dirty categoricals        "Berlin" / "BERLIN" / "berlin" / "Berlin "
11  Orphan foreign keys       2 MaLos in meter data, absent from master
12  Funnel dead ends          switches never acknowledged / never invoiced""")
