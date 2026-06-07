"""Bridge readiness -- the data-tier-aware diagnosis behind self-serve bridging.

Access Layer 3 (docs/architecture/self-serve-fabric-bridging.md). Given what a
building actually has (uploaded months, connected devices, enabled modules,
profile), this produces a per-report-page readiness assessment with an honest
reason for each page. It is the "AI-guided" wizard's brain -- but it is a *pure,
deterministic* function: no LLM, no network, no credits. An LLM can later pretty
up the prose, but the logic stands alone.

Core principle (CLAUDE.md: don't invent unrealistic logic; state assumptions):
**a building's analytics depth is bounded by its data.** Bridging never means
"turn on all pages" -- it means "unlock exactly the pages the data earns". The
app already gates IoT/battery pages by module, so this assessment mirrors that
and adds the data-volume gates (months of history) the reports need.

Thresholds are deliberate, documented assumptions -- not hard science:
  * trends need ~6 months to be meaningful (3-5 = indicative),
  * benchmark/recommendations need ~3 months + floor area + building type,
  * monthly forecasting needs ~12 months; hourly forecasting needs a live feed.
"""
from __future__ import annotations

# Minimum months of history for each data-volume gate (documented assumptions).
TREND_MIN_MONTHS = 6
TREND_PARTIAL_MONTHS = 3
BENCHMARK_MIN_MONTHS = 3
FORECAST_MIN_MONTHS = 12

READY = "ready"
PARTIAL = "partial"
LOCKED = "locked"

TOTAL_PAGES = 10


def _page(key: str, label: str, status: str, reason: str) -> dict:
    return {"key": key, "label": label, "status": status, "reason": reason}


