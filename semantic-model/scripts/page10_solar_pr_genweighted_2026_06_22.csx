// =============================================================================
// FIX - Page 10 (Solar): make "Avg Solar PR Pct" generation-weighted.
// Tabular Editor 2 C# script. Paste -> F5 -> Ctrl+S (F5 alone does NOT save)
// -> Power BI Desktop -> Refresh.
// =============================================================================
// PROBLEM: the measure was AVERAGE( gold_kpi_daily[avg_solar_pr] ) * 100 -- a flat
// mean across every building-day. Low-sun days and tiny systems counted the same as
// peak-producing days, so the portfolio card read 89.3 while the true production-
// weighted PR was 0.655. The companion text requires a generation-weighted PR.
//
// ROOT (gold, notebook 03, same day): daily avg_solar_pr is now ENERGY-BASIS
// (Sum gen / (kWp x Sum reference-yield)) and clamped at 0.95, so no day exceeds
// physical limits. This measure aggregates those daily PRs weighted by generation.
//
// NOTE: keep DAX comment lines free of the '=' character (TE paste quirk).
// =============================================================================

int n = 0;
foreach (var m in Model.AllMeasures)
{
    if (m.Name == "Avg Solar PR Pct")
    {
        m.Expression =
@"// Generation-weighted Performance Ratio (energy basis).
// Each day's PR is weighted by that day's generation, so small or low-sun
// systems cannot inflate the portfolio figure. Daily PR is already energy-basis
// and clamped at 0.95 in gold. Days with no valid PR (no PV, or low-sun gated)
// drop out of BOTH numerator and denominator so they neither lift nor dilute.
VAR _num =
    SUMX ( gold_kpi_daily, gold_kpi_daily[solar_generated_kwh] * gold_kpi_daily[avg_solar_pr] )
VAR _den =
    SUMX (
        FILTER ( gold_kpi_daily, NOT ISBLANK ( gold_kpi_daily[avg_solar_pr] ) ),
        gold_kpi_daily[solar_generated_kwh]
    )
RETURN
    DIVIDE ( _num, _den ) * 100";
        m.FormatString = "#,##0.0";
        n++; Info("Avg Solar PR Pct -> generation-weighted energy-basis PR.");
    }
}
Info("Done. Measures updated: " + n + " (expected 1). Ctrl+S, then Refresh.");

// EXPECTED AFTER GOLD RE-RUN + REFRESH:
//   PV Performance Ratio chart: every bar <= 95 (no bar above 100). B009/B007 sit
//     near the 0.95 clamp ceiling; B003 (~62) and B006 (~61) fall below the 75
//     watch line -- genuine underperformers, correctly flagged.
//   Avg Performance Ratio card (portfolio): plausible ~0.75-0.85 band, NOT 89.3.
//   Single building selected: that building's generation-weighted PR.
