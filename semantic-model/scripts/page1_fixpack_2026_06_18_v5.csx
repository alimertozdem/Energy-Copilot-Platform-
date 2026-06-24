// =====================================================================
// Energy Copilot Platform - Page 1 Fix Pack v5  (SUPERSEDES v1-v4)
// File: semantic-model/scripts/page1_fixpack_2026_06_18_v5.csx
// Tool: Tabular Editor 2/3 -> C# Script -> Run -> Ctrl+S -> Refresh
//
// v5 CHANGES (root cause: the date slicer chops the window to ~323 days):
//   1) EUI now ANNUALIZES the selected period (x 365 / distinct days) ->
//      correct annual figure regardless of how the slicer cuts the window.
//      Verified vs live gold under the on-screen slicer:
//        Berliner 80.5 · DC 1615 · Healthcare 544 · Portfolio 370.
//   2) P1 Active Anomalies now ignores filters on the anomaly table
//      (ALL) -> shows the true open HIGH/CRITICAL count (= 4), slicer-proof.
//   3) Added P1 EUI Index Hex so the BAR chart can be colored by a single
//      field-value rule (the bar colors were inverted; table was fine).
//   No 'Date' table reference anywhere (that table errored earlier).
// =====================================================================

string home   = "gold_kpi_daily";
string folder = "Page1 Portfolio";
if (!Model.Tables.Contains(home))
    throw new Exception("Home table '" + home + "' not found.");

// cleanup any duplicate aliases left by earlier runs (no LINQ)
foreach (var nm in new[] { "P1 Scorecard EUI", "P1 Scorecard EUI Color" })
{
    Measure keep = null;
    var toDelete = new System.Collections.Generic.List<Measure>();
    foreach (var t in Model.Tables)
        foreach (var ms in t.Measures)
            if (ms.Name == nm) { if (keep == null) keep = ms; else toDelete.Add(ms); }
    foreach (var d in toDelete) d.Delete();
}

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

// 1) BUILDING EUI - annualized over the selected period, master area
upsert("P1 Building EUI", @"
VAR _days = DISTINCTCOUNT ( gold_kpi_daily[date] )
VAR _kwh  = SUM ( gold_kpi_daily[total_consumption_kwh] )
VAR _area = SELECTEDVALUE ( silver_building_master[gross_floor_area_m2] )
RETURN DIVIDE ( _kwh, _area ) * DIVIDE ( 365, _days )", "#,##0.0");

// 2) PORTFOLIO EUI - energy-weighted, annualized, master-only (orphan-safe)
upsert("P1 Portfolio EUI", @"
VAR _days = DISTINCTCOUNT ( gold_kpi_daily[date] )
VAR _t =
    ADDCOLUMNS ( VALUES ( silver_building_master[building_id] ),
        ""@kwh"",  CALCULATE ( SUM ( gold_kpi_daily[total_consumption_kwh] ) ),
        ""@area"", CALCULATE ( MAX ( silver_building_master[gross_floor_area_m2] ) ) )
RETURN DIVIDE ( SUMX ( _t, [@kwh] ), SUMX ( _t, [@area] ) ) * DIVIDE ( 365, _days )", "#,##0.0");

// 3) TYPE BENCHMARK - electricity EUI kWh/m2.yr (EDIT VALUES HERE)
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

// 4) EUI INDEX (% of own sector norm; 100 = on benchmark)
upsert("P1 EUI Index Pct",
    "DIVIDE ( [P1 Building EUI], [P1 EUI Type Benchmark] ) * 100", "#,##0\\%");

// 5) EUI COLOR code (1 green / 2 amber / 3 red) vs own type benchmark
upsert("P1 EUI Index Color", @"
VAR _r = DIVIDE ( [P1 Building EUI], [P1 EUI Type Benchmark] )
RETURN SWITCH ( TRUE(), _r <= 0.85, 1, _r <= 1.20, 2, 3 )", "0");

// 5b) EUI COLOR as HEX -> use for the BAR chart 'Color' fx = Field value
upsert("P1 EUI Index Hex", @"
SWITCH ( [P1 EUI Index Color], 1, ""#1D9E75"", 2, ""#EF9F27"", 3, ""#E24B4A"", ""#888888"" )", "");

// 6) PORTFOLIO BENCHMARK (energy-weighted target) - Avg-EUI card TARGET (~215)
upsert("P1 Portfolio EUI Benchmark", @"
VAR _t =
    ADDCOLUMNS ( VALUES ( silver_building_master[building_id] ),
        ""@a"", CALCULATE ( MAX ( silver_building_master[gross_floor_area_m2] ) ),
        ""@b"", CALCULATE ( [P1 EUI Type Benchmark] ) )
RETURN DIVIDE ( SUMX ( _t, [@a] * [@b] ), SUMX ( _t, [@a] ) )", "#,##0.0");

// 7) ACTIVE ANOMALIES - open HIGH/CRITICAL, slicer-proof (= 4)
upsert("P1 Active Anomalies", @"
CALCULATE (
    COUNTROWS ( gold_anomaly_log ),
    ALL ( gold_anomaly_log ),
    gold_anomaly_log[is_resolved] = FALSE ( ),
    UPPER ( gold_anomaly_log[severity] ) IN { ""HIGH"", ""CRITICAL"" }
) + 0", "#,##0");

// 8) BUILDING COST (period) - single-sourced from gold
upsert("P1 Building Cost EUR",
    "SUM ( gold_kpi_daily[estimated_cost_eur] )", "€ #,##0");

Info("v5 applied. Save (Ctrl+S), Refresh. Expect Berliner ~80, Portfolio ~370, "
   + "Active Anomalies = 4. THEN rebind visuals: (A) Avg EUI card value -> P1 Portfolio EUI; "
   + "(B) Anomalies card value -> P1 Active Anomalies; (C) Benchmark BAR color fx -> Field value -> "
   + "P1 EUI Index Hex; (D) Building-Based Consumption visual filter building_name is not (Blank); "
   + "(E) remove Building Name slicer.");
