// =====================================================================
// Energy Copilot Platform - Page 2 (Building Detail) Fix Pack
// File: semantic-model/scripts/page2_fixpack_2026_06_18.csx
// Tool: Tabular Editor 2/3 -> C# Script -> Run -> Ctrl+S -> Refresh
//
// ROOT CAUSES (verified vs live gold, 2026-06-18):
//   * "Date Cap" pattern: CALCULATE(..., 'Date'[Date] <= _cap) OVERWRITES the
//     slicer's start -> cards summed ALL history to _cap, not the selected
//     period. Proof: Berliner Peak read 168 (all-time) vs 126 (window). It
//     also blanked Solar despite both buildings having PV (67k / 215k).
//     FIX: strip the Date Cap; plain AVERAGE/MAX/SUM respect slicer+building.
//   * Base Load Ratio identical 14.4% for every building -> the building
//     filter never reached gold_kpi_hourly (no relationship). FIX: TREATAS
//     bridges the selected building_id(s) onto gold_kpi_hourly.
//   * EUI gauge was daily + fixed 0.27 target + max 1.0 -> off-scale for the
//     DC, wrong "Poor", and inconsistent with Page 1. FIX (approved): gauge
//     uses the Page-1 type-index (P1 EUI Index Pct, 100 = sector norm).
//
// Shares Page-1 measures: P1 Building EUI, P1 EUI Index Pct, P1 EUI Index Color
//   (already built, annual, type-aware -> guarantees Page 1<->2 consistency).
// =====================================================================

string home   = "gold_kpi_daily";
string folder = "Page2 Building";
if (!Model.Tables.Contains(home))
    throw new Exception("Home table '" + home + "' not found.");

Action<string,string,string> upsert = (name, dax, fmt) => {
    Measure m = null;
    foreach (var t in Model.Tables) {
        if (m != null) break;
        foreach (var ms in t.Measures)
            if (ms.Name == name) { m = ms; break; }
    }
    if (m == null) m = Model.Tables[home].AddMeasure(name);
    m.Expression = dax.Trim();
    if (!string.IsNullOrEmpty(fmt)) m.FormatString = fmt;
    m.DisplayFolder = folder;
};

// --- KPI cards: strip Date Cap, respect slicer + building naturally ---

// C1 (Berliner 1.149 / DC 42.011)
upsert("Avg Daily Consumption kWh",
    "AVERAGE ( gold_kpi_daily[total_consumption_kwh] )", "#,##0.0");

// C2 (Berliner 126 / DC 2.137) - was 168 because Date Cap took all-time max
upsert("Peak Demand kW",
    "MAX ( gold_kpi_daily[peak_demand_kw] )", "#,##0.0");

// C4 (Berliner 66.958 / DC 214.553) - was Blank
upsert("Total Solar Generated kWh",
    "SUM ( gold_kpi_daily[solar_generated_kwh] )", "#,##0");

// C6 (Berliner 0.069 / DC 1.880) kgCO2/m2/day
upsert("Avg Carbon Intensity kg m2",
    "AVERAGE ( gold_kpi_daily[carbon_intensity_kg_m2] )", "0.000");

// C5 Battery SoC - blank when the building has no battery (DC -> blank)
upsert("Avg Battery SoC Pct", @"
IF (
    CALCULATE ( MAX ( gold_kpi_daily[battery_capacity_kwh] ) ) > 0,
    AVERAGEX ( gold_kpi_daily,
        DIVIDE ( gold_kpi_daily[battery_soc_min_pct] + gold_kpi_daily[battery_soc_max_pct], 2 ) ),
    BLANK ()
)", "0.0");

// Base Load Ratio - bridge the selected building onto the hourly table
upsert("Base Load Ratio Pct", @"
VAR _bids = VALUES ( silver_building_master[building_id] )
VAR _night =
    CALCULATE ( AVERAGE ( gold_kpi_hourly[peak_demand_kw] ),
        gold_kpi_hourly[hour] IN { 2, 3, 4 },
        TREATAS ( _bids, gold_kpi_hourly[building_id] ) )
VAR _peak =
    CALCULATE ( MAX ( gold_kpi_hourly[peak_demand_kw] ),
        gold_kpi_hourly[hour] IN { 9, 10, 11, 12, 13, 14, 15, 16, 17 },
        TREATAS ( _bids, gold_kpi_hourly[building_id] ) )
RETURN DIVIDE ( _night, _peak )", "0.0%");

// --- EUI gauge -> type-index scale (approved). Value = P1 EUI Index Pct ---
upsert("P2 EUI Gauge Target", "100", "#,##0");   // sector norm line
upsert("P2 EUI Gauge Max",    "200", "#,##0");    // 0-200% scale (DC ~162 fits)

Info("Page 2 fix pack applied. Save (Ctrl+S), Refresh. "
   + "Expect (Berliner / DC): Daily 1.149 / 42.011, Peak 126 / 2.137, "
   + "Solar 66.958 / 214.553, Battery 61 / blank. "
   + "THEN rebind visuals - see chat checklist (EUI card->P1 Building EUI; "
   + "gauge value->P1 EUI Index Pct, target->P2 EUI Gauge Target, max->P2 EUI Gauge Max, "
   + "color->P1 EUI Index Color; remove hardcoded goals; has_battery filter; drop Live cards).");
