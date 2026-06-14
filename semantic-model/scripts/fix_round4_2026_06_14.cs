// =============================================================================
// FIX ROUND 4 — 2026-06-14  (Tabular Editor 2 C# Script — paste once, F5, Save)
// =============================================================================
// Creates two NEW measures (nothing existing is touched, so no trend/visual can
// break). After running, rebind two fields:
//   * Page 10 "Total Generation" card  -> [Solar Generated kWh Rolling 12m]
//   * Page 9 scenario table "Payback" col -> [Scenario Payback Years]
//
// WHY:
//  (1) Solar 289k: the card binds to [Total Solar Generated kWh] = SUM(...), but
//      the date slider (2025-26) doesn't filter gold_kpi_daily (its solar data is
//      2023-24) and the building filter isn't reaching it -> it sums all buildings,
//      all time. The new measure FORCES the selected building (TREATAS, works with
//      or without a relationship) and the LAST 12 MONTHS of available data. A 120
//      kWp building then reads ~88-114k kWh.
//  (2) Battery Payback table shows 67 / 46.7 because it binds to the raw
//      payback_years column, which is inconsistent with the displayed CAPEX /
//      savings. The new measure recomputes payback = CAPEX / savings, capped at 25,
//      so every row is internally consistent.
// =============================================================================

// (1) Solar — selected building, last 12 months of available data
{
    var t = Model.Tables.FirstOrDefault(x => x.Name == "gold_kpi_daily");
    if (t == null) { Info("gold_kpi_daily not found."); }
    else {
        var name = "Solar Generated kWh Rolling 12m";
        var m = Model.AllMeasures.FirstOrDefault(x => x.Name == name) ?? t.AddMeasure(name);
        m.Expression =
@"VAR _maxd = MAXX ( ALL ( gold_kpi_daily ), gold_kpi_daily[date] )
VAR _from = _maxd - 364
VAR _bldgs = VALUES ( silver_building_master[building_id] )
RETURN
CALCULATE (
    SUM ( gold_kpi_daily[solar_generated_kwh] ),
    REMOVEFILTERS ( gold_kpi_daily[date] ),
    gold_kpi_daily[date] >= _from && gold_kpi_daily[date] <= _maxd,
    TREATAS ( _bldgs, gold_kpi_daily[building_id] )
)";
        m.FormatString = "#,##0 \"kWh\"";
        m.DisplayFolder = "Solar";
        Info("Created [Solar Generated kWh Rolling 12m].");
    }
}

// (2) Battery — consistent, capped payback for the scenario table
{
    var t = Model.Tables.FirstOrDefault(x => x.Name == "gold_battery_simulation");
    if (t == null) { Info("gold_battery_simulation not found."); }
    else {
        var name = "Scenario Payback Years";
        var m = Model.AllMeasures.FirstOrDefault(x => x.Name == name) ?? t.AddMeasure(name);
        m.Expression =
@"VAR _p = DIVIDE ( SUM ( gold_battery_simulation[total_capex_eur] ),
                  SUM ( gold_battery_simulation[annual_savings_eur] ) )
RETURN IF ( _p <= 0, BLANK (), MIN ( _p, 25 ) )";
        m.FormatString = "0.0";
        m.DisplayFolder = "Battery";
        Info("Created [Scenario Payback Years].");
    }
}

Info("Round 4 done. Rebind: Solar card -> [Solar Generated kWh Rolling 12m]; battery table Payback -> [Scenario Payback Years].");
