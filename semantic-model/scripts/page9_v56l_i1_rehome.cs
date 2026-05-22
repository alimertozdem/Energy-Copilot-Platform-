// =====================================================================
// Page 9 v56l — I1 REHOME to gold_battery_dispatch
// =====================================================================
// Reason: gold_strategy_fitness is standalone (no relationship), filter
// context from silver_building_master slicer doesn't propagate cleanly.
// Solution: Move I1 to gold_battery_dispatch which IS related to
// silver_building_master via building_id. Filter then auto-flows.
// =====================================================================

System.Func<string, Table> findTable = (string name) => {
    foreach (var tbl in Model.Tables) { if (tbl.Name == name) return tbl; }
    return null;
};

// DELETE existing I1 from wherever it is
foreach (var tbl in Model.Tables) {
    Measure toDelete = null;
    foreach (var meas in tbl.Measures) {
        if (meas.Name == "I1 Strategy Recommendation Text" || meas.Name == "I1 Diagnostic Selection") {
            toDelete = meas;
            break;
        }
    }
    if (toDelete != null) {
        Output("[DELETE] " + tbl.Name + "." + toDelete.Name);
        toDelete.Delete();
    }
}

// CREATE I1 on gold_battery_dispatch (related table)
var t = findTable("gold_battery_dispatch");
if (t == null) { Output("[FAIL] gold_battery_dispatch not found"); return; }

var m = t.AddMeasure("I1 Strategy Recommendation Text",
@"VAR _bn = SELECTEDVALUE( silver_building_master[building_name] )
VAR _bt = SELECTEDVALUE( silver_building_master[building_type] )
VAR _cap = SELECTEDVALUE( silver_building_master[battery_capacity_kwh] )
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
        ISBLANK(_bt),  ""Select 1 building"",
        ISBLANK(_primary_label), _bt & "" - no data"",
        ISBLANK(_est_eur_k), _bt & "" -> "" & _primary_label,
        _bt & "" -> "" & _primary_label & ""  ~EUR "" & FORMAT(_est_eur_k, ""#,0"") & ""K/yr""
    )");
m.FormatString = "";
m.DisplayFolder = "Page 9 / Insights";
Output("[CREATE] gold_battery_dispatch.I1 Strategy Recommendation Text (rehomed)");

Output("");
Output("DONE. Now go to Power BI Desktop:");
Output("1. Refresh");
Output("2. Click I1 card -> remove field -> drag NEW [I1 Strategy Recommendation Text] from gold_battery_dispatch -> Page 9 / Insights folder");
Output("3. Change building -> text should now react");
