// =============================================================================
// FIX ROUND 5 — Solar page consistency  (Tabular Editor 2 C# Script — paste, F5, Save)
// =============================================================================
// Round 4 rescoped "Total Generation" to the selected building's last 12 months
// (86,862 kWh). But its sibling cards still sum ALL history, so they no longer
// agree with generation:
//   * "CO2 Avoided" 84.2 t  (matches the OLD 289k, not the new 86,862)
//   * the self-consumed / exported donut (227k / 63k)
// This creates 3 NEW measures with the SAME building + last-12-months scope so
// every solar card tells one consistent 12-month story. Nothing existing is
// touched (no trend breaks). After running, rebind:
//   * "CO2 Avoided" card        -> [Solar CO2 Avoided tCO2 Rolling 12m]
//   * donut "Solar Self Consumed kWh"  -> [Solar Self Consumed kWh Rolling 12m]
//   * donut "Total Solar Exported kWh" -> [Solar Exported kWh Rolling 12m]
//
// NOTE: the raw data is fine (2023-01 .. 2026-04). The root cause is that the
// date slicer isn't reaching these gold_kpi_daily solar measures (a model-wiring
// thing, like the IoT relationship). This rolling-12m scope is the robust fix and
// needs no data regeneration.
// =============================================================================

var t = Model.Tables.FirstOrDefault(x => x.Name == "gold_kpi_daily");
if (t == null) { Info("ABORT: gold_kpi_daily not found."); return; }

// shared scope preamble reused in each measure
string scope =
@"VAR _maxd = MAXX ( ALL ( gold_kpi_daily ), gold_kpi_daily[date] )
VAR _from = _maxd - 364
VAR _bldgs = VALUES ( silver_building_master[building_id] )
RETURN
CALCULATE (
    {INNER},
    REMOVEFILTERS ( gold_kpi_daily[date] ),
    gold_kpi_daily[date] >= _from && gold_kpi_daily[date] <= _maxd,
    TREATAS ( _bldgs, gold_kpi_daily[building_id] )
)";

System.Action<string,string,string> Make = (name, inner, fmt) => {
    var m = Model.AllMeasures.FirstOrDefault(x => x.Name == name) ?? t.AddMeasure(name);
    m.Expression = scope.Replace("{INNER}", inner);
    m.FormatString = fmt;
    m.DisplayFolder = "Solar";
    Info("Created [" + name + "].");
};

Make("Solar CO2 Avoided tCO2 Rolling 12m",
     "DIVIDE ( SUM ( gold_kpi_daily[co2_savings_from_solar_kg] ), 1000 )", "#,##0.0");
Make("Solar Self Consumed kWh Rolling 12m",
     "SUM ( gold_kpi_daily[solar_self_consumed_kwh] )", "#,##0");
Make("Solar Exported kWh Rolling 12m",
     "SUM ( gold_kpi_daily[solar_exported_kwh] )", "#,##0");

Info("Round 5 done. Rebind the CO2-Avoided card + the self-consumed/exported donut to the new rolling measures.");
