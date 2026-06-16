"""Solar telemetry roll-up: bronze_iot_readings -> gold_solar_daily (Postgres, EUR0).

Turns per-reading inverter/SCADA telemetry into DAILY solar KPIs for connected
buildings, WITHOUT Fabric. Energy logic -- assumptions stated, no invented values:

  * generated_kwh: prefer the day's ENERGY-COUNTER delta (max-min of an energy
    sensor); else integrate AC power (kW) over time (trapezoidal). Gaps > MAX_GAP_H
    are not integrated across.
  * avg_solar_pr (IEC 61724): generated / (pv_capacity_kwp * in-plane irradiation),
    irradiation = integral of irradiance(W/m2)/1000 dt. Clamped to
    [0, PR_MAX_PLAUSIBLE]; NULL when irradiation < MIN_IRRADIATION_KWH_M2 or capacity
    unknown.
  * self_consumed / exported: computed ONLY when BOTH a PV power series AND a
    building-load power series exist for the day:
        self_consumed = integral of min(P_pv, P_load) dt  (on the merged timeline),
                        capped at generated;
        exported      = generated - self_consumed.
    Inverter-only telemetry (no load meter) leaves both NULL -- never estimated.
    Assumes the load sensor is the building's TOTAL consumption power.
"""
from collections import defaultdict
from datetime import date, datetime
from typing import Any, Iterable

# sensor_type vocab (edge configs tag these; matched case-insensitively)
PV_POWER = {"pv_ac_power", "solar_ac_power", "pv_power", "ac_power"}
PV_ENERGY = {"pv_energy_today_kwh", "solar_generated_kwh", "pv_energy_kwh", "ac_energy_kwh"}
IRRADIANCE = {"irradiance", "poa_irradiance", "solar_irradiance"}
LOAD = {"building_kwh", "building_power", "building_load_kw", "main_power_kw"}

PR_MAX_PLAUSIBLE = 1.1          # same cap as 03_gold_kpi_engine
MIN_IRRADIATION_KWH_M2 = 0.05   # below this, PR denominator is noise -> NULL
MAX_GAP_H = 6.0                 # do not integrate across holes larger than this


def _trapz(series: list[tuple[datetime, float]]) -> float:
    """Trapezoidal integral of a kW series -> kWh. series sorted by ts."""
    total = 0.0
    for (t0, v0), (t1, v1) in zip(series, series[1:]):
        dt_h = (t1 - t0).total_seconds() / 3600.0
        if dt_h <= 0 or dt_h > MAX_GAP_H:
            continue
        total += 0.5 * (v0 + v1) * dt_h
    return total


def _interp(series: list[tuple[datetime, float]], t: datetime):
    """Linear value of a sorted (ts, kw) series at t (kw clamped >= 0). t is assumed
    within [series[0].ts, series[-1].ts]."""
    if not series:
        return None
    if t <= series[0][0]:
        return max(0.0, series[0][1])
    if t >= series[-1][0]:
        return max(0.0, series[-1][1])
    for (t0, v0), (t1, v1) in zip(series, series[1:]):
        if t0 <= t <= t1:
            span = (t1 - t0).total_seconds()
            if span <= 0:
                return max(0.0, v0)
            f = (t - t0).total_seconds() / span
            return max(0.0, v0 + f * (v1 - v0))
    return None


def _self_consumption_kwh(pv: list, load: list):
    """integral of min(P_pv, P_load) dt over the overlap window, kWh. None if
    either series is too short or they do not overlap."""
    if len(pv) < 2 or len(load) < 2:
        return None
    lo = max(pv[0][0], load[0][0])
    hi = min(pv[-1][0], load[-1][0])
    if hi <= lo:
        return None
    union = sorted({t for t, _ in pv if lo <= t <= hi}
                   | {t for t, _ in load if lo <= t <= hi} | {lo, hi})
    pts = []
    for t in union:
        p = _interp(pv, t)
        ld = _interp(load, t)
        if p is None or ld is None:
            continue
        pts.append((t, min(p, ld)))
    return _trapz(pts)


def _classify(sensor_type: str) -> str | None:
    s = (sensor_type or "").strip().lower()
    if s in PV_POWER:
        return "power"
    if s in PV_ENERGY:
        return "energy"
    if s in IRRADIANCE:
        return "irr"
    if s in LOAD:
        return "load"
    return None


