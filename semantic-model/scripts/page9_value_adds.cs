// =====================================================================
// EnergyLens — PAGE 9 · value-add visuals (24h price overlay + arbitrage waterfall)
// Replaces the troublesome CAPEX scatter with high-value, robust visuals.
// TE2 → C# Script → File → Reload → F5 → Ctrl+S → Refresh.
// ---------------------------------------------------------------------
//   LEFT  (rebuild 24h dispatch): adds the Avg Grid Price line so the chart
//          shows charge-low / discharge-high arbitrage. Slice by strategy_label.
//   RIGHT (NEW waterfall): Charging Cost -> Discharge Benefit -> Net Arbitrage.
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

// LEFT — avg grid price in EUR/kWh for the 24h dispatch overlay line
U("gold_battery_hourly_dispatch","V2 Avg Grid Price EUR kWh",
@"AVERAGE( gold_battery_hourly_dispatch[grid_price_eur_mwh] ) / 1000.0","0.000","Battery 24h (V6)");

// RIGHT — arbitrage components (annual, from gold_battery_dispatch)
string FW = "Arbitrage (V8)";
U("gold_battery_dispatch","Charging Cost EUR",   @"SUM( gold_battery_dispatch[grid_charge_cost_eur] )","#,##0","" + FW);
U("gold_battery_dispatch","Discharge Benefit EUR",@"SUM( gold_battery_dispatch[cost_avoided_eur] )","#,##0","" + FW);
U("gold_battery_dispatch","Net Arbitrage EUR",   @"[Discharge Benefit EUR] - [Charging Cost EUR]","#,##0","" + FW);

// waterfall step dimension (disconnected calculated table)
if (!Model.Tables.Any(t => t.Name == "Arbitrage Steps")) {
    var ct = Model.AddCalculatedTable("Arbitrage Steps",
        "DATATABLE( \"Step\", STRING, \"Sort\", INTEGER, { { \"Charging Cost\", 1 }, { \"Discharge Benefit\", 2 } } )");
    Output("created calculated table: Arbitrage Steps");
}
var steps = Model.Tables.FirstOrDefault(t => t.Name == "Arbitrage Steps");
if (steps != null && steps.Columns.Any(c => c.Name == "Step") && steps.Columns.Any(c => c.Name == "Sort"))
    steps.Columns["Step"].SortByColumn = steps.Columns["Sort"];

// waterfall value: cost steps down, benefit steps up; running total = Net Arbitrage
U("Arbitrage Steps","Arbitrage Value",
@"SWITCH( SELECTEDVALUE( 'Arbitrage Steps'[Step] ), ""Charging Cost"", -1 * [Charging Cost EUR], ""Discharge Benefit"", [Discharge Benefit EUR], BLANK() )","#,##0",FW);

Output("=====================================================");
Output("PAGE 9 VALUE-ADDS — measures set: " + n);
Output("LEFT: add line [V2 Avg Grid Price EUR kWh] + strategy_label slicer.");
Output("RIGHT: Waterfall — Category 'Arbitrage Steps'[Step], Y [Arbitrage Value], Total ON.");
Output("Ctrl+S -> Refresh.");
Output("=====================================================");
