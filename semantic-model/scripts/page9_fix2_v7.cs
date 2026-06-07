// =====================================================================
// EnergyLens — PAGE 9 · STAGE 2: V7 System Health measures (real SoH)
// RUN ORDER: (1) re-run notebooks/simulation/12_battery_dispatch_and_simulation.py
//   in Fabric  ->  (2) DirectLake Refresh  ->  (3) THEN this script (F5 -> Ctrl+S).
// The script GUARDS on the new columns — if you run it before the re-run it just
// prints a reminder instead of creating broken measures.
// ---------------------------------------------------------------------
// New gold_battery_dispatch columns (from the notebook edit): battery_health_percent,
// cumulative_cycles, annual_cycles, years_until_replacement, install_date.
// SoH = 100 - cycle_fade - calendar_fade ; end-of-life = 80% SoH.  [Mert-approved]
// =====================================================================

string F = "Battery Health (V7)";
var disp = Model.Tables.FirstOrDefault(t => t.Name == "gold_battery_dispatch");
if (disp == null) { Output("STOP: gold_battery_dispatch not in model."); return; }
if (!disp.Columns.Any(c => c.Name == "battery_health_percent")) {
    Output("WAIT: 'battery_health_percent' not found yet.");
    Output("  -> Re-run notebook 12 in Fabric, DirectLake Refresh, then run this script again.");
    return;
}

int n = 0;
System.Action<string,string,string,string> U = (tbl, nm, ex, fmt) => {
    var m = Model.AllMeasures.FirstOrDefault(x => x.Name == nm);
    if (m == null) m = Model.Tables[tbl].AddMeasure(nm, ex); else m.Expression = ex;
    if (fmt != null) m.FormatString = fmt;
    m.DisplayFolder = F; n++; Output("ok: " + nm);
};

// Current State of Health (%) — fleet/selected battery average
U("gold_battery_dispatch","V7 Current SoH Pct",@"AVERAGE( gold_battery_dispatch[battery_health_percent] )","0.0");
// Cycles used vs warranty (cumulative / warranty_cycles)
U("gold_battery_dispatch","V7 Cycles Used Pct",@"VAR bt=SELECTEDVALUE(gold_battery_dispatch[battery_type]) VAR w=LOOKUPVALUE(gold_battery_technologies[warranty_cycles], gold_battery_technologies[battery_type], bt) VAR c=AVERAGE(gold_battery_dispatch[cumulative_cycles]) RETURN IF( ISBLANK(w) || w=0, BLANK(), DIVIDE(c, w) )","0.0%");
// Years until 80% SoH at the observed fade rate
U("gold_battery_dispatch","V7 Years Until Replacement",@"AVERAGE( gold_battery_dispatch[years_until_replacement] )","0.0");
// Annual equivalent full cycles (usage intensity)
U("gold_battery_dispatch","V7 Annual Cycles",@"AVERAGE( gold_battery_dispatch[annual_cycles] )","#,##0");
// SoH color for the panel (>=90 green / >=80 amber / <80 red)
U("gold_battery_dispatch","V7 SoH Color",@"VAR s=[V7 Current SoH Pct] RETURN SWITCH( TRUE(), ISBLANK(s),""#AAAAAA"", s>=90,""#2ECC40"", s>=80,""#FF851B"", ""#FF4136"" )",null);

Output("=====================================================");
Output("PAGE 9 V7 measures updated: " + n);
Output("Panel: SoH% (color [V7 SoH Color]) | Cycles Used % | Years Until Replacement | Annual Cycles.");
Output("Ctrl+S -> Refresh.");
Output("=====================================================");
