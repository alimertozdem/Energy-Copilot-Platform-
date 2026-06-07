// =====================================================================
// EnergyLens — PAGE 8 · FDD Findings table conditional-formatting measures
// TE2 → C# Script → (File → Open) → F5 → Ctrl+S → PBI Refresh.
// ---------------------------------------------------------------------
// Adds row-level color measures so the table reads at a glance instead of
// looking monotone. Dark-theme friendly (these drive FONT color).
//   Severity column  → [IoT FDD Severity Color]
//   Priority column  → [IoT FDD Priority Color]   (already exists)
//   Est. cost column → built-in Data bars (no measure) OR [IoT FDD Cost Heat]
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

// Severity → font color (High red / Medium amber / Low green) on the dark theme.
U("gold_iot_fdd","IoT FDD Severity Color",@"VAR s=MAX(gold_iot_fdd[severity]) RETURN SWITCH( TRUE(), s=""High"",""#FF4136"", s=""Medium"",""#FF851B"", s=""Low"",""#2ECC40"", ""#AAAAAA"" )",null);

// Est. cost → font heat (worst cost rows pop). Thresholds in € per row group.
U("gold_iot_fdd","IoT FDD Cost Heat",@"VAR c=SUM(gold_iot_fdd[cost_eur_estimate]) RETURN SWITCH( TRUE(), ISBLANK(c) || c=0,""#777777"", c>=20,""#FF4136"", c>=8,""#FF851B"", ""#2ECC40"" )",null);

// Confidence → font color (high confidence = stronger green, low = muted).
U("gold_iot_fdd","IoT FDD Confidence Color",@"VAR c=AVERAGE(gold_iot_fdd[confidence]) RETURN SWITCH( TRUE(), ISBLANK(c),""#AAAAAA"", c>=0.8,""#2ECC40"", c>=0.5,""#FFDC00"", ""#FF851B"" )",null);

Output("=====================================================");
Output("FDD table format measures ready: " + n + " (+ existing [IoT FDD Priority Color]).");
Output("Apply per the steps I gave: Cell elements -> Font color -> fx -> Field value.");
Output("=====================================================");
