// =====================================================================
// EnergyLens — PAGE 9 · 24h dispatch chart fix (delete-free, save-safe)
// V6 Charge/Discharge were SUM -> across "All" buildings x strategies x hours
// the totals hit 100,000-300,000 (nonsense axis, bars unreadable). Switch to
// AVERAGE = per-hour kWh, sensible at any slicer level. Pair with a building +
// strategy slicer to isolate one clean dispatch profile.
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
string FV6 = "Battery 24h (V6)";

U("gold_battery_hourly_dispatch","V6 Charge Rate",   @"AVERAGE( gold_battery_hourly_dispatch[charge_kwh] )",   "#,##0.0", FV6);
U("gold_battery_hourly_dispatch","V6 Discharge Rate",@"AVERAGE( gold_battery_hourly_dispatch[discharge_kwh] )","#,##0.0", FV6);
// SoC + price already AVERAGE — keep
U("gold_battery_hourly_dispatch","V6 SoC Pct",       @"AVERAGE( gold_battery_hourly_dispatch[soc_percent] )", "0.0",     FV6);
U("gold_battery_hourly_dispatch","V2 Avg Grid Price EUR kWh",@"AVERAGE( gold_battery_hourly_dispatch[grid_price_eur_mwh] ) / 1000.0","0.000", FV6);

Output("=====================================================");
Output("PAGE 9 24h FIX — measures set: " + n + " | deletes: 0");
Output("Charge/Discharge are now per-hour AVERAGE kWh (axis sane).");
Output("Add a Building slicer + Strategy slicer (strategy_label); pick ONE each for a clean profile.");
Output("If bars are STILL all empty -> charge_kwh/discharge_kwh are 0 in gold_battery_hourly_dispatch; re-run 15_gold_battery_hourly_dispatch.py.");
Output("=====================================================");
