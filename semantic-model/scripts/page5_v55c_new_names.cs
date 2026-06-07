// =====================================================================
// Page 5 v55c — Create with NEW names to avoid duplicate conflicts
// =====================================================================
// Old names had naming conflicts. Use new names ending in "Calc".
// User will rebind the visual to new measure names.
// =====================================================================

Table host = null;
foreach (var tbl in Model.Tables) {
    if (tbl.Name == "gold_occupancy_profile") { host = tbl; break; }
}
if (host == null) {
    Output("[FAIL] gold_occupancy_profile not found");
    return;
}

string[] newNames = new string[] {
    "Building Avg Headcount Calc",
    "Building Peak Headcount Calc"
};

// Make sure these new names don't exist already
foreach (string n in newNames) {
    foreach (var tbl in Model.Tables) {
        Measure d = null;
        foreach (var m in tbl.Measures) { if (m.Name == n) { d = m; break; } }
        if (d != null) {
            Output("[CLEAN] removing existing " + tbl.Name + "." + n);
            d.Delete();
        }
    }
}

var m1 = host.AddMeasure("Building Avg Headcount Calc",
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
Output("[CREATE] gold_occupancy_profile.Building Avg Headcount Calc");

var m2 = host.AddMeasure("Building Peak Headcount Calc",
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
Output("[CREATE] gold_occupancy_profile.Building Peak Headcount Calc");

Output("");
Output("DONE. New measure names:");
Output("  - Building Avg Headcount Calc");
Output("  - Building Peak Headcount Calc");
Output("");
Output("NEXT: Save (Ctrl+S) -> Power BI Desktop refresh");
Output("THEN: On Page 5 visual, remove old field, drag NEW measure.");
