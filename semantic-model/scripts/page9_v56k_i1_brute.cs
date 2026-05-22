// =====================================================================
// Page 9 v56k — I1 with ALL+FILTER (bypass context propagation issues)
// + diagnostic measure that always echoes selection
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

// I1 — brute force lookup via ALL+FILTER (doesn't rely on filter propagation)
upsert("gold_strategy_fitness", "I1 Strategy Recommendation Text",
@"VAR _bn = SELECTEDVALUE( silver_building_master[building_name] )
VAR _bt = CALCULATE(
    MAX( silver_building_master[building_type] ),
    ALL( silver_building_master ),
    silver_building_master[building_name] = _bn )
VAR _cap = CALCULATE(
    MAX( silver_building_master[battery_capacity_kwh] ),
    ALL( silver_building_master ),
    silver_building_master[building_name] = _bn )
VAR _primary_label = CALCULATE(
    SELECTEDVALUE( gold_strategy_fitness[strategy_label] ),
    ALL( gold_strategy_fitness ),
    gold_strategy_fitness[building_type] = _bt,
    gold_strategy_fitness[is_primary] = TRUE() )
VAR _primary_savings = CALCULATE(
    AVERAGE( gold_strategy_fitness[typical_annual_savings_eur_per_kwh] ),
    ALL( gold_strategy_fitness ),
    gold_strategy_fitness[building_type] = _bt,
    gold_strategy_fitness[is_primary] = TRUE() )
VAR _est_eur_k =
    IF( NOT ISBLANK(_primary_savings) && NOT ISBLANK(_cap),
        ROUND( _primary_savings * _cap / 1000, 0 ),
        BLANK() )
RETURN
    SWITCH( TRUE(),
        ISBLANK(_bn),  ""Select 1 building"",
        ISBLANK(_bt),  _bn & "" (no type)"",
        ISBLANK(_primary_label), _bn & "" - no strategy data"",
        ISBLANK(_est_eur_k), _bt & "" -> "" & _primary_label,
        _bt & "" -> "" & _primary_label & ""  ~EUR "" & FORMAT(_est_eur_k, ""#,0"") & ""K/yr""
    )",
"", "Page 9 / Insights");

// DIAGNOSTIC — always shows selected building, can be put in temp card
upsert("gold_strategy_fitness", "I1 Diagnostic Selection",
@"VAR _bn = SELECTEDVALUE( silver_building_master[building_name] )
RETURN ""bn = "" & COALESCE(_bn, ""(blank — slicer not filtering this card)"")",
"", "Page 9 / Insights");

Output("v56k brute force I1 + diagnostic measure ready.");
