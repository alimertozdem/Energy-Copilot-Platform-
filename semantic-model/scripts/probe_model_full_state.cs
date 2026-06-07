// =====================================================================
// PROBE — Full model state (READ-ONLY)
// =====================================================================
// Run in Tabular Editor 2: paste into the C# Script tab, Run (F5),
// then copy the entire Output and send it back.
//
// Dumps everything needed to build the consolidated measure script safely:
//   1) every TABLE with its COLUMNS (+ datatype)
//   2) every MEASURE with its home table
//   3) every RELATIONSHIP (from -> to, active flag)
//
// Nothing is modified. Safe to run any time.
// =====================================================================

Output("######## 1. TABLES + COLUMNS ########");
foreach (var t in Model.Tables.OrderBy(t => t.Name)) {
    Output("");
    Output("TABLE: " + t.Name + "   (" + t.Columns.Count + " cols, " + t.Measures.Count + " measures)");
    foreach (var c in t.Columns.OrderBy(c => c.Name)) {
        Output("   col | " + c.Name + " | " + c.DataType);
    }
}

Output("");
Output("######## 2. MEASURES (home table | measure name) ########");
int mcount = 0;
foreach (var t in Model.Tables.OrderBy(t => t.Name)) {
    foreach (var m in t.Measures.OrderBy(m => m.Name)) {
        mcount++;
        Output("MEASURE | " + t.Name + " | " + m.Name);
    }
}
Output("TOTAL MEASURES: " + mcount);

Output("");
Output("######## 3. RELATIONSHIPS ########");
foreach (var r in Model.Relationships) {
    Output("REL | " + r.FromTable.Name + "[" + r.FromColumn.Name + "] -> "
           + r.ToTable.Name + "[" + r.ToColumn.Name + "]"
           + "  active=" + r.IsActive
           + "  xfilter=" + r.CrossFilteringBehavior);
}

Output("");
Output("######## DONE — copy everything above ########");
