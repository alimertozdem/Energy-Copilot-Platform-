// =====================================================================
// EnergyLens — PAGE 9 (Battery) · FINAL consolidated measure script
// TE2 → C# Script → (File → Open) → F5 → File → Reload (if schema changed) →
//   F5 again → Ctrl+S → Power BI Refresh.
// ---------------------------------------------------------------------
// Fixes everything at the measure layer, ROBUSTLY (no fragile notebook-column
// dependency for V7 — computed from cycle_depth_pct + warranty so it can NEVER
// break again, regardless of how gold_battery_dispatch is rewritten):
//   1. Sweep orphan V6 measures off the dead gold_battery_hourly_profile.
//   2. C4 Round Trip Efficiency — defensive scaling (9050 -> 90.5).
//   3. V6 24h measures on the live gold_battery_hourly_dispatch.
//   4. V7 battery-health panel — DAX-only (Annual Cycles, Years, Cycle Depth,
//      Warranty) + guarded real-SoH (shows only if the patch added the column).
//   5. C2 Payback — best viable scenario (not the absurd 230-yr average).
// Verified against semantic-model/_probe_output.txt.
// =====================================================================

int n = 0, swept = 0;
System.Action<string,string,string,string,string> U = (tbl, nm, ex, fmt, fld) => {
    if (!Model.Tables.Any(t => t.Name == tbl)) { Output("SKIP (no table '" + tbl + "'): " + nm); return; }
    var m = Model.AllMeasures.FirstOrDefault(x => x.Name == nm);
    if (m == null) m = Model.Tables[tbl].AddMeasure(nm, ex); else m.Expression = ex;
    if (fmt != null) m.FormatString = fmt;
    if (fld != null) m.DisplayFolder = fld;
    n++; Output("ok: " + nm);
};

// ── 1. SWEEP orphan V6 measures off the dead profile table ───────────
foreach (var deadTbl in new string[]{ "gold_battery_hourly_profile" }) {
    var t = Model.Tables.FirstOrDefault(x => x.Name == deadTbl);
    if (t == null) { Output("clean (table absent): " + deadTbl); continue; }
    foreach (var mm in t.Measures.ToList()) { Output("swept: " + deadTbl + "." + mm.Name); mm.Delete(); swept++; }
    try { t.Delete(); Output("dropped dead table: " + deadTbl); } catch (System.Exception e) { Output("kept (measures swept): " + deadTbl); }
}
foreach (var mm in Model.AllMeasures.ToList()) {
    if (mm.Table != null && mm.Table.Columns.Count == 0) { Output("swept orphan: " + mm.Table.Name + "." + mm.Name); mm.Delete(); swept++; }
}

// ── 2. C4 RTE — defensive (handles fraction OR percent storage) ──────
U("gold_battery_dispatch","C4 Round Trip Efficiency Pct",@"VAR r = AVERAGE( gold_battery_dispatch[round_trip_efficiency] ) RETURN IF( r <= 1.5, r * 100, r )","0.0",null);

// ── 3. V6 24h behavior (live table gold_battery_hourly_dispatch) ─────
string FV6 = "Battery 24h (V6)";
U("gold_battery_hourly_dispatch","V6 Charge Rate",   @"SUM( gold_battery_hourly_dispatch[charge_kwh] )",       "#,##0.0", FV6);
U("gold_battery_hourly_dispatch","V6 Discharge Rate",@"SUM( gold_battery_hourly_dispatch[discharge_kwh] )",    "#,##0.0", FV6);
U("gold_battery_hourly_dispatch","V6 SoC Pct",       @"AVERAGE( gold_battery_hourly_dispatch[soc_percent] )",  "0.0",     FV6);
U("gold_battery_hourly_dispatch","V6 Price Index",   @"AVERAGE( gold_battery_hourly_dispatch[grid_price_index] )","0.00", FV6);

// ── 4. V7 battery-health — DAX-ONLY core (no notebook columns) ───────
string FV7 = "Battery Health (V7)";
// usage intensity (equivalent full cycles / yr) from cycle_depth_pct — always present
U("gold_battery_dispatch","V7 Annual Cycles",@"ROUND( AVERAGE( gold_battery_dispatch[cycle_depth_pct] ) / 100.0 * 365.0, 0 )","#,##0",FV7);
U("gold_battery_dispatch","V7 Avg Cycle Depth Pct",@"AVERAGE( gold_battery_dispatch[cycle_depth_pct] )","0.0",FV7);
U("gold_battery_dispatch","V7 Warranty Cycles",@"LOOKUPVALUE( gold_battery_technologies[warranty_cycles], gold_battery_technologies[battery_type], SELECTEDVALUE( gold_battery_dispatch[battery_type] ) )","#,##0",FV7);
// replacement horizon = min(cycle-limited life, 20-yr calendar limit) — robust, no column
U("gold_battery_dispatch","V7 Years Until Replacement",@"VAR ac = [V7 Annual Cycles] VAR cyc = DIVIDE( [V7 Warranty Cycles], ac ) RETURN IF( ISBLANK(cyc), BLANK(), MIN( cyc, 20 ) )","0.0",FV7);
// cycles used vs warranty over the observed window (robust)
U("gold_battery_dispatch","V7 Cycles Used Pct",@"VAR used = SUM( gold_battery_dispatch[cycle_depth_pct] ) / 100.0 RETURN DIVIDE( used, [V7 Warranty Cycles] )","0.0%",FV7);

// real stored SoH — only if the patch/notebook added the column (else skipped, no error)
var disp = Model.Tables.FirstOrDefault(t => t.Name == "gold_battery_dispatch");
if (disp != null && disp.Columns.Any(c => c.Name == "battery_health_percent")) {
    U("gold_battery_dispatch","V7 Current SoH Pct",@"AVERAGE( gold_battery_dispatch[battery_health_percent] )","0.0",FV7);
    U("gold_battery_dispatch","V7 SoH Color",@"VAR s=[V7 Current SoH Pct] RETURN SWITCH( TRUE(), ISBLANK(s),""#AAAAAA"", s>=90,""#2ECC40"", s>=80,""#FF851B"", ""#FF4136"" )",null,FV7);
    Output("V7 real SoH measures created (battery_health_percent column present).");
} else {
    // remove a stale SoH measure if it exists, so it can't error on a missing column
    foreach (var mm in Model.AllMeasures.Where(x => x.Name == "V7 Current SoH Pct").ToList()) { mm.Delete(); Output("removed stale V7 Current SoH Pct (column absent — run 12b_patch_soh_columns.py to enable real SoH)"); }
    Output("NOTE: battery_health_percent column absent -> SoH skipped. Run 12b_patch_soh_columns.py (overwrite) to show real SoH.");
}

// ── 5. C2 Payback — best viable scenario (not the 230-yr average) ────
U("gold_battery_simulation","C2 Payback Years",@"CALCULATE( MIN( gold_battery_simulation[payback_years] ), gold_battery_simulation[total_capex_eur] > 0, gold_battery_simulation[payback_years] > 0 )","0.0",null);

Output("=====================================================");
Output("PAGE 9 FINAL — measures set: " + n + " | orphans swept: " + swept);
Output("File->Reload if 3 errors persist, then F5 again. Ctrl+S -> Refresh.");
Output("=====================================================");
