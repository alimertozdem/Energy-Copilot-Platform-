// =====================================================================
// EnergyLens — PAGE 9 · clean payback for the CAPEX-vs-Payback scatter
// The live gold_battery_simulation[payback_years] column is stale/uncapped
// (shows values like 500,000 where annual savings ~ 0), which blows up the
// scatter Y-axis. This recomputes payback FRESH from the reliable capex /
// savings columns, capped at 25 yr, BLANK for non-viable scenarios — so the
// scatter only plots real investment candidates and auto-scales 0-25.
// TE2 → C# Script → File → Reload → F5 → Ctrl+S → Refresh.
// Then in the scatter: Y-axis = [V3 Payback Years Clean] (remove the old
// "Average of payback_years"); clear any manual Y-axis Max so it auto-scales.
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

// clean payback = total_capex / annual_savings, viable only (0 < p <= 25 yr)
U("gold_battery_simulation","V3 Payback Years Clean",
@"VAR cap = SUM( gold_battery_simulation[total_capex_eur] ) VAR sav = SUM( gold_battery_simulation[annual_savings_eur] ) VAR p = DIVIDE( cap, sav ) RETURN IF( sav > 0 && p > 0 && p <= 25, ROUND( p, 1 ), BLANK() )",
"0.0", "Page 9 / V3");

// keep the C2 card consistent with the clean figure (best viable payback)
U("gold_battery_simulation","C2 Payback Years",
@"VAR best = MINX( FILTER( gold_battery_simulation, gold_battery_simulation[total_capex_eur] > 0 && gold_battery_simulation[annual_savings_eur] > 0 ), DIVIDE( gold_battery_simulation[total_capex_eur], gold_battery_simulation[annual_savings_eur] ) ) RETURN IF( best > 25, 25, best )",
"0.0", null);

Output("=====================================================");
Output("PAGE 9 — clean payback set: " + n + " | deletes: 0");
Output("Rebind scatter Y to [V3 Payback Years Clean], clear Y-axis Max. Ctrl+S -> Refresh.");
Output("=====================================================");
