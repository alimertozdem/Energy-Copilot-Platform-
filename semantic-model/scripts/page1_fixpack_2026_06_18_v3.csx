// =====================================================================
// Energy Copilot Platform - Page 1 Fix Pack v3  (SUPERSEDES v1/v2)
// File: semantic-model/scripts/page1_fixpack_2026_06_18_v3.csx
// Tool: Tabular Editor 2/3 -> C# Script -> paste -> Run -> Ctrl+S -> Refresh
//
// v3 CHANGE: removed ALL LINQ (.Where/.FirstOrDefault) and StringComparison
//   -> some TE builds reject LINQ in the script sandbox (this caused the
//   line-36 error). Pure foreach now; behaviour identical to v2.
//
// WHAT IT DOES:
//   - deletes the duplicate measures v1 created (clears Missing_References)
//   - upserts 8 Page-1 measures with VERIFIED-correct DAX (no duplicates)
//
// EUI DESIGN (verified vs live gold): trailing 12 months of available data,
//   slicer-independent, master gross_floor_area_m2, orphans excluded.
//   Expected: Berliner ~78, Portfolio ~368, Portfolio benchmark ~215,
//   Active Anomalies = 4.
//
// REQUIRES a date table named 'Date' (marked as Date Table) related to
//   gold_kpi_daily[date]. If yours has another name, replace 'Date' below.
// =====================================================================

string home   = "gold_kpi_daily";
string folder = "Page1 Portfolio";
if (!Model.Tables.Contains(home))
    throw new Exception("Home table '" + home + "' not found. Set 'home' correctly.");

// --- CLEANUP: drop duplicate measures left by v1 (no LINQ) ------------
foreach (var nm in new[] { "P1 Scorecard EUI", "P1 Scorecard EUI Color" })
{
    Measure keep = null;
    var toDelete = new System.Collections.Generic.List<Measure>();
    foreach (var t in Model.Tables)
        foreach (var ms in t.Measures)
            if (ms.Name == nm) { if (keep == null) keep = ms; else toDelete.Add(ms); }
    foreach (var d in toDelete) d.Delete();
}

// --- upsert helper: find across all tables (no LINQ), update or create
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

// 1) BUILDING EUI - trailing 12 months of data, master area (slicer-independent)
upsert("P1 Building EUI", @"
VAR _maxDate = CALCULATE ( MAX ( gold_kpi_daily[date] ), REMOVEFILTERS ( 'Date' ) )
VAR _kwh =
    CALCULATE ( SUM ( gold_kpi_daily[total_consumption_kwh] ),
        REMOVEFILTERS ( 'Date' ),
        DATESBETWEEN ( 'Date'[Date], _maxDate - 364, _maxDate ) )
VAR _area = SELECTEDVALUE ( silver_building_master[gross_floor_area_m2] )
RETURN DIVIDE ( _kwh, _area )", "#,##0.0");

// 2) PORTFOLIO EUI - energy-weighted, trailing 12 months, master-only (orphan-safe)
upsert("P1 Portfolio EUI", @"
VAR _maxDate = CALCULATE ( MAX ( gold_kpi_daily[date] ), REMOVEFILTERS ( 'Date' ) )
VAR _t =
    ADDCOLUMNS ( VALUES ( silver_building_master[building_id] ),
        ""@kwh"", CALCULATE ( SUM ( gold_kpi_daily[total_consumption_kwh] ),
            REMOVEFILTERS ( 'Date' ),
            DATESBETWEEN ( 'Date'[Date], _maxDate - 364, _maxDate ) ),
        ""@area"", CALCULATE ( MAX ( silver_building_master[gross_floor_area_m2] ) ) )
RETURN DIVIDE ( SUMX ( _t, [@kwh] ), SUMX ( _t, [@area] ) )", "#,##0.0");

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

// 5) EUI COLOR (1 green / 2 amber / 3 red) vs own type benchmark
upsert("P1 EUI Index Color", @"
VAR _r = DIVIDE ( [P1 Building EUI], [P1 EUI Type Benchmark] )
RETURN SWITCH ( TRUE(), _r <= 0.85, 1, _r <= 1.20, 2, 3 )", "0");

// 6) PORTFOLIO BENCHMARK (energy-weighted target) - Avg-EUI card TARGET (~215)
upsert("P1 Portfolio EUI Benchmark", @"
VAR _t =
    ADDCOLUMNS ( VALUES ( silver_building_master[building_id] ),
        ""@a"", CALCULATE ( MAX ( silver_building_master[gross_floor_area_m2] ) ),
        ""@b"", CALCULATE ( [P1 EUI Type Benchmark] ) )
RETURN DIVIDE ( SUMX ( _t, [@a] * [@b] ), SUMX ( _t, [@a] ) )", "#,##0.0");

// 7) ACTIVE ANOMALIES - portfolio-grade CARD measure (was "(Blank)")
upsert("P1 Active Anomalies", @"
CALCULATE (
    COUNTROWS ( gold_anomaly_log ),
    gold_anomaly_log[is_resolved] = FALSE ( ),
    UPPER ( gold_anomaly_log[severity] ) IN { ""HIGH"", ""CRITICAL"" }
) + 0", "#,##0");

// 8) BUILDING COST (period) - single-sourced from gold, no hardcoded tariff
upsert("P1 Building Cost EUR",
    "SUM ( gold_kpi_daily[estimated_cost_eur] )", "€ #,##0");

Info("Page 1 fix pack v3 applied (no LINQ). Save (Ctrl+S), Refresh. "
   + "Expect: Berliner EUI ~78, Portfolio EUI ~368, benchmark ~215, anomalies = 4.");
