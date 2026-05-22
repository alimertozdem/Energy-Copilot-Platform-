// =====================================================================
// Page 5 v55 — Headcount Surgical Fix (Tabular Editor 2 script)
// =====================================================================
// Date    : 2026-05-21
// Target  : Power BI semantic model "EnergyCopilotModel"
// Action  : Update the two broken headcount measures to compute on-the-fly
//           from occupancy_probability × max_occupants (no longer references
//           the non-existent column gold_occupancy_profile[estimated_headcount])
//
// PRE-REQUISITES
//   1. Open Power BI Desktop (Live connect to the semantic model).
//   2. External Tools → Tabular Editor 2.
//   3. Make sure both tables exist in the model:
//        - gold_occupancy_profile  (cols: building_id, hour_of_day,
//                                          occupancy_probability …)
//        - silver_building_master  (cols: building_id, max_occupants …)
//   4. Make sure a 1-to-many relationship exists
//        silver_building_master[building_id]  ←  gold_occupancy_profile[building_id]
//        (used by TREATAS — even without an active relationship, TREATAS works.)
//
// USAGE
//   - Paste this script into Tabular Editor 2 "Advanced Scripting" tab.
//   - Click "Run".
//   - Save model (Ctrl+S) → returns to Power BI → click Refresh on Page 5.
// =====================================================================

string targetTableName    = "gold_occupancy_profile";

string avgBusinessHoursExpr =
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
    )";

string peakHeadcountExpr =
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
    )";

// Locate the home table.
var homeTable = Model.Tables[targetTableName];
if (homeTable == null) {
    Error("Table '" + targetTableName + "' not found in model. Aborting.");
    return;
}

// Helper that updates if found, creates if missing.
System.Action<string,string,string> upsertMeasure = (name, expr, folder) => {
    var existing = homeTable.Measures.FirstOrDefault(m => m.Name == name);
    if (existing != null) {
        existing.Expression = expr;
        existing.FormatString = "#,0";
        existing.DisplayFolder = folder;
        Info("Updated measure: " + name);
    } else {
        var m = homeTable.AddMeasure(name, expr);
        m.FormatString = "#,0";
        m.DisplayFolder = folder;
        Info("Created measure: " + name);
    }
};

upsertMeasure(
    "Building Avg Headcount Business Hours",
    avgBusinessHoursExpr,
    "Page 5 / Headcount"
);

upsertMeasure(
    "Building Peak Headcount",
    peakHeadcountExpr,
    "Page 5 / Headcount"
);

Info("Page 5 v55 surgical fix applied. Save model (Ctrl+S) and refresh Power BI report.");
