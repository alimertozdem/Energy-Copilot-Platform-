// =============================================================================
// FIX — Page 9: remove obsolete payback caps + make the payback CARD honest.
// Tabular Editor 2 C# script.  Paste -> F5 -> Ctrl+S (F5 alone does NOT save)
// -> Power BI Desktop -> Refresh.
// =============================================================================
// gold_battery_simulation is now physically real (notebook 16): paybacks top out
// ~19 yr, IRR is real, savings are Measured/Modeled/Prospect. The old 25-yr MIN
// caps were lipstick over the fabricated values and are no longer needed.
//
//   C2 Payback Years (CARD): was MINX(...) = the single BEST scenario in the whole
//   portfolio (read 1.5 yr — a cherry-pick). Now = payback of the building's
//   INSTALLED (active / Measured) strategy. Portfolio view averages the installed
//   paybacks. Buildings without a real battery (is_active all False) drop out
//   naturally — exactly right.
//
//   V3 / Scenario payback measures: caps removed (no longer bind).
// =============================================================================

int n = 0;
foreach (var m in Model.AllMeasures)
{
    if (m.Name == "C2 Payback Years")
    {
        // NOTE: keep DAX comments free of '=' (TE paste quirk).
        m.Expression =
@"// Payback of the building's installed (active / Measured) strategy.
// Portfolio view averages the installed paybacks across buildings.
CALCULATE (
    AVERAGE ( gold_battery_simulation[payback_years] ),
    gold_battery_simulation[is_active_strategy] = ""True""
)";
        m.FormatString = "0.0";
        n++; Info("C2 Payback Years -> installed-strategy payback (no MIN cap).");
    }
    else if (m.Name == "V3 Payback Years")
    {
        m.Expression = @"AVERAGE ( gold_battery_simulation[payback_years] )";
        m.FormatString = "0.0";
        n++; Info("V3 Payback Years -> uncapped.");
    }
    else if (m.Name == "V3 Payback Years Clean")
    {
        m.Expression =
@"VAR _p = DIVIDE ( SUM ( gold_battery_simulation[total_capex_eur] ), SUM ( gold_battery_simulation[annual_savings_eur] ) )
RETURN IF ( _p > 0, ROUND ( _p, 1 ), BLANK () )";
        n++; Info("V3 Payback Years Clean -> uncapped.");
    }
    else if (m.Name == "Scenario Payback Years")
    {
        m.Expression =
@"VAR _p = DIVIDE ( SUM ( gold_battery_simulation[total_capex_eur] ), SUM ( gold_battery_simulation[annual_savings_eur] ) )
RETURN IF ( _p > 0, _p, BLANK () )";
        n++; Info("Scenario Payback Years -> uncapped.");
    }
}
Info("Done. Measures updated: " + n + " (expected 4). Ctrl+S, then Refresh.");

// EXPECTED AFTER REFRESH (payback CARD):
//   B001 selected -> 7.9 yr  |  B003 -> 1.7 yr  |  B005 -> 2.6 yr
//   All buildings -> ~4.1 yr (avg of installed)  (was a misleading 1.5)
