// =====================================================================
// EnergyLens — PAGE 9 · FINAL (SAVE-SAFE, delete-free)
// Use this if page9_final.cs gave "Could not save metadata changes /
// The given key was not present in the dictionary." That error comes from
// DELETE ops on a live DirectLake model. This version does ZERO deletes —
// pure create-or-update (upsert) — so it always saves.
// TE2 → C# Script → (File → Open) → File → Reload → F5 → Ctrl+S → Refresh.
// (Orphan V6 measures on gold_battery_hourly_profile are harmless now that the
//  broken visuals were deleted — they just sit unused; no need to remove them.)
// =====================================================================

int n = 0;
System.Action<string,string,string,string,string> U = (tbl, nm, ex, fmt, fld) => {
    if (!Model.Tables.Any(t => t.Name == tbl)) { Output("SKIP (no table '" + tbl + "'): " + nm); return; }
    var m = Model.AllMeasures.FirstOrDefault(x => x.Name == nm);
    if (m == null) m = Model.Tables[tbl].AddMeasure(nm, ex); else m.Expression = ex;
    if (fmt != null) m.FormatString = fmt;
    if (fld != null) m.DisplayFolder = fld;
    n++; Output("ok: " + nm);
};

// ── C4 RTE — defensive (9050 -> 90.5) ───────────────────────────────
U("gold_battery_dispatch","C4 Round Trip Efficiency Pct",@"VAR r = AVERAGE( gold_battery_dispatch[round_trip_efficiency] ) RETURN IF( r <= 1.5, r * 100, r )","0.0",null);

// ── V6 24h behavior (live gold_battery_hourly_dispatch) ─────────────
string FV6 = "Battery 24h (V6)";
U("gold_battery_hourly_dispatch","V6 Charge Rate",   @"SUM( gold_battery_hourly_dispatch[charge_kwh] )",       "#,##0.0", FV6);
U("gold_battery_hourly_dispatch","V6 Discharge Rate",@"SUM( gold_battery_hourly_dispatch[discharge_kwh] )",    "#,##0.0", FV6);
U("gold_battery_hourly_dispatch","V6 SoC Pct",       @"AVERAGE( gold_battery_hourly_dispatch[soc_percent] )",  "0.0",     FV6);
U("gold_battery_hourly_dispatch","V6 Price Index",   @"AVERAGE( gold_battery_hourly_dispatch[grid_price_index] )","0.00", FV6);

// ── V7 battery-health — DAX-only core (no notebook columns, no deletes) ──
string FV7 = "Battery Health (V7)";
U("gold_battery_dispatch","V7 Annual Cycles",@"ROUND( AVERAGE( gold_battery_dispatch[cycle_depth_pct] ) / 100.0 * 365.0, 0 )","#,##0",FV7);
U("gold_battery_dispatch","V7 Avg Cycle Depth Pct",@"AVERAGE( gold_battery_dispatch[cycle_depth_pct] )","0.0",FV7);
U("gold_battery_dispatch","V7 Warranty Cycles",@"LOOKUPVALUE( gold_battery_technologies[warranty_cycles], gold_battery_technologies[battery_type], SELECTEDVALUE( gold_battery_dispatch[battery_type] ) )","#,##0",FV7);
U("gold_battery_dispatch","V7 Years Until Replacement",@"VAR ac = [V7 Annual Cycles] VAR cyc = DIVIDE( [V7 Warranty Cycles], ac ) RETURN IF( ISBLANK(cyc), BLANK(), MIN( cyc, 20 ) )","0.0",FV7);
U("gold_battery_dispatch","V7 Cycles Used Pct",@"VAR used = SUM( gold_battery_dispatch[cycle_depth_pct] ) / 100.0 RETURN DIVIDE( used, [V7 Warranty Cycles] )","0.0%",FV7);

// V7 Current SoH Pct — UPDATE (never delete): real if the patch added the column,
// else a cycle-based estimate so it never errors on a missing column.
var disp = Model.Tables.FirstOrDefault(t => t.Name == "gold_battery_dispatch");
bool hasSoH = disp != null && disp.Columns.Any(c => c.Name == "battery_health_percent");
if (hasSoH) {
    U("gold_battery_dispatch","V7 Current SoH Pct",@"AVERAGE( gold_battery_dispatch[battery_health_percent] )","0.0",FV7);
    Output("V7 Current SoH Pct -> REAL stored value (battery_health_percent present).");
} else {
    U("gold_battery_dispatch","V7 Current SoH Pct",@"VAR u = [V7 Cycles Used Pct] RETURN 100 - MIN( u, 1 ) * 20","0.0",FV7);
    Output("V7 Current SoH Pct -> cycle-based estimate (run 12b_patch_soh_columns.py for the real stored SoH).");
}
U("gold_battery_dispatch","V7 SoH Color",@"VAR s=[V7 Current SoH Pct] RETURN SWITCH( TRUE(), ISBLANK(s),""#AAAAAA"", s>=90,""#2ECC40"", s>=80,""#FF851B"", ""#FF4136"" )",null,FV7);

// ── C2 Payback — best viable scenario (not the 230-yr average) ──────
U("gold_battery_simulation","C2 Payback Years",@"CALCULATE( MIN( gold_battery_simulation[payback_years] ), gold_battery_simulation[total_capex_eur] > 0, gold_battery_simulation[payback_years] > 0 )","0.0",null);

Output("=====================================================");
Output("PAGE 9 FINAL (SAFE) — measures set: " + n + " | deletes: 0");
Output("Ctrl+S should succeed now. -> Power BI Refresh.");
Output("=====================================================");
