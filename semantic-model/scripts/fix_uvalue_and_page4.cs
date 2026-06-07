// =====================================================================
// FINAL measure-layer cleanup: U-Value DATATABLE + Page 4 forecast band
// Run in Tabular Editor 2 (C# Script → F5), then File → Save, then PBI Refresh.
// =====================================================================

// 1) Fix the 'U-Value Categories' calculated table (DATATABLE syntax error).
//    GEG 2023 reference U-values (W/m2K): Wall 0.24, Roof 0.20, Floor 0.35, Window 1.30.
var uv = Model.Tables.FirstOrDefault(t => t.Name == "U-Value Categories");
if (uv != null && uv.Partitions.Count > 0) {
    try {
        uv.Partitions[0].Expression =
@"DATATABLE(
    ""Component"",     STRING,
    ""SortIdx"",       INTEGER,
    ""Reference_GEG"", DOUBLE,
    {
        { ""Wall"",   1, 0.24 },
        { ""Roof"",   2, 0.20 },
        { ""Floor"",  3, 0.35 },
        { ""Window"", 4, 1.30 }
    }
)";
        Output("OK: 'U-Value Categories' DATATABLE expression replaced.");
    } catch (System.Exception ex) {
        Output("U-Value fix FAILED via script (" + ex.Message + ") — fix manually (see chat for the DAX).");
    }
} else {
    Output("NOTE: 'U-Value Categories' table/partition not found — fix manually if it still errors.");
}

// 2) Page 4 — forecast confidence band measures (gold_consumption_forecast has the columns).
System.Action<string,string,string> Up = (name, expr, fmt) => {
    if (!Model.Tables.Any(t => t.Name == "gold_consumption_forecast")) {
        Output("SKIP (no gold_consumption_forecast): " + name); return;
    }
    var m = Model.AllMeasures.FirstOrDefault(x => x.Name == name);
    if (m == null) m = Model.Tables["gold_consumption_forecast"].AddMeasure(name, expr);
    else m.Expression = expr;
    m.FormatString = fmt;
    m.DisplayFolder = "Page 4 Forecast";
    Output("OK: " + name);
};
Up("Forecast Predicted kWh",   @"SUM( gold_consumption_forecast[predicted_kwh] )",   "#,##0");
Up("Forecast Lower Bound kWh", @"SUM( gold_consumption_forecast[lower_bound_kwh] )", "#,##0");
Up("Forecast Upper Bound kWh", @"SUM( gold_consumption_forecast[upper_bound_kwh] )", "#,##0");

Output("=====================================================");
Output("DONE — U-Value fixed + 3 forecast-band measures added. Save (Ctrl+S) + Refresh.");
Output("=====================================================");
