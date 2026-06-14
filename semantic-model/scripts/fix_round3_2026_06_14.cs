// =============================================================================
// FIX ROUND 3 — 2026-06-14  (Tabular Editor 2 C# Script — paste once, F5, Save, Refresh)
// =============================================================================
//  (1) Page 9 broken visual: "C1 Annual Savings EUR" compares a TEXT column
//      (gold_battery_simulation[is_active_strategy], stored "True"/"False" for
//      Direct Lake) to the BOOLEAN TRUE() -> "DAX comparison ... True/False" crash.
//      Fix: compare to the string "True". (Surfaced after you re-ran notebook 14.)
//  (2) Page 10 Solar "Total Generation 289K": the KPI used CALCULATE(SUM(...),
//      ALLSELECTED()) which drops the building + date filter, so it sums all
//      buildings / all history. Rescoped to the SELECTED building's most recent
//      12 months of available solar data (date filter relaxed because the solar
//      data sits in 2023-24 while the page slider is 2025-26 — a data-freshness
//      gap to look at separately). A 120 kWp building should now read ~90-120k kWh.
// =============================================================================

// ---- (1) C1 Annual Savings EUR : TEXT bool compare ----
{
    var m = Model.AllMeasures.FirstOrDefault(x => x.Name == "C1 Annual Savings EUR");
    if (m == null) { Info("C1 Annual Savings EUR not found."); }
    else {
        m.Expression =
@"VAR _has_active =
    NOT ISBLANK ( CALCULATE ( COUNTROWS ( gold_battery_dispatch ),
        gold_battery_dispatch[is_simulated] = FALSE() ) )
VAR _annual_savings =
    CALCULATE (
        SUM ( gold_battery_dispatch[net_savings_eur] ),
        gold_battery_dispatch[is_simulated] = FALSE(),
        gold_battery_dispatch[date] >= DATE ( YEAR ( TODAY() ) - 1, MONTH ( TODAY() ), DAY ( TODAY() ) )
    )
VAR _fallback_sim =
    CALCULATE (
        AVERAGE ( gold_battery_simulation[annual_savings_eur] ),
        gold_battery_simulation[is_active_strategy] = ""True""   -- TEXT column, not TRUE()
    )
RETURN
    IF ( _has_active && NOT ISBLANK ( _annual_savings ) && _annual_savings > 0,
        _annual_savings, _fallback_sim )";
        Info("Fixed C1 Annual Savings EUR (text-bool compare).");
    }
}

// ---- (2) Total Solar Generated kWh KPI : rescope ----
{
    var m = Model.AllMeasures.FirstOrDefault(x => x.Name == "Total Solar Generated kWh KPI");
    if (m == null) { Info("Total Solar Generated kWh KPI not found."); }
    else {
        m.Expression =
@"VAR _maxd = CALCULATE ( MAX ( gold_kpi_daily[date] ), ALLSELECTED ( gold_kpi_daily[date] ) )
VAR _from = _maxd - 364
RETURN
CALCULATE (
    SUM ( gold_kpi_daily[solar_generated_kwh] ),
    ALLSELECTED ( gold_kpi_daily[date] ),
    gold_kpi_daily[date] >= _from && gold_kpi_daily[date] <= _maxd
)";
        m.FormatString = "#,##0";
        Info("Rescoped Total Solar Generated kWh KPI to the building's last 12 months.");
    }
}

Info("Round 3 done.");
