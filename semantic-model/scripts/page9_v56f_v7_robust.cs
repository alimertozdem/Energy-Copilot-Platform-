// =====================================================================
// Page 9 v56f — V7 robust + battery_id debug
// =====================================================================
// Problem: System Health cards return BLANK even when single building selected.
// Likely cause: LOOKUPVALUE fails because gold_battery_dispatch[battery_id]
//   doesn't match gold_battery_technologies[battery_id] exactly.
// Fix: Use COALESCE fallbacks. If warranty not found, use design_cycles or
//   reasonable defaults from the chemistry table.
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
        foreach (var m in tbl.Measures) { if (m.Name == measureName) { existing = m; break; } }
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
    var newM = t.AddMeasure(measureName, expression);
    if (!string.IsNullOrEmpty(format)) newM.FormatString = format;
    if (!string.IsNullOrEmpty(folder)) newM.DisplayFolder = folder;
    Output("[CREATE] " + tableName + "." + measureName);
};

// =====================================================================
// DEBUG measure: show what battery_id is actually in selection
// =====================================================================
upsert("gold_battery_dispatch", "V7 Debug Battery ID",
@"VAR _disp_id = SELECTEDVALUE( gold_battery_dispatch[battery_id], ""NO-SINGLE-VALUE"" )
VAR _tech_match = LOOKUPVALUE(
    gold_battery_technologies[warranty_cycles],
    gold_battery_technologies[battery_id],
    _disp_id )
RETURN
    ""dispatch.battery_id = "" & _disp_id & ""  |  tech.warranty match = "" &
    IF( ISBLANK(_tech_match), ""NO MATCH"", FORMAT(_tech_match, ""#,0"") )",
"", "Page 9 / V7 Debug");

// =====================================================================
// V7 measures with robust fallbacks
// =====================================================================
upsert("gold_battery_dispatch", "V7 Current SoH Pct",
@"VAR _soh =
    CALCULATE( AVERAGE( gold_battery_dispatch[battery_health_percent] ),
               gold_battery_dispatch[is_simulated] = FALSE() )
VAR _soh_any =
    CALCULATE( AVERAGE( gold_battery_dispatch[battery_health_percent] ) )
VAR _final = COALESCE(_soh, _soh_any)
RETURN
    IF( NOT ISBLANK(_final), DIVIDE(_final, 100), BLANK() )",
"0.0%", "Page 9 / V7");

upsert("gold_battery_dispatch", "V7 Cycles Used Pct",
@"VAR _used =
    CALCULATE( MAX( gold_battery_dispatch[cumulative_cycles] ),
               gold_battery_dispatch[is_simulated] = FALSE() )
VAR _used_any =
    CALCULATE( MAX( gold_battery_dispatch[cumulative_cycles] ) )
VAR _used_final = COALESCE(_used, _used_any)
VAR _bid = SELECTEDVALUE( gold_battery_dispatch[battery_id] )
VAR _warranty_lookup =
    LOOKUPVALUE( gold_battery_technologies[warranty_cycles],
                 gold_battery_technologies[battery_id], _bid )
VAR _warranty_fallback =
    CALCULATE( AVERAGE( gold_battery_technologies[warranty_cycles] ) )
VAR _warranty = COALESCE(_warranty_lookup, _warranty_fallback, 5000)
RETURN
    IF( NOT ISBLANK(_used_final) && _warranty > 0,
        DIVIDE(_used_final, _warranty),
        BLANK() )",
"0.0%", "Page 9 / V7");

upsert("gold_battery_dispatch", "V7 Years Until Replacement",
@"VAR _used =
    CALCULATE( MAX( gold_battery_dispatch[cumulative_cycles] ),
               gold_battery_dispatch[is_simulated] = FALSE() )
VAR _used_any =
    CALCULATE( MAX( gold_battery_dispatch[cumulative_cycles] ) )
VAR _used_final = COALESCE(_used, _used_any)
VAR _bid = SELECTEDVALUE( gold_battery_dispatch[battery_id] )
VAR _warranty_lookup =
    LOOKUPVALUE( gold_battery_technologies[warranty_cycles],
                 gold_battery_technologies[battery_id], _bid )
VAR _warranty_fallback =
    CALCULATE( AVERAGE( gold_battery_technologies[warranty_cycles] ) )
VAR _warranty = COALESCE(_warranty_lookup, _warranty_fallback, 5000)
VAR _date_min = CALCULATE( MIN( gold_battery_dispatch[date] ) )
VAR _date_max = CALCULATE( MAX( gold_battery_dispatch[date] ) )
VAR _days = IF( NOT ISBLANK(_date_min) && NOT ISBLANK(_date_max),
                DATEDIFF(_date_min, _date_max, DAY), BLANK() )
VAR _avg_daily = IF( _days > 0, DIVIDE(_used_final, _days), BLANK() )
VAR _remaining = _warranty - _used_final
RETURN
    IF( NOT ISBLANK(_used_final)
        && _remaining > 0
        && NOT ISBLANK(_avg_daily) && _avg_daily > 0,
        DIVIDE(_remaining, _avg_daily) / 365,
        BLANK() )",
@"0.0 ""yr""", "Page 9 / V7");

Output("v56f V7 robust + debug COMPLETE.");
Output("Place [V7 Debug Battery ID] in a temporary card to see what's mismatching.");
