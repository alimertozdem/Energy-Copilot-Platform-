// =====================================================================
// Page 9 v56g — Use battery_type for warranty lookup (battery_id mismatch fix)
// =====================================================================
// Debug showed: dispatch.battery_id = B001_BATT_01 (building-based)
//               tech.battery_id     = CATL_LFP_200 (product-based)
// They don't match. Both tables have battery_type (LFP, NMC, NCA, etc.)
// Aggregate technologies by battery_type and use that for lookup.
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

// Warranty lookup via battery_type (e.g. LFP avg = 5500 cycles, NMC = 3000)
upsert("gold_battery_dispatch", "V7 Cycles Used Pct",
@"VAR _used = CALCULATE( MAX( gold_battery_dispatch[cumulative_cycles] ) )
VAR _btype = SELECTEDVALUE( gold_battery_dispatch[battery_type] )
VAR _warranty_by_type =
    CALCULATE(
        AVERAGE( gold_battery_technologies[warranty_cycles] ),
        gold_battery_technologies[battery_type] = _btype )
VAR _warranty_all =
    CALCULATE( AVERAGE( gold_battery_technologies[warranty_cycles] ) )
VAR _warranty = COALESCE( _warranty_by_type, _warranty_all, 5000 )
RETURN
    IF( NOT ISBLANK(_used) && _warranty > 0,
        DIVIDE(_used, _warranty), BLANK() )",
"0.0%", "Page 9 / V7");

upsert("gold_battery_dispatch", "V7 Years Until Replacement",
@"VAR _used = CALCULATE( MAX( gold_battery_dispatch[cumulative_cycles] ) )
VAR _btype = SELECTEDVALUE( gold_battery_dispatch[battery_type] )
VAR _warranty_by_type =
    CALCULATE( AVERAGE( gold_battery_technologies[warranty_cycles] ),
               gold_battery_technologies[battery_type] = _btype )
VAR _warranty_all =
    CALCULATE( AVERAGE( gold_battery_technologies[warranty_cycles] ) )
VAR _warranty = COALESCE( _warranty_by_type, _warranty_all, 5000 )
VAR _date_min = CALCULATE( MIN( gold_battery_dispatch[date] ) )
VAR _date_max = CALCULATE( MAX( gold_battery_dispatch[date] ) )
VAR _days = IF( NOT ISBLANK(_date_min) && NOT ISBLANK(_date_max),
                DATEDIFF(_date_min, _date_max, DAY), BLANK() )
VAR _avg_daily = IF( _days > 0, DIVIDE(_used, _days), BLANK() )
VAR _remaining = _warranty - _used
RETURN
    IF( NOT ISBLANK(_used) && _remaining > 0 && _avg_daily > 0,
        DIVIDE(_remaining, _avg_daily) / 365, BLANK() )",
@"0.0 ""yr""", "Page 9 / V7");

// Update debug measure to show battery_type lookup instead
upsert("gold_battery_dispatch", "V7 Debug Battery ID",
@"VAR _btype = SELECTEDVALUE( gold_battery_dispatch[battery_type], ""NO-SINGLE-TYPE"" )
VAR _w = CALCULATE( AVERAGE( gold_battery_technologies[warranty_cycles] ),
                    gold_battery_technologies[battery_type] = _btype )
RETURN
    ""battery_type = "" & _btype & ""  |  avg warranty cycles = "" &
    IF( ISBLANK(_w), ""NO MATCH"", FORMAT(_w, ""#,0"") )",
"", "Page 9 / V7 Debug");

Output("v56g battery_type lookup COMPLETE. Now V7 should show real values.");