def assess_readiness(
    *,
    building_type: str | None,
    floor_area_m2: float | None,
    pv_capacity_kwp: float | None,
    epc_class: str | None,
    consumption_months: int,
    has_cost: bool,
    has_device: bool,
    iot_enabled: bool,
    battery_enabled: bool,
) -> dict:
    """Assess which report pages a building's data can support.

    Returns a dict: overall_tier, can_request, counts, a `pages` list (one entry
    per report page with status + reason), a plain-language `summary`, and a
    `blocking` list of concrete next steps to unlock more.
    """
    m = max(0, int(consumption_months or 0))
    has_area = floor_area_m2 is not None and float(floor_area_m2) > 0
    has_type = bool(building_type)
    has_pv = pv_capacity_kwp is not None and float(pv_capacity_kwp) > 0

    pages: list[dict] = []

    # 1 — Overview & KPIs
    if m >= 1:
        pages.append(_page("overview", "Overview & KPIs", READY,
                           "Computed from your uploaded meter data."))
    else:
        pages.append(_page("overview", "Overview & KPIs", LOCKED,
                           "Upload at least one month of consumption."))

    # 2 — Consumption trends
    if m >= TREND_MIN_MONTHS:
        pages.append(_page("trends", "Consumption Trends", READY,
                           f"{m} months of history."))
    elif m >= TREND_PARTIAL_MONTHS:
        pages.append(_page("trends", "Consumption Trends", PARTIAL,
                           f"Only {m} months — the trend is indicative."))
    else:
        pages.append(_page("trends", "Consumption Trends", LOCKED,
                           f"Needs ~{TREND_MIN_MONTHS} months of history (have {m})."))

    # 3 — Benchmark & targets (EUI vs peers)
    if m >= BENCHMARK_MIN_MONTHS and has_area and has_type:
        pages.append(_page("benchmark", "Benchmark & Targets", READY,
                           f"EUI vs {building_type} peers."))
    elif m >= BENCHMARK_MIN_MONTHS:
        pages.append(_page("benchmark", "Benchmark & Targets", PARTIAL,
                           "Add floor area + building type for a peer benchmark."))
    else:
        pages.append(_page("benchmark", "Benchmark & Targets", LOCKED,
                           f"Needs ~{BENCHMARK_MIN_MONTHS} months + floor area + building type."))

    # 4 — Forecast
    if m >= FORECAST_MIN_MONTHS:
        pages.append(_page("forecast", "Forecast", PARTIAL,
                           f"Monthly forecast from {m} months; hourly forecasting needs a live feed."))
    else:
        pages.append(_page("forecast", "Forecast", LOCKED,
                           f"Needs {FORECAST_MIN_MONTHS}+ months or a live feed (have {m})."))

    # 5 — Decision support / recommendations
    if m >= BENCHMARK_MIN_MONTHS and has_type:
        pages.append(_page("recommendations", "Decision Support", READY,
                           "Building-type-aware recommendations."))
    elif m >= 1:
        pages.append(_page("recommendations", "Decision Support", PARTIAL,
                           "Basic recommendations; add building type + history for more."))
    else:
        pages.append(_page("recommendations", "Decision Support", LOCKED,
                           "Upload consumption to generate recommendations."))

    # 6 — Sustainability / GHG (Scope 2)
    if m >= 1:
        pages.append(_page("sustainability", "Sustainability (GHG)", READY,
                           "Scope-2 emissions from your data + grid factors."))
    else:
        pages.append(_page("sustainability", "Sustainability (GHG)", LOCKED,
                           "Upload consumption for an emissions baseline."))

    # 7 — HVAC analytics (needs sub-metered HVAC)
    if iot_enabled and has_device:
        pages.append(_page("hvac", "HVAC Analytics", READY,
                           "Sub-metered HVAC from your connected devices."))
    elif iot_enabled:
        pages.append(_page("hvac", "HVAC Analytics", PARTIAL,
                           "IoT module on — connect an HVAC sensor."))
    else:
        pages.append(_page("hvac", "HVAC Analytics", LOCKED,
                           "Needs sub-metered HVAC sensors (IoT module)."))

    # 8 — IoT monitoring
    if iot_enabled and has_device:
        pages.append(_page("iot", "IoT Monitoring", READY,
                           "Live sensor monitoring."))
    elif iot_enabled:
        pages.append(_page("iot", "IoT Monitoring", PARTIAL,
                           "IoT module on — connect a device."))
    else:
        pages.append(_page("iot", "IoT Monitoring", LOCKED,
                           "Needs connected IoT sensors."))

    # 9 — Battery strategy
    if battery_enabled:
        pages.append(_page("battery", "Battery Strategy", PARTIAL,
                           "Battery module on — add tariff + (optional) solar for dispatch ROI."))
    else:
        pages.append(_page("battery", "Battery Strategy", LOCKED,
                           "Needs a battery system (battery module)."))

    # 10 — Solar
    if has_pv and m >= 1:
        pages.append(_page("solar", "Solar", READY,
                           "On-site solar vs your consumption."))
    elif has_pv:
        pages.append(_page("solar", "Solar", PARTIAL,
                           "Solar configured — upload consumption to compare."))
    else:
        pages.append(_page("solar", "Solar", LOCKED,
                           "No on-site solar configured."))

    ready_pages = sum(1 for p in pages if p["status"] == READY)
    partial_pages = sum(1 for p in pages if p["status"] == PARTIAL)

    # Overall data tier.
    if iot_enabled and has_device and battery_enabled:
        overall_tier = "full"
    elif iot_enabled and has_device:
        overall_tier = "monitoring"
    elif m >= 1:
        overall_tier = "baseline"
    else:
        overall_tier = "empty"

    # Can only request a bridge once there is *something* real to bridge.
    can_request = m >= 1 or has_device

    # Concrete next steps to unlock more (most-relevant first).
    blocking: list[str] = []
    if m < TREND_MIN_MONTHS:
        blocking.append(
            f"Add more monthly history (have {m}) to unlock richer trends"
            + (" and forecasting." if m < FORECAST_MIN_MONTHS else ".")
        )
    if not has_area or not has_type:
        blocking.append("Add floor area + building type for peer benchmarking.")
    if iot_enabled and not has_device:
        blocking.append("Connect a device — the IoT module is on but none is configured.")
    elif not iot_enabled:
        blocking.append("Connect an IoT device to unlock HVAC + live monitoring.")
    if not battery_enabled:
        blocking.append("Enable the battery module to model battery strategy.")

    return {
        "overall_tier": overall_tier,
        "can_request": can_request,
        "ready_pages": ready_pages,
        "partial_pages": partial_pages,
        "total_pages": TOTAL_PAGES,
        "consumption_months": m,
        "pages": pages,
        "summary": _summarize(m, ready_pages, partial_pages, overall_tier),
        "blocking": blocking[:4],
    }


def _summarize(m: int, ready: int, partial: int, tier: str) -> str:
    """One plain-language sentence the wizard shows above the page list."""
    if m == 0:
        return (
            "No consumption uploaded yet. Upload a CSV or a utility bill to unlock "
            "baseline analytics — then you can request the full Fabric bridge."
        )
    base = f"{m} month{'s' if m != 1 else ''} of meter data"
    earned = f"{ready} report page{'s' if ready != 1 else ''} ready"
    if partial:
        earned += f", {partial} partial"
    tail = {
        "full": "Connected sensors + a battery system unlock the deep pages too.",
        "monitoring": "Connected sensors unlock live monitoring; a battery system would add battery strategy.",
        "baseline": "Connect a device (and/or a battery) to unlock the deep pages.",
        "empty": "",
    }.get(tier, "")
    return f"{base} → {earned}. {tail}".strip()
