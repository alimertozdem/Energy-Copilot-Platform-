// =====================================================================
// EnergyLens — PAGE 8 · annualized waste run-rate (credible €/yr story)
// TE2 → C# Script → (File → Open) → F5 → Ctrl+S → PBI Refresh.
// ---------------------------------------------------------------------
// The raw waste measures are a few-DAY window total (cost = power_waste_kw ×
// occurrence × interval × grid_price over the rolling window) → looks tiny.
// These annualize the run-rate so the bar reads as "fix this → save €X/yr",
// which is the decision-support framing buyers expect. Labelled an ESTIMATE.
//
// NOTE: these are only meaningful once the whole window is populated — re-run
// notebooks/iot/11b_iot_processing.py → 11c_iot_fdd.py first, so older
// partitions carry the new cost/priority/confidence columns (not NULL).
//
// BIND: swap the waste bar's X-axis to [IoT Waste Cost EUR Annual Est].
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

// Annual run-rate = (avg daily window cost) × 365, over the days present in context.
U("gold_iot_fdd","IoT Waste Cost EUR Annual Est",@"VAR d=CALCULATE( DISTINCTCOUNT(gold_iot_fdd[event_date]) ) VAR w=SUM(gold_iot_fdd[cost_eur_estimate]) RETURN ROUND( DIVIDE(w,d) * 365, 0 )","#,##0");
U("gold_iot_fdd","IoT Waste Energy kWh Annual Est",@"VAR d=CALCULATE( DISTINCTCOUNT(gold_iot_fdd[event_date]) ) VAR w=SUM(gold_iot_fdd[energy_impact_kwh]) RETURN ROUND( DIVIDE(w,d) * 365, 0 )","#,##0");

Output("=====================================================");
Output("ANNUAL WASTE measures ready: " + n + ". Use [IoT Waste Cost EUR Annual Est] on the bar.");
Output("Re-run 11b -> 11c first so the whole window is populated (no NULL days).");
Output("=====================================================");
