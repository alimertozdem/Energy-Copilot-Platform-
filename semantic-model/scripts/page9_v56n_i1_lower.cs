// =====================================================================
// Page 9 v56n — I1 with LOWER() normalization for building_type match
// =====================================================================
// User reports: some buildings work, most show "no data".
// Likely cause: building_type case mismatch (e.g. "Office" vs "office")
// Fix: LOWER() both sides of comparison
// =====================================================================

System.Func<string, Table> findTable = (string name) => {
    foreach (var tbl in Model.Tables) { if (tbl.Name == name) return tbl; }
    return null;
};

Measure existing = null;
foreach (var tbl in Model.Tables) {
    foreach (var meas in tbl.Measures) {
        if (meas.Name == "I1 Strategy Recommendation Text") {
            existing = meas;
            break;
        }
    }
    if (existing != null) break;
}

string expression = @"VAR _bn = COALESCE(
    SELECTEDVALUE( silver_building_master[building_name] ),
    SELECTEDVALUE( gold_battery_dispatch[building_name] ),
    SELECTEDVALUE( gold_battery_simulation[building_name] )
)
VAR _bt_raw = COALESCE(
    SELECTEDVALUE( silver_building_master[building_type] ),
    LOOKUPVALUE( silver_building_master[building_type],
                 silver_building_master[building_name], _bn )
)
VAR _bt = LOWER( SUBSTITUTE( SUBSTITUTE( _bt_raw, "" "", ""_"" ), ""-"", ""_"" ) )
VAR _cap = COALESCE(
    SELECTEDVALUE( silver_building_master[battery_capacity_kwh] ),
    LOOKUPVALUE( silver_building_master[battery_capacity_kwh],
                 silver_building_master[building_name], _bn )
)
VAR _primary_label = CALCULATE(
    SELECTEDVALUE( gold_strategy_fitness[strategy_label] ),
    ALL( gold_strategy_fitness ),
    LOWER( gold_strategy_fitness[building_type] ) = _bt,
    gold_strategy_fitness[is_primary] = TRUE() )
VAR _primary_savings = CALCULATE(
    AVERAGE( gold_strategy_fitness[typical_annual_savings_eur_per_kwh] ),
    ALL( gold_strategy_fitness ),
    LOWER( gold_strategy_fitness[building_type] ) = _bt,
    gold_strategy_fitness[is_primary] = TRUE() )
VAR _est_eur_k =
    IF( NOT ISBLANK(_primary_savings) && NOT ISBLANK(_cap),
        ROUND( _primary_savings * _cap / 1000, 0 ),
        BLANK() )
RETURN
    SWITCH( TRUE(),
        ISBLANK(_bn),  ""Select 1 building"",
        ISBLANK(_bt_raw),  _bn & "" - no type"",
        ISBLANK(_primary_label),
            _bn & "" ("" & _bt_raw & "") - no strategy fit"",
        ISBLANK(_est_eur_k),
            _bn & "" -> "" & _primary_label,
        _bn & ""  ·  "" & _primary_label & ""  ·  ~EUR "" & FORMAT(_est_eur_k, ""#,0"") & ""K/yr""
    )";

if (existing != null) {
    existing.Expression = expression;
    Output("[UPDATE] " + existing.Table.Name + ".I1 Strategy Recommendation Text");
} else {
    var t = findTable("gold_battery_dispatch");
    var newM = t.AddMeasure("I1 Strategy Recommendation Text", expression);
    newM.DisplayFolder = "Page 9 / Insights";
    Output("[CREATE] gold_battery_dispatch.I1 Strategy Recommendation Text");
}

// Diagnostic to show actual building_type values
upsert_helper:;

// Helper diagnostic measure
var disp = findTable("gold_battery_dispatch");
if (disp != null) {
    Measure existingDiag = null;
    foreach (var tbl in Model.Tables) {
        foreach (var meas in tbl.Measures) {
            if (meas.Name == "I1 Type Check") { existingDiag = meas; break; }
        }
        if (existingDiag != null) break;
    }
    string diagExpr = @"VAR _bn = COALESCE(
    SELECTEDVALUE( silver_building_master[building_name] ),
    SELECTEDVALUE( gold_battery_dispatch[building_name] ) )
VAR _bt_raw = LOOKUPVALUE( silver_building_master[building_type],
                           silver_building_master[building_name], _bn )
VAR _bt_norm = LOWER( SUBSTITUTE( SUBSTITUTE( _bt_raw, "" "", ""_"" ), ""-"", ""_"" ) )
VAR _fit_types_concat = CONCATENATEX( VALUES( gold_strategy_fitness[building_type] ), gold_strategy_fitness[building_type], "", "" )
RETURN ""bn="" & _bn & "" | bt_raw='"" & _bt_raw & ""' | bt_norm='"" & _bt_norm & ""' | fitness_types="" & _fit_types_concat";
    if (existingDiag != null) {
        existingDiag.Expression = diagExpr;
        Output("[UPDATE] " + existingDiag.Table.Name + ".I1 Type Check");
    } else {
        var nm = disp.AddMeasure("I1 Type Check", diagExpr);
        nm.DisplayFolder = "Page 9 / Insights";
        Output("[CREATE] gold_battery_dispatch.I1 Type Check");
    }
}

Output("v56n LOWER + SUBSTITUTE normalization. I1 Type Check diagnostic added.");
