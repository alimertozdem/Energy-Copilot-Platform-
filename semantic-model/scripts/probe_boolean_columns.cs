// =====================================================================
// PROBE — Check data types of boolean-looking columns
// =====================================================================
// Read-only. Identifies columns that store "true"/"false" as Text
// instead of Boolean, which breaks the v56 measures.
// =====================================================================

string[] tablesToCheck = new string[] {
    "gold_battery_dispatch",
    "gold_battery_simulation",
    "gold_battery_technologies",
    "gold_country_regulations",
    "gold_strategy_fitness"
};

string[] suspectColumns = new string[] {
    "is_simulated", "is_active_strategy", "eu_compliant",
    "is_eu_member", "lfp_allowed", "nmc_allowed_new_2025",
    "nca_allowed", "sodium_ion_approved", "solid_state_pilot",
    "v2g_grid_code_ready", "frequency_market_eligible",
    "capacity_market_eligible", "sub_metering_required",
    "demand_charge_required", "thermal_management_required",
    "is_primary", "is_secondary"
};

Output("=================================================================");
Output("Boolean column type probe");
Output("=================================================================");
Output("");
Output(string.Format("{0,-32} {1,-32} {2}", "TABLE", "COLUMN", "TYPE"));
Output("-----------------------------------------------------------------");

foreach (var tName in tablesToCheck) {
    Table t = null;
    foreach (var tbl in Model.Tables) {
        if (tbl.Name == tName) { t = tbl; break; }
    }
    if (t == null) continue;

    foreach (var c in t.Columns) {
        bool isSuspect = false;
        foreach (var s in suspectColumns) {
            if (c.Name == s) { isSuspect = true; break; }
        }
        if (!isSuspect) continue;

        string typeStr = c.DataType.ToString();
        string flag = (typeStr == "String") ? "[TEXT - needs string comparison]" :
                      (typeStr == "Boolean") ? "[BOOL - OK]" :
                      "[" + typeStr + "]";
        Output(string.Format("{0,-32} {1,-32} {2}", t.Name, c.Name, flag));
    }
}

Output("");
Output("=================================================================");
Output("ACTION");
Output("=================================================================");
Output("If you see [TEXT - needs string comparison] above, run the");
Output("page9_v56b_text_boolean_fix.cs patch script next.");
