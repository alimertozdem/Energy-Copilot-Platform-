// =====================================================================
// EnergyLens — PAGE 9 · FINAL POLISH v2 (delete-free, save-safe)
// Fixes two things from polish v1:
//   1. V7 Warranty Cycles -> "multiple values" error: gold_battery_technologies
//      has several products per battery_type, so LOOKUPVALUE returned many rows.
//      Switch to CALCULATE(AVERAGE(...)) per type -> single value, no error.
//   2. I2/I3 cards didn't react to the building slicer: they read the country from
//      gold_country_regulations (which the building slicer doesn't filter). Now they
//      read the SELECTED building's silver_building_master[country_code] (slicer DOES
//      filter that), then LOOKUPVALUE the regulation -> building-aware.
// TE2 → C# Script → File → Reload → F5 → Ctrl+S → Refresh.
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

// 1. V7 Warranty Cycles — average across products of each battery_type in context
U("gold_battery_dispatch","V7 Warranty Cycles",
@"AVERAGEX( VALUES( gold_battery_dispatch[battery_type] ), VAR _bt = gold_battery_dispatch[battery_type] RETURN CALCULATE( AVERAGE( gold_battery_technologies[warranty_cycles] ), gold_battery_technologies[battery_type] = _bt ) )",
"#,##0", "Battery Health (V7)");

// 2. I2 — Chemistry recommendation (building-aware via silver_building_master[country_code])
U("gold_country_regulations","I2 Chemistry Recommendation Text",
@"VAR cc = SELECTEDVALUE( silver_building_master[country_code] ) VAR ctry = LOOKUPVALUE( gold_country_regulations[country_name], gold_country_regulations[country_code], cc ) VAR nmcOk = LOOKUPVALUE( gold_country_regulations[nmc_allowed_new_2025], gold_country_regulations[country_code], cc ) RETURN IF( ISBLANK(cc), ""Select a single building for a chemistry recommendation."", ""Recommended: LFP — EU 2023/1542 compliant, best cost / safety / cycle-life for "" & ctry & ""."" & IF( nmcOk = FALSE(), "" Avoid NMC: restricted for new installs in "" & ctry & "" (2025)."", """" ) )",
null, FI);

// 3. I3 — Compliance flag (building-aware)
U("gold_country_regulations","I3 Compliance Flag Text",
@"VAR cc = SELECTEDVALUE( silver_building_master[country_code] ) VAR ctry = LOOKUPVALUE( gold_country_regulations[country_name], gold_country_regulations[country_code], cc ) VAR lfpOk = LOOKUPVALUE( gold_country_regulations[lfp_allowed], gold_country_regulations[country_code], cc ) VAR nmcOk = LOOKUPVALUE( gold_country_regulations[nmc_allowed_new_2025], gold_country_regulations[country_code], cc ) RETURN IF( ISBLANK(cc), ""Select a single building to check compliance."", ""EU 2023/1542 in "" & ctry & "": LFP "" & IF( lfpOk = TRUE(), ""approved"", ""restricted"" ) & "", NMC (new installs 2025) "" & IF( nmcOk = TRUE(), ""approved"", ""restricted"" ) & ""."" )",
null, FI);

Output("=====================================================");
Output("PAGE 9 POLISH v2 — measures set: " + n + " | deletes: 0");
Output("Ctrl+S -> Refresh. V7 Warranty error gone; I2/I3 now follow the building slicer.");
Output("=====================================================");
