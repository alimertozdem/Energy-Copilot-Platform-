// =====================================================================
// EnergyLens — PAGE 9 · 24h chart DIAGNOSE + FIX (delete-free)
// Reports the HOME TABLE of each 24h measure (both gold_battery_dispatch and
// gold_battery_hourly_dispatch have charge_kwh/discharge_kwh — a measure on the
// wrong/ daily table breaks the hourly axis), then re-asserts them on the
// correct hourly table as AVERAGE.
// TE2 → C# Script → File → Reload → F5 (read the Output) → Ctrl+S → Refresh.
// =====================================================================

// 1) DIAGNOSE — where does each 24h measure currently live?
foreach (var nm in new string[]{ "V6 Charge Rate","V6 Discharge Rate","V6 SoC Pct","V6 Price Index","V2 Avg Grid Price EUR kWh" }) {
    var hits = Model.AllMeasures.Where(m => m.Name == nm).ToList();
    if (hits.Count == 0) Output("MISSING: " + nm);
    else foreach (var m in hits) Output("found: " + nm + "  ON TABLE -> " + m.Table.Name);
}

// 2) FIX — force the correct definitions on gold_battery_hourly_dispatch.
//    If a duplicate exists on the wrong table, delete it first (name clash).
System.Action<string> dropWrong = (nm) => {
    foreach (var m in Model.AllMeasures.Where(x => x.Name == nm && x.Table.Name != "gold_battery_hourly_dispatch").ToList()) {
        Output("removing wrong-table copy: " + nm + " (was on " + m.Table.Name + ")"); m.Delete();
    }
};
string F = "Battery 24h (V6)";
System.Action<string,string,string> U = (nm, ex, fmt) => {
    dropWrong(nm);
    var t = Model.Tables["gold_battery_hourly_dispatch"];
    var m = t.Measures.FirstOrDefault(x => x.Name == nm);
    if (m == null) m = t.AddMeasure(nm, ex); else m.Expression = ex;
    m.FormatString = fmt; m.DisplayFolder = F; Output("set: " + nm + " -> gold_battery_hourly_dispatch");
};

U("V6 Charge Rate",            @"AVERAGE( gold_battery_hourly_dispatch[charge_kwh] )",        "#,##0.0");
U("V6 Discharge Rate",         @"AVERAGE( gold_battery_hourly_dispatch[discharge_kwh] )",     "#,##0.0");
U("V6 SoC Pct",                @"AVERAGE( gold_battery_hourly_dispatch[soc_percent] )",       "0.0");
U("V6 Price Index",            @"AVERAGE( gold_battery_hourly_dispatch[grid_price_index] )",  "0.00");
U("V2 Avg Grid Price EUR kWh", @"AVERAGE( gold_battery_hourly_dispatch[grid_price_eur_mwh] ) / 1000.0","0.000");

Output("=====================================================");
Output("Read the 'found ... ON TABLE' lines above — every 24h measure must be on gold_battery_hourly_dispatch.");
Output("Then: chart = Line and clustered column | Strategy slicer (strategy_label) -> pick ONE | Building slicer -> pick ONE.");
Output("Ctrl+S -> Refresh.");
Output("=====================================================");
