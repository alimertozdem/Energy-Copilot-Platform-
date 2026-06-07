// =====================================================================
// EnergyLens — PAGE 9 (Battery) · STAGE 1: clear errors (orphan sweep + RTE)
// TE2 → C# Script → (File → Open this file) → F5 → Ctrl+S → PBI Refresh.
// ---------------------------------------------------------------------
// FIX A — Missing_References dialog: the 24h visual is bound to the DEAD table
//   gold_battery_hourly_profile (orphan V6 measures + hour_label). The live
//   source is gold_battery_hourly_dispatch (has hour_label, charge_kwh,
//   discharge_kwh, soc_percent, grid_price_index). Sweep the orphans + drop
//   the dead table; (re)ensure the V6 measures live on the dispatch table.
// FIX B — C4 Round Trip Efficiency shows 9050%: round_trip_efficiency is
//   already stored as ~90.5 (percent), so ×100 double-scales it. Defensive:
//   IF(r <= 1.5, r*100, r) → handles both fraction and percent storage.
// (Verified against semantic-model/_probe_output.txt.)
// =====================================================================

int created = 0, updated = 0, swept = 0;
string F = "Battery 24h (V6)";
System.Action<string,string,string,string,string> U = (tbl, nm, ex, fmt, fld) => {
    if (!Model.Tables.Any(t => t.Name == tbl)) { Output("SKIP (no table '" + tbl + "'): " + nm); return; }
    var m = Model.AllMeasures.FirstOrDefault(x => x.Name == nm);
    if (m == null) { m = Model.Tables[tbl].AddMeasure(nm, ex); created++; }
    else { m.Expression = ex; updated++; }
    if (fmt != null) m.FormatString = fmt;
    if (fld != null) m.DisplayFolder = fld;
};

// ── FIX A.1 — sweep orphans off the dead battery profile table ───────
foreach (var deadTbl in new string[]{ "gold_battery_hourly_profile" }) {
    var t = Model.Tables.FirstOrDefault(x => x.Name == deadTbl);
    if (t == null) { Output("clean (table absent): " + deadTbl); continue; }
    foreach (var m in t.Measures.ToList()) { Output("swept: " + deadTbl + "." + m.Name); m.Delete(); swept++; }
    try { t.Delete(); Output("dropped dead table: " + deadTbl); }
    catch (System.Exception e) { Output("kept table (measures swept): " + deadTbl + " — remove it via Power BI model view if it lingers"); }
}
// catch-all: any measure stranded on a 0-column (broken) table
foreach (var m in Model.AllMeasures.ToList()) {
    if (m.Table != null && m.Table.Columns.Count == 0) { Output("swept orphan: " + m.Table.Name + "." + m.Name); m.Delete(); swept++; }
}

// ── FIX A.2 — (re)ensure V6 24h measures on the LIVE dispatch table ──
U("gold_battery_hourly_dispatch","V6 Charge Rate",   @"SUM( gold_battery_hourly_dispatch[charge_kwh] )",      "#,##0.0", F);
U("gold_battery_hourly_dispatch","V6 Discharge Rate",@"SUM( gold_battery_hourly_dispatch[discharge_kwh] )",   "#,##0.0", F);
U("gold_battery_hourly_dispatch","V6 SoC Pct",       @"AVERAGE( gold_battery_hourly_dispatch[soc_percent] )", "0.0",     F);
U("gold_battery_hourly_dispatch","V6 Price Index",   @"AVERAGE( gold_battery_hourly_dispatch[grid_price_index] )","0.00", F);

// ── FIX B — RTE defensive scaling (9050 → 90.5) ─────────────────────
U("gold_battery_dispatch","C4 Round Trip Efficiency Pct",@"VAR r = AVERAGE( gold_battery_dispatch[round_trip_efficiency] ) RETURN IF( r <= 1.5, r * 100, r )","0.0", null);

Output("=====================================================");
Output("PAGE 9 STAGE 1 DONE — swept: " + swept + " | created: " + created + " | updated: " + updated);
Output("Ctrl+S -> Refresh. Rebind the 24h visual to gold_battery_hourly_dispatch[hour_label]");
Output("  + V6 Charge/Discharge/SoC/Price. Then send me the fresh error state.");
Output("=====================================================");
