// =====================================================================
// Energy Copilot Platform - Page 2 Fix Pack v2  (run AFTER v1)
// File: semantic-model/scripts/page2_fixpack_2026_06_18_v2.csx
// Tool: Tabular Editor 2/3 -> C# Script -> Run -> Ctrl+S -> Refresh
//
// WHY v2: the Page-2 KPI cards are bound to the "...KPI" twin measures, which
//   wrap the value in CALCULATE(..., ALLSELECTED()). ALLSELECTED() drops the
//   date slicer here -> the cards showed ALL-TIME, not the selected period.
//   Proof (B001): Peak 168 (all-time) vs 126 (window); Solar all-time vs
//   66,531 (window). Dropping ALLSELECTED makes them respect the slicer.
//   (Daily/Carbon/Battery looked fine only because their values are flat.)
// =====================================================================

string home = "gold_kpi_daily";

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
    m.DisplayFolder = "Page2 Building";
};

// KPI twins -> drop ALLSELECTED so they honor the date slicer + building
upsert("Avg Daily Consumption kWh KPI",
    "AVERAGE ( gold_kpi_daily[total_consumption_kwh] )", "#,##0.0 \"kWh\"");

upsert("Peak Demand kW KPI",
    "MAX ( gold_kpi_daily[peak_demand_kw] )", "#,##0.0 \"kW\"");

upsert("Total Solar Generated kWh KPI",
    "SUM ( gold_kpi_daily[solar_generated_kwh] )", "#,##0 \"kWh\"");

Info("Page 2 v2 applied. Save (Ctrl+S), Refresh. Expect (B001, window): "
   + "Peak 126 (was 168), Solar ~66,531 (was all-time), Daily ~1.149. "
   + "If any other Page-2 KPI card still ignores the slicer, its measure also "
   + "uses ALLSELECTED() - fix the same way.");
