// =============================================================================
// FIX — Page 9 "Battery Arbitrage Breakdown (Annual)" was NOT annual.
// Tabular Editor 2 C# script.  Paste -> F5 -> Ctrl+S (F5 alone does NOT save)
// -> Power BI Desktop -> Refresh.
// =============================================================================
// VERIFIED against live Fabric (2026-06-22):
//   The three arbitrage measures SUM the entire dispatch history
//   (2023-01-01 .. 2026-04-18 = 1204 days ~= 3.3 years) with no annualization,
//   yet the panel title says "(Annual)".
//     Discharge Benefit 272,042  |  Charging Cost 69,965  |  Net 202,076   <- 3.3-yr cumulative
//   True annual (divide by 3.296 yr):
//     Discharge ~82,540  |  Charging ~21,230  |  Net ~61,310
//
// This redefines the two component measures to divide the real (is_simulated=FALSE)
// sum by the actual span (in years) within the current filter context. "Net
// Arbitrage EUR" = [Discharge Benefit EUR] - [Charging Cost EUR] inherits the fix.
// Per-building selection annualizes by that building's own span automatically.
// =============================================================================

string annualCharging =
@"VAR _d =
    CALCULATE (
        DATEDIFF ( MIN ( gold_battery_dispatch[date] ), MAX ( gold_battery_dispatch[date] ), DAY ) + 1,
        gold_battery_dispatch[is_simulated] = FALSE ()
    )
VAR _y = DIVIDE ( _d, 365.25 )
RETURN
    DIVIDE (
        CALCULATE ( SUM ( gold_battery_dispatch[grid_charge_cost_eur] ), gold_battery_dispatch[is_simulated] = FALSE () ),
        _y
    )";

string annualDischarge =
@"VAR _d =
    CALCULATE (
        DATEDIFF ( MIN ( gold_battery_dispatch[date] ), MAX ( gold_battery_dispatch[date] ), DAY ) + 1,
        gold_battery_dispatch[is_simulated] = FALSE ()
    )
VAR _y = DIVIDE ( _d, 365.25 )
RETURN
    DIVIDE (
        CALCULATE ( SUM ( gold_battery_dispatch[cost_avoided_eur] ), gold_battery_dispatch[is_simulated] = FALSE () ),
        _y
    )";

int n = 0;
foreach (var m in Model.AllMeasures)
{
    if (m.Name == "Charging Cost EUR")    { m.Expression = annualCharging;  n++; Info("Annualized: Charging Cost EUR"); }
    if (m.Name == "Discharge Benefit EUR"){ m.Expression = annualDischarge; n++; Info("Annualized: Discharge Benefit EUR"); }
}
Info("Done. Measures annualized: " + n + " (expected 2). 'Net Arbitrage EUR' inherits the fix automatically.");

// AFTER RUNNING: Ctrl+S, then Refresh. Panel should read ~61k Net (not 202k).
// The title "(Annual)" is now truthful; no need to rename it.
