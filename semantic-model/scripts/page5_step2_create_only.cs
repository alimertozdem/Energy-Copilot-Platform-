// =====================================================================
// Page 5 STEP 2 — CREATE only (after step 1 + save + refresh)
// =====================================================================

Table host = null;
foreach (var tbl in Model.Tables) {
    if (tbl.Name == "gold_occupancy_profile") { host = tbl; break; }
}
if (host == null) {
    Output("[FAIL] gold_occupancy_profile not found");
    return;
}

// Safety check — make sure no duplicates exist (from step 1)
foreach (var tbl in Model.Tables) {
    foreach (var m in tbl.Measures) {
        if (m.Name == "Building Avg Headcount Business Hours" ||
            m.Name == "Building Peak Headcount") {
            Output("[ABORT] Duplicate still exists: " + tbl.Name + "." + m.Name);
            Output("Run step 1 again, save, refresh, then retry step 2");
            return;
        }
    }
}

var m1 = host.AddMeasure("Building Avg Headcount Business Hours",
@"VAR _avg_prob =
    CALCULATE(
        AVERAGE( gold_occupancy_profile[occupancy_probability] ),
        gold_occupancy_profile[hour_of_day] >= 8,
        gold_occupancy_profile[hour_of_day] <= 18
    )
VAR _max_occ =
    CALCULATE(
        SUM( silver_building_master[max_occupants] ),
        TREATAS(
            VALUES( gold_occupancy_profile[building_id] ),
            silver_building_master[building_id]
        )
    )
VAR _result = _avg_prob * _max_occ
RETURN
    IF( ISBLANK( _avg_prob ) || ISBLANK( _max_occ ) || _max_occ = 0,
        BLANK(),
        ROUND( _result, 0 )
    )");
m1.FormatString = "#,0";
m1.DisplayFolder = "Page 5 / Headcount";
Output("[CREATE] gold_occupancy_profile.Building Avg Headcount Business Hours");

var m2 = host.AddMeasure("Building Peak Headcount",
@"VAR _peak_prob =
    CALCULATE(
        MAX( gold_occupancy_profile[occupancy_probability] )
    )
VAR _max_occ =
    CALCULATE(
        SUM( silver_building_master[max_occupants] ),
        TREATAS(
            VALUES( gold_occupancy_profile[building_id] ),
            silver_building_master[building_id]
        )
    )
VAR _result = _peak_prob * _max_occ
RETURN
    IF( ISBLANK( _peak_prob ) || ISBLANK( _max_occ ) || _max_occ = 0,
        BLANK(),
        ROUND( _result, 0 )
    )");
m2.FormatString = "#,0";
m2.DisplayFolder = "Page 5 / Headcount";
Output("[CREATE] gold_occupancy_profile.Building Peak Headcount");

Output("");
Output("DONE. Save (Ctrl+S) -> Power BI Desktop -> Home -> Refresh");
Output("Visual on Page 5 should auto-rebind to new measures.");
