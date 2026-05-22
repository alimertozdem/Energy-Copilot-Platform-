// =====================================================================
// PROBE v2 — Full table listing + Page 9 requirement check
// =====================================================================
// Read-only. Safe.
// =====================================================================

Output("================================================================");
Output("FULL TABLE LIST (model: " + Model.Name + ")");
Output("================================================================");

int idx = 0;
var allNames = new System.Collections.Generic.List<string>();
foreach (var t in Model.Tables.OrderBy(t => t.Name)) {
    idx++;
    allNames.Add(t.Name);
    Output(idx.ToString("00") + "  " + t.Name);
}

Output("");
Output("================================================================");
Output("PAGE 9 REQUIREMENT CHECK");
Output("================================================================");

string[] required = new string[] {
    "silver_building_master",
    "gold_battery_dispatch",
    "gold_battery_simulation",
    "gold_battery_technologies",
    "gold_battery_hourly_dispatch",
    "gold_country_regulations",
    "gold_strategy_fitness"
};

foreach (var req in required) {
    bool found = allNames.Contains(req);
    string status = found ? "[OK] PRESENT  " : "[MISSING]     ";
    Output(status + req);

    // Fuzzy search if missing — check for close names
    if (!found) {
        foreach (var name in allNames) {
            string lower = name.ToLower().Replace(" ", "_").Replace("-", "_");
            string lowerReq = req.ToLower();
            // Match by suffix or contains
            if (lower.Contains(lowerReq) || lowerReq.Contains(lower.Replace("dbo_", "").Replace("dbo.", ""))) {
                Output("              ?  Possible match: '" + name + "'");
            }
        }
    }
}
