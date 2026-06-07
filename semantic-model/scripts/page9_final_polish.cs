// =====================================================================
// EnergyLens — PAGE 9 · FINAL POLISH (delete-free, save-safe)
// Fixes the last 3 measure issues after page9_final_safe.cs:
//   1. I2 Chemistry Recommendation Text — was a calc error -> robust rewrite
//      (country-rule based; a building has several chemistries across strategies,
//       so it does NOT depend on a single battery_type).
//   2. I3 Compliance Flag Text — robust rewrite (country chemistry rules).
//   3. V7 Warranty Cycles — average across the battery types in context, so
//      V7 Cycles Used % and Years populate even with "All" buildings selected.
// TE2 → C# Script → (File → Open) → File → Reload → F5 → Ctrl+S → Refresh.
// Verified against semantic-model/_probe_output.txt.
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
string FI = "Insights (I)";

// 1. I2 — Chemistry recommendation (country-rule based, robust)
U("gold_country_regulations","I2 Chemistry Recommendation Text",
@"VAR ctry = SELECTEDVALUE( gold_country_regulations[country_name] ) VAR nmcOk = SELECTEDVALUE( gold_country_regulations[nmc_allowed_new_2025] ) RETURN IF( ISBLANK(ctry), ""Select a single building for a chemistry recommendation."", ""Recommended: LFP — EU 2023/1542 compliant, best cost / safety / cycle-life for "" & ctry & ""."" & IF( nmcOk = FALSE(), "" Avoid NMC: restricted for new installs in "" & ctry & "" (2025)."", """" ) )",
null, FI);

// 2. I3 — Compliance flag (country chemistry rules, robust)
U("gold_country_regulations","I3 Compliance Flag Text",
@"VAR ctry = SELECTEDVALUE( gold_country_regulations[country_name] ) VAR lfpOk = SELECTEDVALUE( gold_country_regulations[lfp_allowed] ) VAR nmcOk = SELECTEDVALUE( gold_country_regulations[nmc_allowed_new_2025] ) RETURN IF( ISBLANK(ctry), ""Select a single building to check compliance."", ""EU 2023/1542 in "" & ctry & "": LFP "" & IF( lfpOk = TRUE(), ""approved"", ""restricted"" ) & "", NMC (new installs 2025) "" & IF( nmcOk = TRUE(), ""approved"", ""restricted"" ) & ""."" )",
null, FI);

// 3. V7 Warranty Cycles — average across battery types in context (populates with "All")
U("gold_battery_dispatch","V7 Warranty Cycles",
@"AVERAGEX( VALUES( gold_battery_dispatch[battery_type] ), LOOKUPVALUE( gold_battery_technologies[warranty_cycles], gold_battery_technologies[battery_type], gold_battery_dispatch[battery_type] ) )",
"#,##0", "Battery Health (V7)");

Output("=====================================================");
Output("PAGE 9 FINAL POLISH — measures set: " + n + " | deletes: 0");
Output("Ctrl+S -> Refresh. I2/I3 cards render; V7 Cycles Used % + Years populate.");
Output("=====================================================");
