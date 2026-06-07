// =====================================================================
// Page 9 v56h — I1 short + defensive (fits in narrow card, robust to BLANK)
// =====================================================================
// Problem: I1 text too long for card + showing "office" instead of "logistics"
// Fix: shorter text, better fallback chain, building_name as primary key
// =====================================================================

System.Func<string, Table> findTable = (string name) => {
    foreach (var tbl in Model.Tables) { if (tbl.Name == name) return tbl; }
    return null;
};

System.Action<string,string,string,string,string> upsert =
    (string tableName, string measureName, string expression, string format, string folder) =>
{
    var t = findTable(tableName);
    if (t == null) { Output("[SKIP] " + tableName); return; }
    Measure existing = null;
    foreach (var tbl in Model.Tables) {
        foreach (var meas in tbl.Measures) { if (meas.Name == measureName) { existing = meas; break; } }
        if (existing != null) break;
    }
    if (existing != null) {
        if (existing.Table.Name != tableName) { existing.Delete(); }
        else {
            existing.Expression = expression;
            if (!string.IsNullOrEmpty(format)) existing.FormatString = format;
            if (!string.IsNullOrEmpty(folder)) existing.DisplayFolder = folder;
            Output("[UPDATE] " + tableName + "." + measureName);
            return;
        }
    }
    var nm = t.AddMeasure(measureName, expression);
    if (!string.IsNullOrEmpty(format)) nm.FormatString = format;
    if (!string.IsNullOrEmpty(folder)) nm.DisplayFolder = folder;
    Output("[CREATE] " + tableName + "." + measureName);
};

// I1 Strategy Recommendation — short version with fallback chain
upsert("gold_strategy_fitness", "I1 Strategy Recommendation Text",
@"VAR _building_name = SELECTEDVALUE( silver_building_master[building_name] )
VAR _bt = COALESCE(
    SELECTEDVALUE( silver_building_master[building_type] ),
    CALCULATE( MAX( silver_building_master[building_type] ),
               TREATAS( VALUES(gold_battery_dispatch[building_id]),
                        silver_building_master[building_id] ) )
)
VAR _has_single = NOT ISBLANK(_building_name) && NOT ISBLANK(_bt)
VAR _primary_label = CALCULATE(
    SELECTEDVALUE( gold_strategy_fitness[strategy_label] ),
    gold_strategy_fitness[building_type] = _bt,
    gold_strategy_fitness[is_primary] = TRUE() )
VAR _primary_savings = CALCULATE(
    AVERAGE( gold_strategy_fitness[typical_annual_savings_eur_per_kwh] ),
    gold_strategy_fitness[building_type] = _bt,
    gold_strategy_fitness[is_primary] = TRUE() )
VAR _cap = SELECTEDVALUE( silver_building_master[battery_capacity_kwh], 100 )
VAR _est_eur = ROUND( _primary_savings * _cap, -2 )
RETURN
    IF( NOT _has_single,
        ""Select a single building"",
        IF( ISBLANK(_primary_label),
            ""No primary strategy for "" & _bt,
            ""Best for "" & _bt & "": "" & _primary_label & UNICHAR(10) &
            ""Est. EUR "" & FORMAT(_est_eur, ""#,0"") & ""/yr (±25%)""
        )
    )",
"", "Page 9 / Insights");

Output("v56h I1 short COMPLETE. Card text now fits + defensive against BLANK.");
