// =====================================================================
// Page 5 v55b — Force rebuild (delete all duplicates then create fresh)
// =====================================================================

string[] targetMeasures = new string[] {
    "Building Avg Headcount Business Hours",
    "Building Peak Headcount"
};

// STEP 1: Delete ALL existing measures with these names (wherever they are)
foreach (string targetName in targetMeasures) {
    foreach (var tbl in Model.Tables) {
        Measure toDelete = null;
        foreach (var m in tbl.Measures) {
            if (m.Name == targetName) { toDelete = m; break; }
        }
        if (toDelete != null) {
            Output("[DELETE] " + tbl.Name + "." + targetName);
            toDelete.Delete();
        }
    }
}

// STEP 2: Find gold_occupancy_profile table
Table host = null;
foreach (var tbl in Model.Tables) {
    if (tbl.Name == "gold_occupancy_profile") { host = tbl; break; }
}
if (host == null) {
    Output("[FAIL] gold_occupancy_profile table not found");
    return;
}

// STEP 3: Create fresh measures on gold_occupancy_profile

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
Output("Page 5 v55b DONE — duplicates cleaned + fresh measures created.");
Output("Save (Ctrl+S), then refresh Power BI Desktop.");
