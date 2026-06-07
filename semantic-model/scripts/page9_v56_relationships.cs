// =====================================================================
// Page 9 v56 — Relationship setup (Tabular Editor 2 script)
// =====================================================================
// Date    : 2026-05-21
// Purpose : Create the 2 relationships needed by Page 9 v56 master DAX.
//           Idempotent — re-runnable. Skips if relationship exists.
//
// PRE-FLIGHT
//   - All 5 Page 9 tables must be in the model (probe_model_tables_v2.cs
//     should report [OK] PRESENT for all 7 required tables).
//
// WHAT THIS SCRIPT DOES
//   1. gold_battery_dispatch[building_id]  ───►  silver_building_master[building_id]
//   2. gold_battery_simulation[building_id] ──►  silver_building_master[building_id]
//
// WHAT IT DOES NOT DO (intentional design)
//   - gold_country_regulations stays STANDALONE
//   - gold_strategy_fitness stays STANDALONE
//   - gold_battery_technologies stays STANDALONE (DAX uses LOOKUPVALUE)
//   This keeps V1 strategy matrix and V5 country×chemistry heatmap as
//   GLOBAL reference visuals (not filtered by building selection).
//
// USAGE
//   Paste into TE2 → Advanced Scripting → Run (F5) → Save (Ctrl+S)
// =====================================================================

// Safe table lookup helper
System.Func<string, Table> findTable = (string name) => {
    foreach (var tbl in Model.Tables) {
        if (tbl.Name == name) return tbl;
    }
    return null;
};

// Safe column lookup helper
System.Func<Table, string, Column> findColumn = (Table tbl, string colName) => {
    if (tbl == null) return null;
    foreach (var c in tbl.Columns) {
        if (c.Name == colName) return c;
    }
    return null;
};

// Idempotent: create relationship only if missing
System.Action<string,string,string,string> ensureRelationship =
    (string fromTable, string fromColumn, string toTable, string toColumn) =>
{
    var ft = findTable(fromTable);
    var tt = findTable(toTable);
    if (ft == null) { Output("[SKIP] From-table missing: " + fromTable); return; }
    if (tt == null) { Output("[SKIP] To-table missing: "   + toTable);   return; }

    var fc = findColumn(ft, fromColumn);
    var tc = findColumn(tt, toColumn);
    if (fc == null) { Output("[SKIP] From-column missing: " + fromTable + "[" + fromColumn + "]"); return; }
    if (tc == null) { Output("[SKIP] To-column missing: "   + toTable   + "[" + toColumn   + "]"); return; }

    // Check if already exists
    foreach (var r in Model.Relationships) {
        var sr = r as SingleColumnRelationship;
        if (sr == null) continue;
        if (sr.FromColumn == fc && sr.ToColumn == tc) {
            Output("[EXISTS] " + fromTable + "[" + fromColumn + "] -> " + toTable + "[" + toColumn + "]");
            return;
        }
    }

    // Create
    var rel = Model.AddRelationship();
    rel.FromColumn = fc;
    rel.ToColumn   = tc;
    rel.FromCardinality = RelationshipEndCardinality.Many;
    rel.ToCardinality   = RelationshipEndCardinality.One;
    rel.CrossFilteringBehavior = CrossFilteringBehavior.OneDirection;
    rel.IsActive = true;

    Output("[CREATE] " + fromTable + "[" + fromColumn + "] -> " + toTable + "[" + toColumn + "]");
};

// =====================================================================
// Required relationships for Page 9 v56
// =====================================================================

Output("Page 9 v56 — Relationship setup");
Output("================================================================");

ensureRelationship("gold_battery_dispatch",   "building_id", "silver_building_master", "building_id");
ensureRelationship("gold_battery_simulation", "building_id", "silver_building_master", "building_id");

Output("================================================================");
Output("Done. Save (Ctrl+S), then run page9_v56_master_install.cs.");
Output("");
Output("Intentional non-relationships (do NOT add — kept standalone):");
Output("  - gold_country_regulations  (V5 heatmap global reference)");
Output("  - gold_strategy_fitness     (V1 matrix global reference)");
Output("  - gold_battery_technologies (DAX uses LOOKUPVALUE pattern)");
