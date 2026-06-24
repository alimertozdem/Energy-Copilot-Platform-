// =====================================================================
// Energy Copilot Platform - Page 1 (Portfolio Overview) Fix Pack
// File: semantic-model/scripts/page1_fixpack_2026_06_18.csx
// Tool: Tabular Editor 2 or 3 -> C# Script tab -> paste -> Run (Play)
//       Then Save (Ctrl+S) to push to the live model, then Refresh report.
// Idempotent: re-running UPDATES the measures in place (safe to repeat).
//
// WHY (root causes proven against live gold data, 2026-06-18):
//   * "3 different EUIs for one building": card/table/benchmark each used
//     a different PERIOD (one measure hardcoded YEAR=2025 yet did not drop
//     the Date slicer -> only ~6.5 months counted) and a different AREA
//     (KPI floor_area_m2 = 4800 vs master gross_floor_area_m2 = 5200).
//     Berliner proof: 230822/5200=44.4 (benchmark) vs 356680/4800=74.3
//     (table). This pack puts EVERY EUI on ONE basis -> they converge.
//   * EUI benchmark unreadable + colors inverted: absolute EUI mixes a
//     Data Center (>1600) with offices (~60). Replaced by a type-NORMALIZED
//     index (100 = sector norm) with correct 1=green/2=amber/3=red.
//   * Active Anomalies CARD shows "(Blank)" at portfolio grain (the table
//     is fine). Added a portfolio-grade card measure.
//   * Cost re-derived in DAX with HARDCODED tariffs -> single-sourced from
//     gold instead.
//
// DECISIONS BAKED IN (change in ONE place if you decide otherwise):
//   * PERIOD : driven by the page Date slicer, ANNUALIZED (x365/days).
//   * AREA   : silver_building_master[gross_floor_area_m2] everywhere.
//   * Benchmarks are ELECTRICITY EUI (model kWh = grid electricity);
//     values are CIBSE TM46 / ENERGY STAR / EU screening-grade. Edit the
//     SWITCH in measure (3) to drop in DE-specific numbers.
// =====================================================================

string home   = "gold_kpi_daily";    // home table for NEW measures
string folder = "Page1 Portfolio";

if (!Model.Tables.Contains(home))
    throw new Exception("Home table '" + home + "' not found. Set 'home' to your fact table or a _Measures table.");

// add-or-update a measure by name (searches the whole model)
Action<string,string,string> upsert = (name, dax, fmt) => {
    Measure m = Model.AllMeasures.FirstOrDefault(x => x.Name == name);
    if (m == null) m = Model.Tables[home].AddMeasure(name);
    m.Expression = dax.Trim();
    if (!string.IsNullOrEmpty(fmt)) m.FormatString = fmt;
    m.DisplayFolder = folder;
};

