// =====================================================================
// EnergyLens — PAGE 8 POLISH PATCH (run after page8_final_install.cs)
// Tabular Editor 2 → C# Script → (File → Open this file) → F5 → Ctrl+S → PBI Refresh.
// Measure NAMES are unchanged → no visual rebinding needed.
// ---------------------------------------------------------------------
// FIX 1 — "Today" cards were blank / C4 stuck on "All Clear":
//   the sim data ends ~2026-06-01, so event_date = TODAY() matched no rows.
//   → switch the 4 day-scoped FDD measures to the LATEST day present in the
//     data (respects the building slicer). When the pipeline runs daily,
//     "latest day" == today automatically.
// FIX 2 — FDD Findings table showed many "--":
//   row helpers used SELECTEDVALUE(), which is blank when an Equipment+Fault
//   group spans >1 underlying row → switch to MAX / AVERAGE / SUM so every
//   row resolves (worst priority, avg confidence, total cost for the group).
// =====================================================================

int updated = 0;
string F = "IoT (Page 8)";
System.Action<string,string,string,string> U = (tbl, nm, ex, fmt) => {
    var m = Model.AllMeasures.FirstOrDefault(x => x.Name == nm);
    if (m == null) { Output("NOTE (not found, creating): " + nm); if(!Model.Tables.Any(t=>t.Name==tbl)){Output("  SKIP no table "+tbl);return;} m = Model.Tables[tbl].AddMeasure(nm, ex); }
    else m.Expression = ex;
    if (fmt != null) m.FormatString = fmt;
    m.DisplayFolder = F; updated++; Output("ok: " + nm);
};

// ── FIX 1 — latest-day instead of TODAY() (cards + C4) ───────────────
U("gold_iot_fdd","IoT FDD Diagnoses Today",@"VAR d=MAX(gold_iot_fdd[event_date]) RETURN CALCULATE( COUNTROWS(gold_iot_fdd), gold_iot_fdd[event_date]=d )","#,##0");
U("gold_iot_fdd","IoT FDD High Today",@"VAR d=MAX(gold_iot_fdd[event_date]) RETURN CALCULATE( COUNTROWS(gold_iot_fdd), gold_iot_fdd[severity]=""High"", gold_iot_fdd[event_date]=d )","#,##0");
U("gold_iot_fdd","IoT FDD Cost Today EUR",@"VAR d=MAX(gold_iot_fdd[event_date]) RETURN CALCULATE( SUM(gold_iot_fdd[cost_eur_estimate]), gold_iot_fdd[event_date]=d )","#,##0.00");
U("gold_iot_fdd","IoT FDD Energy Impact kWh Today",@"VAR d=MAX(gold_iot_fdd[event_date]) RETURN CALCULATE( SUM(gold_iot_fdd[energy_impact_kwh]), gold_iot_fdd[event_date]=d )","#,##0.0");
// C4 Label/Color auto-fix: they read [IoT FDD High Today] + [IoT FDD Cost Today EUR].

// ── FIX 2 — FDD table row helpers: aggregate, never blank ────────────
U("gold_iot_fdd","IoT FDD Priority Band",@"VAR p=MAX(gold_iot_fdd[priority_score]) RETURN SWITCH( TRUE(), ISBLANK(p),""--"", p>=60,""Urgent"", p>=35,""High"", p>=20,""Medium"", ""Low"" )",null);
U("gold_iot_fdd","IoT FDD Priority Color",@"VAR p=MAX(gold_iot_fdd[priority_score]) RETURN SWITCH( TRUE(), ISBLANK(p),""#AAAAAA"", p>=60,""#FF4136"", p>=35,""#FF851B"", p>=20,""#FFDC00"", ""#2ECC40"" )",null);
U("gold_iot_fdd","IoT FDD Row Confidence",@"VAR c=AVERAGE(gold_iot_fdd[confidence]) RETURN IF( ISBLANK(c), ""--"", FORMAT(c,""0%"") )",null);
U("gold_iot_fdd","IoT FDD Row Cost Label",@"VAR c=SUM(gold_iot_fdd[cost_eur_estimate]) RETURN IF( ISBLANK(c) || c=0, ""--"", ""Est. EUR "" & FORMAT(c,""0.00"") )",null);

// ── Optional: numeric sort key for the V5 table (sort worst-first) ───
U("gold_iot_fdd","IoT FDD Priority Sort",@"MAX(gold_iot_fdd[priority_score])","0");

Output("=====================================================");
Output("PAGE 8 POLISH DONE — measures updated: " + updated);
Output("Ctrl+S -> Power BI Refresh. No rebinding needed (names unchanged).");
Output("=====================================================");
