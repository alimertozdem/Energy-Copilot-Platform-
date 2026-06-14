#!/usr/bin/env python3
"""Transform sample_fallback.json to the post-review (2026-06-14) realistic shape.

WHY: the captured snapshot mirrored the raw Fabric output, which had the two
problems this review fixes:
  * 2,962 unresolved alerts (one row per (building,type,DATE)) — unusable;
  * action/abatement savings that summed to >100% of the portfolio bill/emissions.
The live demo serves THIS file when Fabric is unreachable, so it must reflect the
new model: alerts grouped into a small set of ongoing issues with a realistic
resolved split; savings capped to a realistic share of each building's baseline;
a believable mix of action statuses.

Deterministic (seeded per building) so re-runs are stable.
"""
import hashlib
import json
import sys
from datetime import date, datetime, timedelta

SRC = sys.argv[1] if len(sys.argv) > 1 else "/tmp/sf.json"
DST = sys.argv[2] if len(sys.argv) > 2 else "/tmp/sf_new.json"

ANCHOR = date(2026, 4, 30)          # KPI period end = synthetic "today"
ACTIVE_WINDOW_DAYS = 14
ANNUALIZE = 365.25 / 30.0
CAP_EUR, CAP_CO2 = 0.65, 0.75       # mirror the recommendation-engine cap

d = json.load(open(SRC, encoding="utf-8"))


def seed(*parts) -> int:
    h = hashlib.md5("__".join(str(p) for p in parts).encode()).hexdigest()
    return int(h[:8], 16)


# ---------------------------------------------------------------------------
# 1) ALERTS — synthesize a realistic set of grouped ISSUES across the buildings
# ---------------------------------------------------------------------------
# (building, type) issue catalog. severity is the issue's worst; metric/threshold
# and copy are unit-correct per type. Generic types apply to every building;
# feature types only when the building has that asset.
ISSUE_TYPES = [
    # type, severity, applies_fn, metric, threshold, unit, desc, action
    ("CONSUMPTION_SPIKE", "CRITICAL", lambda b: True, 1.34, 1.0, "ratio",
     "Daily consumption repeatedly exceeds the rolling baseline by 30-60%.",
     "Inspect scheduling/After-hours loads; check for a stuck damper or simultaneous heat+cool."),
    ("COP_DEGRADATION", "HIGH", lambda b: True, 2.4, 3.2, "COP",
     "Heating COP has drifted below the expected band on heating days.",
     "Check heat-pump refrigerant charge, defrost cycles and source-side flow."),
    ("HVAC_INEFFICIENCY", "HIGH", lambda b: True, 1.27, 1.0, "ratio",
     "HVAC energy per degree-day is running above the building-type benchmark.",
     "Review setpoints, economiser operation and AHU scheduling."),
    ("HIGH_CARBON_INTENSITY", "MEDIUM", lambda b: True, 0.41, 0.30, "kg/kWh",
     "Carbon intensity per m2 exceeds the reference for this building type.",
     "Shift flexible load off carbon-peak hours; review heating fuel mix."),
    ("OFF_HOURS_LOAD", "MEDIUM", lambda b: True, 0.38, 0.20, "share",
     "A large share of consumption occurs outside occupied hours.",
     "Tighten BMS schedules; audit always-on plug and process loads."),
    ("SETPOINT_DRIFT", "LOW", lambda b: True, 2.6, 1.0, "degC",
     "Zone temperatures drift from setpoint for sustained periods.",
     "Recalibrate zone sensors; check actuator and valve operation."),
    ("SOLAR_UNDERPERFORM", "HIGH", lambda b: b.get("has_pv"), 0.62, 0.78, "PR",
     "PV performance ratio is below threshold despite active generation.",
     "Inspect for soiling, shading or string/inverter faults."),
    ("BATTERY_IDLE", "MEDIUM", lambda b: b.get("has_battery"), 0.04, 0.10, "cycles/day",
     "Battery is cycling far below its dispatch potential.",
     "Review dispatch schedule vs tariff/PV; check inverter limits."),
    ("DATA_GAP", "LOW", lambda b: b.get("has_iot"), 14.0, 24.0, "readings/day",
     "Sensor readings are intermittently missing for this asset.",
     "Check gateway connectivity and sensor power/wiring."),
]
SEV_RANK = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

buildings = d["portfolio_buildings"]["buildings"]
# skip the empty-name placeholder building, if present
buildings = [b for b in buildings if (b.get("name") or "").strip()]

alert_items = []
open_issue_types_by_b = {}   # fabric_building_id -> set of open HIGH/CRITICAL types
counts = {k: 0 for k in (
    "critical", "high", "medium", "low", "total",
    "unresolved_total", "unresolved_critical", "unresolved_high",
    "unresolved_medium", "unresolved_low",
    "unhandled_total", "unhandled_critical", "unhandled_high",
    "acknowledged", "dismissed")}

ack_budget = 4  # a few issues already triaged, for realism

