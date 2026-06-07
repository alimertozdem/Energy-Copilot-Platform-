// =====================================================================
// EnergyLens — PAGE 9 · value-add measures (save-safe: NO calc table, NO deletes)
// All measures for the 24h dispatch chart + the arbitrage waterfall, in one go.
// TE2 → C# Script → File → Reload → F5 → Ctrl+S → Refresh.
// The waterfall's 2-row step table is created by YOU in Power BI (Home → Enter
// data) — TE2 calculated tables fail to save on a live DirectLake model.
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

// ── 24h dispatch chart (gold_battery_hourly_dispatch) — re-assert + price ──
string FV6 = "Battery 24h (V6)";
U("gold_battery_hourly_dispatch","V6 Charge Rate",   @"SUM( gold_battery_hourly_dispatch[charge_kwh] )",        "#,##0.0", FV6);
U("gold_battery_hourly_dispatch","V6 Discharge Rate",@"SUM( gold_battery_hourly_dispatch[discharge_kwh] )",     "#,##0.0", FV6);
U("gold_battery_hourly_dispatch","V6 SoC Pct",       @"AVERAGE( gold_battery_hourly_dispatch[soc_percent] )",   "0.0",     FV6);
U("gold_battery_hourly_dispatch","V6 Price Index",   @"AVERAGE( gold_battery_hourly_dispatch[grid_price_index] )","0.00",  FV6);
U("gold_battery_hourly_dispatch","V2 Avg Grid Price EUR kWh",@"AVERAGE( gold_battery_hourly_dispatch[grid_price_eur_mwh] ) / 1000.0","0.000", FV6);

// ── arbitrage components (gold_battery_dispatch) ──────────────────────────
string FW = "Arbitrage (V8)";
U("gold_battery_dispatch","Charging Cost EUR",    @"SUM( gold_battery_dispatch[grid_charge_cost_eur] )","#,##0", FW);
U("gold_battery_dispatch","Discharge Benefit EUR",@"SUM( gold_battery_dispatch[cost_avoided_eur] )",    "#,##0", FW);
U("gold_battery_dispatch","Net Arbitrage EUR",    @"[Discharge Benefit EUR] - [Charging Cost EUR]",     "#,##0", FW);

// ── waterfall value — only if you created the 'Arbitrage Steps' table ─────
if (Model.Tables.Any(t => t.Name == "Arbitrage Steps")) {
    U("Arbitrage Steps","Arbitrage Value",
@"SWITCH( SELECTEDVALUE( 'Arbitrage Steps'[Step] ), ""Charging Cost"", -1 * [Charging Cost EUR], ""Discharge Benefit"", [Discharge Benefit EUR], BLANK() )","#,##0", FW);
} else {
    Output("NOTE: 'Arbitrage Steps' table not found. Create it in Power BI (Home -> Enter data):");
    Output("  table name: Arbitrage Steps | columns: Step (text), Sort (whole number)");
    Output("  rows: Charging Cost / 1   and   Discharge Benefit / 2");
    Output("  Then re-run this script to add [Arbitrage Value].");
}

Output("=====================================================");
Output("PAGE 9 VALUE-ADDS — measures set: " + n + " | deletes: 0 | calc tables: 0");
Output("If V6 Charge/Discharge are still EMPTY after refresh -> gold_battery_hourly_dispatch has no data; re-run notebooks/simulation/15_gold_battery_hourly_dispatch.py.");
Output("=====================================================");
