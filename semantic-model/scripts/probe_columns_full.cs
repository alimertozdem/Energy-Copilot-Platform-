// =====================================================================
// PROBE — Full column listing for Page 9 tables
// =====================================================================
// Read-only. Lists every column name in the 5 Page 9 tables so we can
// compare against what the DAX expects.
// =====================================================================

string[] tables = new string[] {
    "gold_battery_dispatch",
    "gold_battery_simulation",
    "gold_battery_technologies",
    "gold_country_regulations",
    "gold_strategy_fitness",
    "silver_building_master"
};

foreach (var tName in tables) {
    Table t = null;
    foreach (var tbl in Model.Tables) {
        if (tbl.Name == tName) { t = tbl; break; }
    }

    Output("");
    Output("=================================================================");
    if (t == null) {
        Output("[MISSING] " + tName);
        continue;
    }
    Output("TABLE: " + t.Name + "   (" + t.Columns.Count + " columns)");
    Output("=================================================================");
    int idx = 0;
    foreach (var c in t.Columns.OrderBy(c => c.Name)) {
        idx++;
        Output(string.Format("  {0,2}. {1,-40} {2}", idx, c.Name, c.DataType));
    }
}

Output("");
Output("=================================================================");
Output("DAX expects these columns:");
Output("  gold_battery_dispatch    : date, building_id, battery_id, battery_tech,");
Output("                             battery_type, capacity_kwh, strategy, is_simulated,");
Output("                             charge_kwh, discharge_kwh, pv_generation_kwh,");
Output("                             pv_charge_kwh, grid_charge_kwh, net_savings_eur,");
Output("                             co2_avoided_kg, round_trip_efficiency_percent,");
Output("                             battery_health_percent, cumulative_cycles,");
Output("                             eu_compliant");
Output("  gold_battery_simulation  : payback_years, annual_savings_eur, total_capex_eur,");
Output("                             is_active_strategy, battery_tech, building_id");
Output("  gold_battery_technologies: battery_id, battery_type, warranty_cycles");
Output("  gold_country_regulations : country_code, is_eu_member, nmc_allowed_new_2025,");
Output("                             sodium_ion_approved, solid_state_pilot");
Output("  gold_strategy_fitness    : building_type, strategy_label, fitness_score,");
Output("                             is_primary, is_secondary,");
Output("                             typical_annual_savings_eur_per_kwh");
Output("  silver_building_master   : building_id, building_type, country_code,");
Output("                             battery_capacity_kwh, max_occupants");
Output("=================================================================");