for b in buildings:
    bid = b["fabric_building_id"]
    bname = b.get("name") or bid
    open_issue_types_by_b[bid] = set()
    # pick which issue types this building exhibits (deterministic, 3-6 types)
    candidate = [t for t in ISSUE_TYPES if t[2](b)]
    s = seed(bid, "issues")
    n_types = 3 + (s % 4)                       # 3..6 issue types
    # rotate selection deterministically
    chosen = [candidate[(s + i) % len(candidate)] for i in range(min(n_types, len(candidate)))]
    chosen = list({c[0]: c for c in chosen}.values())  # dedupe by type

    for (atype, sev, _fn, metric, thr, unit, desc, action) in chosen:
        rs = seed(bid, atype)
        # active (open) ~45% of issues, else resolved
        is_open = (rs % 100) < 45
        span_days = 20 + (rs % 130)             # how long the issue has been seen
        first_dt = ANCHOR - timedelta(days=span_days)
        if is_open:
            last_dt = ANCHOR - timedelta(days=(rs % ACTIVE_WINDOW_DAYS))   # recent -> active
        else:
            last_dt = ANCHOR - timedelta(days=ACTIVE_WINDOW_DAYS + 5 + (rs % 90))  # stale
        # occurrence_count: recurs every ~1-4 days over its active span
        freq = 1 + (rs % 4)
        occ = max(1, (last_dt - first_dt).days // freq)

        rank = SEV_RANK[sev]
        counts["total"] += 1
        counts[{0: "critical", 1: "high", 2: "medium", 3: "low"}[rank]] += 1

        if is_open:
            counts["unresolved_total"] += 1
            counts["unresolved_" + {0: "critical", 1: "high", 2: "medium", 3: "low"}[rank]] += 1
            if rank <= 1:
                open_issue_types_by_b[bid].add(atype)
            # a few already acknowledged
            ack = "new"
            if ack_budget > 0 and (rs % 7 == 0):
                ack = "acknowledged"
                ack_budget -= 1
                counts["acknowledged"] += 1
            if ack == "new":
                counts["unhandled_total"] += 1
                if rank == 0:
                    counts["unhandled_critical"] += 1
                elif rank == 1:
                    counts["unhandled_high"] += 1

            dev = round((metric - thr) / thr * 100, 1) if thr else None
            alert_items.append({
                "anomaly_id": f"{bid}__{atype}__{last_dt.isoformat()}",
                "fabric_building_id": bid,
                "building_name": bname,
                "anomaly_type": atype,
                "severity": sev,
                "detected_at": datetime(last_dt.year, last_dt.month, last_dt.day, 6, 0, 0).isoformat(),
                "is_resolved": False,
                "occurrence_count": int(occ),
                "first_detected_at": datetime(first_dt.year, first_dt.month, first_dt.day, 6, 0, 0).isoformat(),
                "last_detected_at": datetime(last_dt.year, last_dt.month, last_dt.day, 6, 0, 0).isoformat(),
                "metric_value": metric,
                "threshold_value": thr,
                "deviation_pct": dev,
                "description": desc,
                "recommended_action": action,
                "ack_status": ack,
                "acknowledged_at": (datetime(last_dt.year, last_dt.month, last_dt.day, 8, 0, 0).isoformat()
                                    if ack != "new" else None),
                "ack_notes": None,
                "can_manage": bool(b.get("subscription_tier")),
            })

# sort open issues worst-first, then most-recent
alert_items.sort(key=lambda a: (SEV_RANK[a["severity"]], a["last_detected_at"]), reverse=False)
alert_items.sort(key=lambda a: SEV_RANK[a["severity"]])

d["alerts"] = {"alerts": alert_items, "severity_counts": counts}

# ---------------------------------------------------------------------------
# 2) PORTFOLIO_BUILDINGS — open_anomalies = distinct OPEN high/critical issue types
# ---------------------------------------------------------------------------
for b in d["portfolio_buildings"]["buildings"]:
    bid = b["fabric_building_id"]
    b["open_anomalies"] = len(open_issue_types_by_b.get(bid, set()))

# ---------------------------------------------------------------------------
# 3) ACTIONS — cap per-building savings to a realistic share of baseline,
#    recompute payback/npv consistently, assign a believable status mix.
# ---------------------------------------------------------------------------
base_by_b = {
    b["fabric_building_id"]: {
        "cost": (b.get("cost_30d_eur") or 0) * ANNUALIZE,
        "co2": (b.get("co2_30d_kg") or 0) * ANNUALIZE,
    }
    for b in d["portfolio_buildings"]["buildings"]
}

acts = d["actions"]["actions"]
# sum per building
sum_eur, sum_co2 = {}, {}
for a in acts:
    bid = a["fabric_building_id"]
    sum_eur[bid] = sum_eur.get(bid, 0) + (a.get("annual_saving_eur") or 0)
    sum_co2[bid] = sum_co2.get(bid, 0) + (a.get("co2_saving_kg") or 0)

status_cycle = ["open", "in_progress", "completed", "open", "completed",
                "in_progress", "open", "dismissed", "open", "completed"]
status_counts = {k: 0 for k in ("open", "in_progress", "completed", "dismissed", "not_applicable", "total")}

for a in acts:
    bid = a["fabric_building_id"]
    base = base_by_b.get(bid, {"cost": 0, "co2": 0})
    cap_e = base["cost"] * CAP_EUR
    cap_c = base["co2"] * CAP_CO2
    se = (cap_e / sum_eur[bid]) if (cap_e and sum_eur.get(bid, 0) > cap_e) else 1.0
    sc = (cap_c / sum_co2[bid]) if (cap_c and sum_co2.get(bid, 0) > cap_c) else 1.0

    orig_sav = a.get("annual_saving_eur") or 0.0
    net_capex = a.get("net_capex_eur") or 0.0
    npv = a.get("npv_eur")
    if se < 1.0 and orig_sav > 0:
        ann = ((npv or 0) + net_capex) / orig_sav
        a["annual_saving_eur"] = round(orig_sav * se, 0)
        if a["annual_saving_eur"] > 0:
            a["payback_years"] = round(net_capex / a["annual_saving_eur"], 1)
            a["npv_eur"] = round(a["annual_saving_eur"] * ann - net_capex, 0)
    if sc < 1.0 and (a.get("co2_saving_kg") or 0) > 0:
        a["co2_saving_kg"] = round(a["co2_saving_kg"] * sc, 0)

    # status mix (deterministic per action)
    st = status_cycle[seed(a.get("action_id", bid), a.get("rank", 0)) % len(status_cycle)]
    a["status"] = st
    status_counts[st] += 1
    status_counts["total"] += 1

d["actions"]["status_counts"] = status_counts

# ---------------------------------------------------------------------------
# 4) ABATEMENT — cap measure CO2 to the same per-building share, recompute totals
# ---------------------------------------------------------------------------
ab = d.get("abatement")
if ab and ab.get("measures"):
    sum_co2_t, sum_sav = {}, {}
    for m in ab["measures"]:
        bid = m["fabric_building_id"]
        sum_co2_t[bid] = sum_co2_t.get(bid, 0) + (m.get("annual_co2_t") or 0)
        sum_sav[bid] = sum_sav.get(bid, 0) + (m.get("annual_saving_eur") or 0)
    for m in ab["measures"]:
        bid = m["fabric_building_id"]
        base = base_by_b.get(bid, {"cost": 0, "co2": 0})
        cap_c_t = base["co2"] / 1000.0 * CAP_CO2
        cap_e = base["cost"] * CAP_EUR
        sc = (cap_c_t / sum_co2_t[bid]) if (cap_c_t and sum_co2_t.get(bid, 0) > cap_c_t) else 1.0
        se = (cap_e / sum_sav[bid]) if (cap_e and sum_sav.get(bid, 0) > cap_e) else 1.0
        # scale BOTH co2 and saving by their per-building caps so MAC stays sane
        if sc < 1.0:
            m["annual_co2_t"] = round((m.get("annual_co2_t") or 0) * sc, 3)
        if se < 1.0:
            m["annual_saving_eur"] = round((m.get("annual_saving_eur") or 0) * se, 0)
        life = m.get("assumed_lifetime_years") or 15
        sav = m.get("annual_saving_eur") or 0
        ncx = m.get("net_capex_eur") or 0
        if (m.get("annual_co2_t") or 0) > 0:
            m["mac_eur_per_t"] = round((ncx / life - sav) / m["annual_co2_t"], 2)
        m["is_profitable"] = (m.get("mac_eur_per_t") or 0) < 0
    # re-sort by mac, rebuild cumulative + totals
    ab["measures"].sort(key=lambda m: (m.get("mac_eur_per_t") if m.get("mac_eur_per_t") is not None else 1e9))
    cum = 0.0
    for m in ab["measures"]:
        cum += m.get("annual_co2_t") or 0
        m["cumulative_co2_t"] = round(cum, 3)
    measures = ab["measures"]
    prof = [m for m in measures if m.get("is_profitable")]
    tot_co2 = sum(m.get("annual_co2_t") or 0 for m in measures)
    t = ab["totals"]
    t["measure_count"] = len(measures)
    t["total_annual_co2_t"] = round(tot_co2, 3)
    t["profitable_annual_co2_t"] = round(sum(m.get("annual_co2_t") or 0 for m in prof), 3)
    t["total_net_capex_eur"] = round(sum(m.get("net_capex_eur") or 0 for m in measures), 2)
    t["profitable_net_capex_eur"] = round(sum(m.get("net_capex_eur") or 0 for m in prof), 2)
    if tot_co2 > 0:
        t["weighted_avg_mac_eur_per_t"] = round(
            sum((m.get("mac_eur_per_t") or 0) * (m.get("annual_co2_t") or 0) for m in measures) / tot_co2, 2)

json.dump(d, open(DST, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("WROTE", DST)
