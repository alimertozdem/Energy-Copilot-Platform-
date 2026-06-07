// =====================================================================
// Page 9 v56j — I1 compact (one-line, works for portfolio + single)
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

upsert("gold_strategy_fitness", "I1 Strategy Recommendation Text",
@"VAR _bt = SELECTEDVALUE( silver_building_master[building_type] )
VAR _building_count = DISTINCTCOUNT( silver_building_master[building_id] )
VAR _primary_label = CALCULATE(
    SELECTEDVALUE( gold_strategy_fitness[strategy_label] ),
    gold_strategy_fitness[building_type] = _bt,
    gold_strategy_fitness[is_primary] = TRUE() )
VAR _primary_savings = CALCULATE(
    AVERAGE( gold_strategy_fitness[typical_annual_savings_eur_per_kwh] ),
    gold_strategy_fitness[building_type] = _bt,
    gold_strategy_fitness[is_primary] = TRUE() )
VAR _cap = SELECTEDVALUE( silver_building_master[battery_capacity_kwh] )
VAR _est_eur_thousand =
    IF( NOT ISBLANK(_primary_savings) && NOT ISBLANK(_cap),
        ROUND( _primary_savings * _cap / 1000, 0 ),
        BLANK() )
RETURN
    SWITCH( TRUE(),
        ISBLANK(_bt),
            ""Portfolio: "" & _building_count & "" buildings · select 1 for best-fit"",
        ISBLANK(_primary_label),
            _bt & "" · no data"",
        ISBLANK(_est_eur_thousand),
            _bt & "" → "" & _primary_label,
        _bt & "" → "" & _primary_label & ""  ·  ~€"" & FORMAT(_est_eur_thousand, ""#,0"") & ""K/yr""
    )",
"", "Page 9 / Insights");

Output("v56j I1 compact done. One line, works for both portfolio and single.");
