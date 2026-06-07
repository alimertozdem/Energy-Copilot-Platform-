// =====================================================================
// EnergyLens — PAGE 10 (SOLAR) FINAL measure loader
// Run ONCE in Tabular Editor 2 (C# Script tab -> F5), then Ctrl+S, then
// Power BI Desktop: Home -> Refresh (or Model -> Refresh).
// =====================================================================
// SAFE FOR LIVE DIRECTLAKE: pure create-or-update (upsert) only.
//   - NO DelAll / NO measure deletes  (deletes -> "key not present in
//     dictionary" save failure AND they ORPHAN visuals -> Missing_References).
//   - NO AddCalculatedTable.
//   - Updates existing measures IN PLACE (keeps lineage -> visuals stay bound).
//
// IMPORTANT: do NOT re-run the "PAGE 10 + GATE-D FIXES" block inside
// final_master_install.cs — its line ~213 DelAll("Avg Solar Specific Yield
// kWh kWp") is what orphaned the visual and caused the current
// Missing_References on that bar. THIS file replaces it.
//
// Self-contained: specific yield is computed from solar_generated_kwh and
// pv_capacity_kwp (both already in gold_kpi_daily) — it does NOT depend on the
// solar_specific_yield_kwh_kwp column, so the 03 re-run is NOT a prerequisite.
//
// Built against live probe: semantic-model/_probe_output.txt
//   gold_iot_realtime[reading_value_avg|reading_value_max|sensor_type]
//   gold_iot_fdd[fault_code|cost_eur_estimate]
//   gold_kpi_daily[solar_generated_kwh|pv_capacity_kwp|building_id|date]
//   silver_building_master[pv_capacity_kwp]
//   gold_recommendations[action_type|country_code]
//   gold_country_regulations[feed_in_tariff_eur_per_kwh|country_code]
// =====================================================================

int created = 0, updated = 0, skipped = 0;

System.Action<string,string,string,string,string> Upsert = (table, name, expr, fmt, folder) => {
    if (!Model.Tables.Any(t => t.Name == table)) {
        Output("SKIP (missing table '" + table + "'): " + name); skipped++; return;
    }
    var m = Model.AllMeasures.FirstOrDefault(x => x.Name == name);
    if (m == null) { m = Model.Tables[table].AddMeasure(name, expr); created++; }
    else { m.Expression = expr; updated++; }     // update in place: does NOT re-orphan
    if (fmt != null) m.FormatString = fmt;
    if (folder != null) m.DisplayFolder = folder;
};

string F10 = "Solar - Realtime & Opportunity";

// ---- Row 4: live PV power (gold_iot_realtime, sensor_type = pv_ac_power) ----
Upsert("gold_iot_realtime", "Realtime PV Power kW",
@"CALCULATE( AVERAGE( gold_iot_realtime[reading_value_avg] ), gold_iot_realtime[sensor_type] = ""pv_ac_power"" )",
"#,##0.0", F10);

Upsert("gold_iot_realtime", "Peak PV Power kW",
@"CALCULATE( MAX( gold_iot_realtime[reading_value_max] ), gold_iot_realtime[sensor_type] = ""pv_ac_power"" )",
"#,##0.0", F10);

// ---- Row 4: PV underperformance faults (gold_iot_fdd) ----
Upsert("gold_iot_fdd", "PV Underperformance Count",
@"CALCULATE( COUNTROWS( gold_iot_fdd ), gold_iot_fdd[fault_code] = ""PV_UNDERPERFORMANCE"" )",
"#,##0", F10);

Upsert("gold_iot_fdd", "PV Loss EUR",
@"CALCULATE( SUM( gold_iot_fdd[cost_eur_estimate] ), gold_iot_fdd[fault_code] = ""PV_UNDERPERFORMANCE"" )",
"#,##0", F10);

