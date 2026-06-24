// =============================================================================
// BUILD - Page 10 (Solar): real "PV Underperformance - Est. Annual Loss" table.
// Replaces the mis-sourced "PV Faults" table (which was pulling gold_iot_fdd
// HVAC/IoT equipment faults -- Page 8 content -- with a non-building-scoped
// "Score"). Tabular Editor 2 C# script. Paste -> F5 -> Ctrl+S -> PBI refresh.
// =============================================================================
// ENERGY LOGIC (assumption-stated):
//   Target PR 0.80 (mid of the healthy 0.75-0.85 band). A building below target
//   loses generation it could have produced. Lost annual generation equals
//   annual generation times (target over actual minus 1). Buildings at or above
//   target return blank (no loss). The euro value uses the building's OWN
//   effective solar tariff (platform savings per self-consumed kWh) -- no
//   hardcoded price. Figures are estimates and rest on synthetic generation.
//
//   NOTE: keep DAX comment lines free of the '=' character (TE paste quirk).
// =============================================================================

int created = 0, updated = 0;
Table tbl = Model.Tables["gold_kpi_daily"];

// ---- Measure 1: lost generation kWh (annual, estimate) ----
string n1 = "PV Underperf Lost Gen kWh (Est)";
Measure m1 = null;
foreach (var m in Model.AllMeasures) { if (m.Name == n1) { m1 = m; break; } }
if (m1 == null) { m1 = tbl.AddMeasure(n1); created++; } else { updated++; }
m1.Expression =
@"// Annual generation a building would gain at the healthy target PR.
// Target PR 0.80. Buildings at or above target return blank. Self-annualizing
// via solar-day count so the date slicer does not distort the yearly figure.
VAR _prTarget = 0.80
VAR _pr = DIVIDE ( [Avg Solar PR Pct], 100 )
VAR _days = CALCULATE ( DISTINCTCOUNT ( gold_kpi_daily[date] ), gold_kpi_daily[solar_generated_kwh] > 0 )
VAR _years = DIVIDE ( _days, 365.0 )
VAR _genAnnual = DIVIDE ( [Total Solar Generated kWh], _years )
VAR _uplift = MAX ( 0, DIVIDE ( _prTarget - _pr, _pr ) )
RETURN IF ( _pr > 0 && _uplift > 0, _genAnnual * _uplift, BLANK () )";
m1.FormatString = "#,##0";
m1.DisplayFolder = "Solar - Realtime & Opportunity";

// ---- Measure 2: euro loss (annual, estimate) ----
string n2 = "PV Underperf Loss EUR (Est)";
Measure m2 = null;
foreach (var m in Model.AllMeasures) { if (m.Name == n2) { m2 = m; break; } }
if (m2 == null) { m2 = tbl.AddMeasure(n2); created++; } else { updated++; }
m2.Expression =
@"// Value of the lost generation at the building's own effective solar tariff
// (platform savings per self-consumed kWh). Per-building, no hardcoded price.
VAR _lostKwh = [PV Underperf Lost Gen kWh (Est)]
VAR _tariff = DIVIDE ( SUM ( gold_kpi_daily[estimated_savings_eur] ), SUM ( gold_kpi_daily[solar_self_consumed_kwh] ) )
RETURN IF ( NOT ISBLANK ( _lostKwh ) && _lostKwh > 0, _lostKwh * _tariff, BLANK () )";
m2.FormatString = "#,##0";
m2.DisplayFolder = "Solar - Realtime & Opportunity";

Info("Done. created=" + created + " updated=" + updated + " (expected 2 total). Ctrl+S, then Refresh.");

// EXPECTED (table, underperformers only, Loss EUR desc):
//   B003  PR 55.2  ~147,580 kWh  ~33,353 EUR/yr
//   B006  PR 58.6  ~ 35,279 kWh  ~ 7,232 EUR/yr
//   B005  PR 66.8  ~ 30,115 kWh  ~ 6,806 EUR/yr
//   B001  PR 64.0  ~ 22,014 kWh  ~ 4,975 EUR/yr
//   B004  PR 73.3  ~  6,283 kWh  ~ 1,194 EUR/yr
//   B007 / B009 / B010 (PR >= 80) -> blank (drop out of the table)
