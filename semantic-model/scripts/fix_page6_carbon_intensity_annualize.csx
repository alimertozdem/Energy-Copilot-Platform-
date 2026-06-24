// fix_page6_carbon_intensity_annualize.csx
// Tabular Editor 2 - Advanced Scripting (C# Script tab). NO LINQ.
//
// D1: the "Carbon Intensity vs CRREM Pathway" trend plunges in the current
// INCOMPLETE year (e.g. 2026 = Jan-Apr only) because the measure sums YTD without
// annualizing -> a STRANDED building dips below the pathway in the latest point,
// contradicting its own STRANDED status.
//
// FIX (energy assumption, veto-able): annualize the partial year = monthly average
// x 12 (run-rate). Complete years are unchanged, so the headline KPI card (which
// already picks the most-complete year) is NOT affected -- only the trend's partial
// year is lifted to a full-year-equivalent.
//
// Alternative if you prefer actuals-only: drop the incomplete year via a visual
// filter instead (Desktop) -- then do NOT run this script.
//
// HOW TO RUN: External Tools -> Tabular Editor -> C# Script -> paste -> Run (F5) -> Save -> publish.

string dax =
@"VAR _years = ADDCOLUMNS ( VALUES ( gold_ghg_scope[reporting_year] ), ""@n"", CALCULATE ( COUNTROWS ( gold_ghg_scope ) ) )
VAR _maxN = MAXX ( _years, [@n] )
VAR _yr = MAXX ( FILTER ( _years, [@n] = _maxN ), gold_ghg_scope[reporting_year] )
VAR _s1s2 =
    CALCULATE (
        SUMX ( gold_ghg_scope, gold_ghg_scope[scope1_total_tco2] + gold_ghg_scope[scope2_location_tco2] ),
        gold_ghg_scope[reporting_year] = _yr
    )
VAR _months =
    CALCULATE ( DISTINCTCOUNT ( gold_ghg_scope[reporting_month] ), gold_ghg_scope[reporting_year] = _yr )
VAR _s1s2_annual =
    IF ( _months > 0 && _months < 12, DIVIDE ( _s1s2, _months ) * 12, _s1s2 )
VAR _area = SUMX ( silver_building_master, silver_building_master[conditioned_area_m2] )
RETURN DIVIDE ( _s1s2_annual * 1000, _area )";

int n = 0;
foreach (var m in Model.AllMeasures)
{
    if (m.Name == "Carbon Intensity S1S2 kgCO2 m2 yr")
    {
        m.Expression = dax;
        n++;
    }
}
Info("Carbon Intensity S1S2 annualized: " + n + " (expected 1).");