// ---------------------------------------------------------------------
// 1) BUILDING EUI - annualized over selected period, MASTER area.
//    Single source of truth. Used by the table AND the benchmark.
// ---------------------------------------------------------------------
upsert("P1 Building EUI", @"
VAR _days = CALCULATE ( DISTINCTCOUNT ( gold_kpi_daily[date] ) )
VAR _kwh  = SUM ( gold_kpi_daily[total_consumption_kwh] )
VAR _area = SELECTEDVALUE ( silver_building_master[gross_floor_area_m2] )
RETURN DIVIDE ( _kwh, _area ) * DIVIDE ( 365, _days )", "#,##0.0");

// keep anything still bound to the old name working -> alias to the fix
upsert("P1 Scorecard EUI", "[P1 Building EUI]", "#,##0.0");

// ---------------------------------------------------------------------
// 2) PORTFOLIO EUI - energy-weighted Sum(kWh)/Sum(m2), annualized.
//    Replaces the simple-average "Avg EUI 1.20/day" card (DC-distorted).
// ---------------------------------------------------------------------
upsert("P1 Portfolio EUI", @"
VAR _days = CALCULATE ( DISTINCTCOUNT ( gold_kpi_daily[date] ) )
VAR _kwh  = SUM ( gold_kpi_daily[total_consumption_kwh] )
VAR _area =
    SUMX ( VALUES ( silver_building_master[building_id] ),
           CALCULATE ( MAX ( silver_building_master[gross_floor_area_m2] ) ) )
RETURN DIVIDE ( _kwh, _area ) * DIVIDE ( 365, _days )", "#,##0.0");

// ---------------------------------------------------------------------
// 3) TYPE BENCHMARK - electricity EUI kWh/m2.yr. EDIT VALUES HERE.
//    Includes Data_Center & Lab (were missing -> fell to default).
// ---------------------------------------------------------------------
upsert("P1 EUI Type Benchmark", @"
SWITCH ( SELECTEDVALUE ( silver_building_master[building_type] ),
    ""Office"",        95,
    ""Retail"",       165,
    ""Hotel"",        105,
    ""Healthcare"",   150,
    ""Education"",     80,
    ""Logistics"",     60,
    ""Data_Center"", 1000,
    ""Lab"",          300,
    120 )", "#,##0");

// ---------------------------------------------------------------------
// 4) EUI INDEX (% of own sector norm; 100 = on benchmark).
//    This is the VALUE for the "EUI vs Sector Benchmark" bar chart.
// ---------------------------------------------------------------------
upsert("P1 EUI Index Pct",
    "DIVIDE ( [P1 Building EUI], [P1 EUI Type Benchmark] ) * 100", "#,##0\\%");

// ---------------------------------------------------------------------
// 5) EUI COLOR (1 green / 2 amber / 3 red) vs OWN type benchmark.
//    Bind conditional formatting to this. Fixes the inverted colors.
// ---------------------------------------------------------------------
upsert("P1 EUI Index Color", @"
VAR _r = DIVIDE ( [P1 Building EUI], [P1 EUI Type Benchmark] )
RETURN SWITCH ( TRUE(), _r <= 0.85, 1, _r <= 1.20, 2, 3 )", "0");

// fix the table's existing color measure to the same correct logic
upsert("P1 Scorecard EUI Color", "[P1 EUI Index Color]", "0");

// ---------------------------------------------------------------------
// 6) PORTFOLIO BENCHMARK (energy-weighted target) - the "where you should
//    be" line. Use as the Avg-EUI card TARGET (kills the -218% goal).
// ---------------------------------------------------------------------
upsert("P1 Portfolio EUI Benchmark", @"
VAR _t =
    ADDCOLUMNS ( VALUES ( silver_building_master[building_id] ),
        ""@a"", CALCULATE ( MAX ( silver_building_master[gross_floor_area_m2] ) ),
        ""@b"", CALCULATE ( [P1 EUI Type Benchmark] ) )
RETURN DIVIDE ( SUMX ( _t, [@a] * [@b] ), SUMX ( _t, [@a] ) )", "#,##0.0");

// ---------------------------------------------------------------------
// 7) ACTIVE ANOMALIES - portfolio-grade CARD measure (was "(Blank)").
//    The table keeps its own per-building measure (it already works).
// ---------------------------------------------------------------------
upsert("P1 Active Anomalies", @"
CALCULATE (
    COUNTROWS ( gold_anomaly_log ),
    gold_anomaly_log[is_resolved] = FALSE ( ),
    UPPER ( gold_anomaly_log[severity] ) IN { ""HIGH"", ""CRITICAL"" }
) + 0", "#,##0");

// ---------------------------------------------------------------------
// 8) BUILDING COST (period) - single-sourced from gold, no hardcoded tariff
// ---------------------------------------------------------------------
upsert("P1 Building Cost EUR",
    "SUM ( gold_kpi_daily[estimated_cost_eur] )", "€ #,##0");

Info("Page 1 fix pack applied: 10 measures created/updated. "
   + "Save (Ctrl+S) to push to the model, then Refresh the report. "
   + "Then re-point the visuals per the mockup (card -> P1 Portfolio EUI, "
   + "anomalies card -> P1 Active Anomalies, benchmark -> P1 EUI Index Pct + color P1 EUI Index Color).");
