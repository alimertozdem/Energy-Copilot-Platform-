// =====================================================================
// Page 5 STEP 1 — DELETE only (save + refresh BEFORE running step 2)
// =====================================================================

string[] targetMeasures = new string[] {
    "Building Avg Headcount Business Hours",
    "Building Peak Headcount"
};

int deleted = 0;
foreach (string targetName in targetMeasures) {
    foreach (var tbl in Model.Tables) {
        Measure toDelete = null;
        foreach (var m in tbl.Measures) {
            if (m.Name == targetName) { toDelete = m; break; }
        }
        if (toDelete != null) {
            Output("[DELETE] " + tbl.Name + "." + targetName);
            toDelete.Delete();
            deleted++;
        }
    }
}

Output("");
Output("DELETED " + deleted + " measures.");
Output("NEXT: Ctrl+S to save -> Power BI Desktop -> Home -> Refresh");
Output("THEN: run page5_step2_create_only.cs");
