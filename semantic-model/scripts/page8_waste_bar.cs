// =====================================================================
// EnergyLens — PAGE 8 · completing visual: "Estimated Waste by Equipment"
// TE2 → C# Script → (File → Open this file) → F5 → Ctrl+S → PBI Refresh.
// ---------------------------------------------------------------------
// Turns the FDD diagnosis list into a €-ranked action list: which asset is
// wasting the most money / energy → fix that first. Decision-support, not
// just monitoring. Uses existing gold_iot_fdd columns (no new data).
//
// BIND (new horizontal bar in the empty slot):
//   Visual = Clustered bar chart on gold_iot_fdd
//   Y-axis (Category) = gold_iot_fdd[equipment]   (or [equipment_type] for fewer bars)
//   X-axis (Value)    = [IoT Waste Cost EUR]       (primary) — sort DESC
//   Bar color         = conditional → [IoT FDD Priority Color]  (worst = red)
//   Tooltip           = [IoT Waste Energy kWh], [IoT FDD Avg Confidence Pct]
//   Title             = "Estimated Waste by Equipment (€)"
//   (Optional second view: swap X to [IoT Waste Energy kWh] for a kWh ranking.)
// =====================================================================

int n = 0;
string F = "IoT (Page 8)";
System.Action<string,string,string,string> U = (tbl, nm, ex, fmt) => {
    if (!Model.Tables.Any(t => t.Name == tbl)) { Output("SKIP (no table '" + tbl + "'): " + nm); return; }
    var m = Model.AllMeasures.FirstOrDefault(x => x.Name == nm);
    if (m == null) m = Model.Tables[tbl].AddMeasure(nm, ex); else m.Expression = ex;
    if (fmt != null) m.FormatString = fmt;
    m.DisplayFolder = F; n++; Output("ok: " + nm);
};

U("gold_iot_fdd","IoT Waste Cost EUR",@"SUM( gold_iot_fdd[cost_eur_estimate] )","#,##0.00");
U("gold_iot_fdd","IoT Waste Energy kWh",@"SUM( gold_iot_fdd[energy_impact_kwh] )","#,##0.0");

Output("=====================================================");
Output("WASTE BAR measures ready: " + n + ". Bind per header comment.");
Output("Ctrl+S -> Power BI Refresh.");
Output("=====================================================");
