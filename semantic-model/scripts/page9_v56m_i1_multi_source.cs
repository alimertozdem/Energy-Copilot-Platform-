// =====================================================================
// Page 9 v56m — I1 reads building_name from ANY table (multi-source COALESCE)
// =====================================================================
// User identified the real issue: slicer might be on different table than
// silver_building_master. Try all 3 sources for building_name.
// =====================================================================

System.Func<string, Table> findTable = (string name) => {
    foreach (var tbl in Model.Tables) { if (tbl.Name == name) return tbl; }
    return null;
};

// Find and update existing I1 wherever it lives
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
VAR _bt = COALESCE(
    SELECTEDVALUE( silver_building_master[building_type] ),
    LOOKUPVALUE( silver_building_master[building_type],
                 silver_building_master[building_name], _bn )
)
VAR _cap = COALESCE(
    SELECTEDVALUE( silver_building_master[battery_capacity_kwh] ),
    LOOKUPVALUE( silver_building_master[battery_capacity_kwh],
                 silver_building_master[building_name], _bn )
)
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
        ISBLANK(_primary_label), _bt & "" - no data"",
        ISBLANK(_est_eur_k), _bn & "" ("" & _bt & "") -> "" & _primary_label,
        _bn & "" ("" & _bt & "") -> "" & _primary_label & ""  ~EUR "" & FORMAT(_est_eur_k, ""#,0"") & ""K/yr""
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

Output("v56m multi-source COALESCE — reads building_name from silver OR dispatch OR simulation");