def rollup_readings(
    readings: Iterable[dict[str, Any]], capacity_kwp: float | None
) -> list[dict[str, Any]]:
    """Pure: per-reading dicts -> list of daily solar KPI dicts for one building.

    Each reading: {sensor_type, reading_value (float|None), ts (datetime)}.
    """
    by_day: dict[date, dict[str, list[tuple[datetime, float]]]] = defaultdict(
        lambda: {"power": [], "energy": [], "irr": [], "load": []}
    )
    for r in readings:
        v = r.get("reading_value")
        ts = r.get("ts")
        cls = _classify(r.get("sensor_type", ""))
        if v is None or ts is None or cls is None:
            continue
        by_day[ts.date()][cls].append((ts, float(v)))

    out: list[dict[str, Any]] = []
    for d in sorted(by_day):
        b = by_day[d]
        power = sorted(b["power"])
        energy = sorted(b["energy"])
        irr = sorted(b["irr"])
        load = sorted(b["load"])

        # --- generation ---
        if len(energy) >= 2:
            generated = max(0.0, max(v for _, v in energy) - min(v for _, v in energy))
            method = "counter"
        elif len(power) >= 2:
            generated = _trapz(power)
            method = "power_integration"
        else:
            generated = 0.0
            method = "none"

        # --- PR (IEC 61724) ---
        irradiation = _trapz([(t, v / 1000.0) for t, v in irr]) if len(irr) >= 2 else 0.0
        pr: float | None = None
        if capacity_kwp and capacity_kwp > 0 and irradiation >= MIN_IRRADIATION_KWH_M2:
            pr = generated / (capacity_kwp * irradiation)
            pr = max(0.0, min(PR_MAX_PLAUSIBLE, pr))

        # --- self-consumption split (needs PV power + load power) ---
        self_c: float | None = None
        exp_c: float | None = None
        if len(power) >= 2 and len(load) >= 2 and generated > 0:
            self_pi = _self_consumption_kwh(power, load)
            if self_pi is not None:
                self_c = max(0.0, min(self_pi, generated))
                exp_c = max(0.0, generated - self_c)

        out.append(
            {
                "date": d,
                "solar_generated_kwh": round(generated, 4),
                "solar_self_consumed_kwh": round(self_c, 4) if self_c is not None else None,
                "solar_exported_kwh": round(exp_c, 4) if exp_c is not None else None,
                "avg_solar_pr": round(pr, 4) if pr is not None else None,
                "in_plane_irradiation_kwh_m2": round(irradiation, 4) if irradiation else None,
                "pv_capacity_kwp": capacity_kwp,
                "reading_count": sum(len(b[k]) for k in b),
                "has_load_meter": len(load) > 0,
                "generation_method": method,
            }
        )
    return out


# --- DB wrapper (idempotent upsert into gold_solar_daily) --------------------
def run_rollup(db, building_ids: list[str] | None = None, since: date | None = None) -> int:
    """Aggregate bronze_iot_readings into gold_solar_daily. Returns rows upserted.

    Imports are local so the pure rollup_readings stays dependency-free + testable.
    """
    from sqlalchemy import text
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    from app.db.models.gold_solar_daily import GoldSolarDaily

    where = ["reading_value IS NOT NULL"]
    params: dict[str, Any] = {}
    if building_ids:
        where.append("building_id = ANY(:bids)")
        params["bids"] = list(building_ids)
    if since:
        where.append("source_timestamp >= :since")
        params["since"] = since
    sql = (
        "SELECT building_id, sensor_type, reading_value, source_protocol, "
        "source_timestamp AS ts "
        "FROM bronze_iot_readings WHERE " + " AND ".join(where) +
        " ORDER BY building_id, source_timestamp"
    )
    rows = db.execute(text(sql), params).mappings().all()

    per_b: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        per_b[r["building_id"]].append(dict(r))

    caps: dict[str, float] = {}
    if per_b:
        cap_rows = db.execute(
            text("SELECT building_id, pv_capacity_kwp FROM mv_building_master "
                 "WHERE building_id = ANY(:bids)"),
            {"bids": list(per_b)},
        ).mappings().all()
        caps = {r["building_id"]: r["pv_capacity_kwp"] for r in cap_rows}

    upserted = 0
    for bid, rdgs in per_b.items():
        # Honest provenance: telemetry entirely from the "Simulated" source is a
        # DEMO feed, not a live device. Mixed/real -> "telemetry".
        protos = {(r.get("source_protocol") or "") for r in rdgs}
        data_source = "simulated" if protos == {"Simulated"} else "telemetry"
        daily = rollup_readings(rdgs, caps.get(bid))
        for row in daily:
            stmt = pg_insert(GoldSolarDaily).values(
                building_id=bid, data_source=data_source, **row
            )
            update_cols = {k: stmt.excluded[k] for k in row if k != "date"}
            update_cols["data_source"] = data_source
            stmt = stmt.on_conflict_do_update(
                index_elements=["building_id", "date"], set_=update_cols
            )
            db.execute(stmt)
            upserted += 1
    db.commit()
    return upserted