// ---- Row 1: installed capacity card ----
Upsert("silver_building_master", "Solar Capacity kWp",
@"SUM( silver_building_master[pv_capacity_kwp] )",
"#,##0", F10);

// ---- Row 5: INSTALL_SOLAR opportunities (gold_recommendations) ----
Upsert("gold_recommendations", "INSTALL_SOLAR Opportunities",
@"CALCULATE( COUNTROWS( gold_recommendations ), gold_recommendations[action_type] = ""INSTALL_SOLAR"" )",
"#,##0", F10);

// Feed-in tariff per recommendation row (country lookup; no relationship needed).
// Lives on gold_recommendations (NOT gold_country_regulations) — that mismatch
// is what the visual must be re-pointed to (see rebind guide).
if (Model.Tables.Any(t => t.Name == "gold_country_regulations")) {
    Upsert("gold_recommendations", "Feed-in Tariff EUR kWh",
@"LOOKUPVALUE( gold_country_regulations[feed_in_tariff_eur_per_kwh], gold_country_regulations[country_code], SELECTEDVALUE( gold_recommendations[country_code] ) )",
"0.000", F10);
}

// ---- Row 3: specific yield, ANNUALIZED (kWh/kWp/yr), self-contained ----
// ASSUMPTION (energy logic, flagged): annualized = period yield * 365 / days-in-context.
// Realistic range: Berlin ~900-1000, Istanbul ~1300-1400 kWh/kWp/yr.
// To switch to DAILY yield (~2-4) instead: remove the "* 365.0" and "/ _days".
Upsert("gold_kpi_daily", "Avg Solar Specific Yield kWh kWp",
@"VAR _days = CALCULATE( DISTINCTCOUNT( gold_kpi_daily[date] ) )
RETURN
DIVIDE(
    AVERAGEX(
        VALUES( gold_kpi_daily[building_id] ),
        DIVIDE(
            CALCULATE( SUM( gold_kpi_daily[solar_generated_kwh] ) ),
            CALCULATE( MAX( gold_kpi_daily[pv_capacity_kwp] ) )
        )
    ) * 365.0,
    _days
)",
"#,##0", F10);

// ---- Row 1: total-weighted self-consumption rate (matches the donut split) ----
// The existing 'Avg Self Consumption Rate Pct' averages per building (unweighted)
// -> reads ~61% while the donut (kWh-weighted) reads ~37.5%. This one is
// kWh-weighted so the card and donut agree. Use THIS on the C2 card.
Upsert("gold_kpi_daily", "Solar Self-Consumption Rate Pct",
@"DIVIDE( [Solar Self Consumed kWh], [Total Solar Generated kWh] )",
"0.0%", F10);

// ---- Row 1 (OPTIONAL): renewable rate scoped to PV-equipped buildings ----
// The existing 'Renewable Energy Rate Pct' = solar / consumption of ALL buildings
// -> reads ~4% because the denominator includes non-solar buildings + big
// consumers (e.g. Frankfurt DC). That is CORRECT but undersells the solar page.
// This variant divides only by the consumption of buildings that HAVE PV, so the
// card answers "for our solar sites, what share of their demand is renewable?".
// ASSUMPTION (flag): bind this on the Renewable Rate card ONLY if you want the
// solar-sites view. Format "0.0".
Upsert("gold_kpi_daily", "Renewable Rate Solar Sites Pct",
@"VAR _solarBuildings = FILTER( VALUES( silver_building_master[building_id] ), CALCULATE( SUM( silver_building_master[pv_capacity_kwp] ) ) > 0 )
VAR _gen = CALCULATE( [Total Solar Generated kWh], KEEPFILTERS( _solarBuildings ) )
VAR _con = CALCULATE( [Total Consumption kWh], KEEPFILTERS( _solarBuildings ) )
RETURN DIVIDE( _gen, _con, 0 ) * 100",
"#,##0.0", F10);

Output(string.Format("Page 10 done. created={0} updated={1} skipped={2}", created, updated, skipped));
