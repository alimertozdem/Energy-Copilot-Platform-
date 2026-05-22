// =====================================================================
// Page 9 v56 — Master Install (Tabular Editor 2 script)
// =====================================================================
// Date    : 2026-05-21
// Target  : EnergyCopilotModel semantic model
// Purpose : Install / upsert all Page 9 v56 master measures, ensuring
//           each measure lives on the correct HOME TABLE (this fixes the
//           "Move measure to another table" warnings shown in Power BI).
//
// PRE-FLIGHT
//   1. Upload the new CSVs into the Fabric Lakehouse (or local model):
//        - sample-data/gold_country_regulations.csv
//        - sample-data/gold_strategy_fitness.csv
//        - sample-data/gold_battery_technologies.csv  (already exists,
//          appended 5 new rows in this commit)
//      Then build/refresh the semantic model so the tables are visible.
//   2. Open Power BI Desktop (live to EnergyCopilotModel) → External
//      Tools → Tabular Editor 2.
//   3. Paste this script into Advanced Scripting → Run → save.
//
// =====================================================================
// HELPER: upsert measure on a target table
// =====================================================================

// Safe table lookup — TE2's Model.Tables[name] throws ArgumentException
// instead of returning null when the table doesn't exist.
System.Func<string, Table> findTable = (string name) => {
    foreach (var tbl in Model.Tables) {
        if (tbl.Name == name) return tbl;
    }
    return null;
};

System.Action<string,string,string,string,string> upsert =
    (string tableName, string measureName, string expression, string format, string folder) =>
{
    var t = findTable(tableName);
    if (t == null) {
        Output("[SKIP] Table not found in model: '" + tableName + "' — measure '" + measureName + "' not installed.");
        return;
    }

    // Find existing measure ANYWHERE in the model so we can move it if needed
    Measure existing = null;
    foreach (var tbl in Model.Tables) {
        foreach (var m in tbl.Measures) {
            if (m.Name == measureName) { existing = m; break; }
        }
        if (existing != null) break;
    }

    if (existing != null) {
        // TE2 limitation: Measure.Table is read-only.
        // If the home table is wrong, DELETE + CREATE on target table.
        if (existing.Table.Name != tableName) {
            Output("[REHOME] " + measureName + " : " + existing.Table.Name + " → " + tableName + " (delete+recreate)");
            existing.Delete();
            var m = t.AddMeasure(measureName, expression);
            if (!string.IsNullOrEmpty(format)) m.FormatString = format;
            if (!string.IsNullOrEmpty(folder)) m.DisplayFolder = folder;
            return;
        }
        existing.Expression = expression;
        if (!string.IsNullOrEmpty(format)) existing.FormatString = format;
        if (!string.IsNullOrEmpty(folder)) existing.DisplayFolder = folder;
        Output("[UPDATE] " + tableName + "." + measureName);
    } else {
        var m = t.AddMeasure(measureName, expression);
        if (!string.IsNullOrEmpty(format)) m.FormatString = format;
        if (!string.IsNullOrEmpty(folder)) m.DisplayFolder = folder;
        Output("[CREATE] " + tableName + "." + measureName);
    }
};

// =====================================================================
// §1 — ORPHANED V2 FIX (6 measures rehomed to gold_battery_dispatch)
// =====================================================================

upsert("gold_battery_dispatch", "V2 Charge kWh Daily",
@"IFERROR( SUM( gold_battery_dispatch[charge_kwh] ), BLANK() )",
"#,0",
"Page 9 / V2 Daily Flow");

upsert("gold_battery_dispatch", "V2 Discharge kWh Daily",
@"IFERROR( SUM( gold_battery_dispatch[discharge_kwh] ), BLANK() )",
"#,0",
"Page 9 / V2 Daily Flow");

upsert("gold_battery_dispatch", "V2 PV Generation kWh",
@"IFERROR( SUM( gold_battery_dispatch[pv_generation_kwh] ), BLANK() )",
"#,0",
"Page 9 / V2 Daily Flow");

upsert("gold_battery_dispatch", "V2 Grid Charge kWh Daily",
@"IFERROR( SUM( gold_battery_dispatch[grid_charge_kwh] ), BLANK() )",
"#,0",
"Page 9 / V2 Daily Flow");

upsert("gold_battery_dispatch", "V2 PV Charge kWh Daily",
@"IFERROR( SUM( gold_battery_dispatch[pv_charge_kwh] ), BLANK() )",
"#,0",
"Page 9 / V2 Daily Flow");

upsert("gold_battery_dispatch", "V2 Net Savings EUR Daily",
@"IFERROR( SUM( gold_battery_dispatch[net_savings_eur] ), BLANK() )",
"€ #,##0",
"Page 9 / V2 Daily Flow");


// =====================================================================
// §2 — KPI Cards C1–C5
// =====================================================================

upsert("gold_battery_dispatch", "C1 Annual Savings EUR",
@"VAR _has_active =
    NOT ISBLANK( CALCULATE( COUNTROWS( gold_battery_dispatch ),
        gold_battery_dispatch[is_simulated] = FALSE() ) )
VAR _annual_savings =
    CALCULATE(
        SUM( gold_battery_dispatch[net_savings_eur] ),
        gold_battery_dispatch[is_simulated] = FALSE(),
        gold_battery_dispatch[date] >= DATE(YEAR(TODAY())-1, MONTH(TODAY()), DAY(TODAY()))
    )
VAR _fallback_sim =
    CALCULATE(
        AVERAGE( gold_battery_simulation[annual_savings_eur] ),
        gold_battery_simulation[is_active_strategy] = TRUE()
    )
RETURN
    IF( _has_active && NOT ISBLANK(_annual_savings) && _annual_savings > 0,
        _annual_savings, _fallback_sim )",
"€ #,##0",
"Page 9 / KPI");

upsert("gold_battery_simulation", "C2 Payback Years",
@"VAR _payback =
    CALCULATE(
        AVERAGE( gold_battery_simulation[payback_years] ),
        gold_battery_simulation[is_active_strategy] = TRUE()
    )
RETURN
    IF( ISBLANK(_payback) || _payback >= 99, BLANK(), ROUND(_payback, 1) )",
@"0.0 ""yr""",
"Page 9 / KPI");

upsert("gold_battery_simulation", "C2 Payback Status Label",
@"VAR _y = [C2 Payback Years]
RETURN
    SWITCH( TRUE(),
        ISBLANK(_y),       ""—"",
        _y <= 5,           ""✓ Excellent"",
        _y <= 8,           ""✓ Good"",
        _y <= 12,          ""⚠ Acceptable"",
        ""✗ Poor"" )",
"",
"Page 9 / KPI");

upsert("gold_battery_dispatch", "C3 CO2 Avoided Tonnes Annual",
@"VAR _co2_kg =
    CALCULATE(
        SUM( gold_battery_dispatch[co2_avoided_kg] ),
        gold_battery_dispatch[is_simulated] = FALSE(),
        gold_battery_dispatch[date] >= DATE(YEAR(TODAY())-1, MONTH(TODAY()), DAY(TODAY()))
    )
RETURN
    DIVIDE( _co2_kg, 1000 )",
@"#,0.0 ""tCO₂""",
"Page 9 / KPI");

upsert("gold_battery_dispatch", "C4 Round Trip Efficiency Pct",
@"VAR _rte =
    CALCULATE(
        AVERAGE( gold_battery_dispatch[round_trip_efficiency_percent] ),
        gold_battery_dispatch[is_simulated] = FALSE()
    )
RETURN
    DIVIDE( _rte, 100 )",
"0.0%",
"Page 9 / KPI");

upsert("gold_battery_simulation", "C5 EU Compliance Status Text",
@"VAR _active_tech =
    CALCULATE(
        MAX( gold_battery_dispatch[battery_tech] ),
        gold_battery_dispatch[is_simulated] = FALSE()
    )
VAR _country =
    SELECTEDVALUE( silver_building_master[country_code], ""DE"" )
VAR _is_eu_member =
    CALCULATE( MAX(gold_country_regulations[is_eu_member]),
               gold_country_regulations[country_code] = _country )
VAR _nmc_allowed =
    CALCULATE( MAX(gold_country_regulations[nmc_allowed_new_2025]),
               gold_country_regulations[country_code] = _country )
VAR _battery_eu_compliant =
    CALCULATE(
        MAX( gold_battery_dispatch[eu_compliant] ),
        gold_battery_dispatch[is_simulated] = FALSE()
    )
RETURN
    SWITCH( TRUE(),
        ISBLANK(_active_tech),                                   ""— No active battery"",
        _active_tech = ""NMC"" && _country IN {""DE"",""AT""} && NOT _nmc_allowed,
                            ""❌ NMC banned for new installs in "" & _country,
        NOT _battery_eu_compliant && _is_eu_member,
                            ""⚠ Non-compliant under EU 2023/1670"",
        _is_eu_member && _battery_eu_compliant,
                            ""✓ EU 2023/1670 compliant"",
        NOT _is_eu_member,  ""ℹ Outside EU framework"",
        ""ℹ Status unknown"" )",
"",
"Page 9 / KPI");


// =====================================================================
// §3 — Visual measures
// =====================================================================

upsert("gold_strategy_fitness", "V1 Strategy Fitness Score",
@"AVERAGE( gold_strategy_fitness[fitness_score] )",
"0",
"Page 9 / V1");

upsert("gold_strategy_fitness", "V1 Fitness Color Bucket",
@"VAR _s = [V1 Strategy Fitness Score]
RETURN
    SWITCH( TRUE(),
        _s >= 80, ""#27AE60"",
        _s >= 60, ""#F39C12"",
        _s >= 40, ""#E67E22"",
        ""#C0392B"" )",
"",
"Page 9 / V1");

upsert("gold_battery_simulation", "V3 CAPEX EUR",
@"AVERAGE( gold_battery_simulation[total_capex_eur] )",
"€ #,##0",
"Page 9 / V3");

upsert("gold_battery_simulation", "V3 Payback Years",
@"AVERAGE( gold_battery_simulation[payback_years] )",
"0.0",
"Page 9 / V3");

upsert("gold_battery_simulation", "V3 Battery Chemistry Color",
@"VAR _tech =
    SELECTEDVALUE( gold_battery_simulation[battery_tech], ""LFP"" )
RETURN
    SWITCH( TRUE(),
        _tech = ""LFP"",                   ""#27AE60"",
        _tech = ""Sodium-Ion"",            ""#F1C40F"",
        _tech = ""Solid-State"",           ""#9B59B6"",
        _tech = ""LFP-V2G"",               ""#16A085"",
        _tech IN {""NMC"",""NCA""},          ""#E67E22"",
        _tech = ""Second-Life NMC"",       ""#7F8C8D"",
        _tech = ""LFP-Supercap-Hybrid"",   ""#2980B9"",
        ""#95A5A6"" )",
"",
"Page 9 / V3");

upsert("gold_battery_dispatch", "V4 Monthly Net Savings EUR",
@"CALCULATE(
    SUM( gold_battery_dispatch[net_savings_eur] ),
    gold_battery_dispatch[is_simulated] = FALSE() )",
"€ #,##0",
"Page 9 / V4");

upsert("gold_battery_dispatch", "V4 Monthly CO2 Avoided Kg",
@"CALCULATE(
    SUM( gold_battery_dispatch[co2_avoided_kg] ),
    gold_battery_dispatch[is_simulated] = FALSE() )",
@"#,0 ""kg""",
"Page 9 / V4");

upsert("gold_country_regulations", "V5 Country Chemistry Flag",
@"VAR _country = SELECTEDVALUE( gold_country_regulations[country_code] )
VAR _chem    = SELECTEDVALUE( gold_battery_technologies[battery_type] )
VAR _is_eu   = CALCULATE( MAX(gold_country_regulations[is_eu_member]),
                          gold_country_regulations[country_code] = _country )
VAR _nmc_ok  = CALCULATE( MAX(gold_country_regulations[nmc_allowed_new_2025]),
                          gold_country_regulations[country_code] = _country )
VAR _sodium_ok = CALCULATE( MAX(gold_country_regulations[sodium_ion_approved]),
                            gold_country_regulations[country_code] = _country )
VAR _ss_ok   = CALCULATE( MAX(gold_country_regulations[solid_state_pilot]),
                          gold_country_regulations[country_code] = _country )
RETURN
    SWITCH( TRUE(),
        ISBLANK(_country) || ISBLANK(_chem), BLANK(),
        _chem = ""LFP"",                                       1,
        _chem = ""LFP-V2G"",                                   IF(_is_eu, 1, 0),
        _chem = ""LFP-Supercap-Hybrid"",                       1,
        _chem = ""NMC"" && _nmc_ok,                            0,
        _chem = ""NMC"" && NOT _nmc_ok,                       -1,
        _chem = ""Second-Life NMC"",                           IF(_is_eu, 0, -1),
        _chem = ""NCA"",                                       0,
        _chem = ""Sodium-Ion"" && _sodium_ok,                  1,
        _chem = ""Sodium-Ion"" && NOT _sodium_ok,              0,
        _chem = ""Solid-State"" && _ss_ok,                     1,
        _chem = ""Solid-State"",                               0,
        0 )",
"0",
"Page 9 / V5");

upsert("gold_country_regulations", "V5 Country Chemistry Symbol",
@"VAR _f = [V5 Country Chemistry Flag]
RETURN
    SWITCH( TRUE(),
        ISBLANK(_f), ""—"",
        _f = 1,      ""✓"",
        _f = 0,      ""⚠"",
        _f = -1,     ""✗"",
        """" )",
"",
"Page 9 / V5");

upsert("gold_battery_dispatch", "V7 Current SoH Pct",
@"DIVIDE(
    CALCULATE(
        AVERAGE( gold_battery_dispatch[battery_health_percent] ),
        gold_battery_dispatch[is_simulated] = FALSE(),
        gold_battery_dispatch[date] = MAX( gold_battery_dispatch[date] )
    ), 100 )",
"0.0%",
"Page 9 / V7");

upsert("gold_battery_dispatch", "V7 Cycles Used Pct",
@"VAR _used =
    CALCULATE(
        MAX( gold_battery_dispatch[cumulative_cycles] ),
        gold_battery_dispatch[is_simulated] = FALSE()
    )
VAR _warranty =
    LOOKUPVALUE(
        gold_battery_technologies[warranty_cycles],
        gold_battery_technologies[battery_id],
        SELECTEDVALUE( gold_battery_dispatch[battery_id] )
    )
RETURN
    DIVIDE( _used, _warranty )",
"0.0%",
"Page 9 / V7");

upsert("gold_battery_dispatch", "V7 Years Until Replacement",
@"VAR _used = CALCULATE(
        MAX( gold_battery_dispatch[cumulative_cycles] ),
        gold_battery_dispatch[is_simulated] = FALSE() )
VAR _warranty =
    LOOKUPVALUE(
        gold_battery_technologies[warranty_cycles],
        gold_battery_technologies[battery_id],
        SELECTEDVALUE( gold_battery_dispatch[battery_id] ) )
VAR _avg_daily_cycles =
    DIVIDE( _used,
        DATEDIFF(
            CALCULATE( MIN( gold_battery_dispatch[date] ),
                       gold_battery_dispatch[is_simulated] = FALSE() ),
            CALCULATE( MAX( gold_battery_dispatch[date] ),
                       gold_battery_dispatch[is_simulated] = FALSE() ),
            DAY ) )
VAR _remaining = _warranty - _used
RETURN
    IF( _avg_daily_cycles > 0,
        DIVIDE( _remaining, _avg_daily_cycles ) / 365,
        BLANK() )",
@"0.0 ""yr""",
"Page 9 / V7");


// =====================================================================
// §4 — Insight strip
// =====================================================================

upsert("gold_strategy_fitness", "I1 Strategy Recommendation Text",
@"VAR _bt = SELECTEDVALUE( silver_building_master[building_type], ""office"" )
VAR _country = SELECTEDVALUE( silver_building_master[country_code], ""DE"" )
VAR _primary =
    CALCULATE(
        SELECTEDVALUE( gold_strategy_fitness[strategy_label] ),
        gold_strategy_fitness[building_type] = _bt,
        gold_strategy_fitness[is_primary] = TRUE() )
VAR _secondary =
    CALCULATE(
        SELECTEDVALUE( gold_strategy_fitness[strategy_label] ),
        gold_strategy_fitness[building_type] = _bt,
        gold_strategy_fitness[is_secondary] = TRUE() )
VAR _primary_savings =
    CALCULATE(
        AVERAGE( gold_strategy_fitness[typical_annual_savings_eur_per_kwh] ),
        gold_strategy_fitness[building_type] = _bt,
        gold_strategy_fitness[is_primary] = TRUE() )
VAR _cap =
    SELECTEDVALUE( silver_building_master[battery_capacity_kwh], 100 )
VAR _est_eur = ROUND( _primary_savings * _cap, -2 )
RETURN
    ""For this "" & _bt & "" building in "" & _country & "", primary strategy: "" &
    _primary &
    IF( NOT ISBLANK(_secondary), "" (combined with "" & _secondary & "")"", """" ) &
    "". Estimated annual savings ≈ €"" & FORMAT( _est_eur, ""#,0"" ) & "" (range ±25%)."" ",
"",
"Page 9 / Insights");

upsert("gold_country_regulations", "I2 Chemistry Recommendation Text",
@"VAR _country = SELECTEDVALUE( silver_building_master[country_code], ""DE"" )
VAR _is_cold_climate = _country IN {""FI"",""NO"",""SE"",""DK"",""AT""}
VAR _nmc_ok =
    CALCULATE( MAX(gold_country_regulations[nmc_allowed_new_2025]),
               gold_country_regulations[country_code] = _country )
VAR _sodium_ok =
    CALCULATE( MAX(gold_country_regulations[sodium_ion_approved]),
               gold_country_regulations[country_code] = _country )
RETURN
    SWITCH( TRUE(),
        _is_cold_climate && _sodium_ok,
            ""Recommended: Sodium-Ion (CATL Naxtra) — superior cold-weather performance below -10°C, lowest carbon footprint (28 kg CO₂/kWh), available Q3 2026 in "" & _country & ""."",
        _country IN {""DE"",""AT""} && NOT _nmc_ok,
            ""Recommended: LFP (CATL or Fluence) — NMC chemistry banned for new installs in "" & _country & "" per BattG 2025 amendment. LFP yields 6,000+ cycles and full EU 2023/1670 compliance."",
        _country = ""NL"",
            ""Recommended: LFP-V2G (BYD Battery-Box HVS) — Netherlands has most mature V2G regulation. Bidirectional charger + EV fleet integration yields ~30% additional revenue."",
        _country = ""UK"",
            ""Recommended: LFP-Supercap-Hybrid (Skeleton SkelGrid) — UK Dynamic Containment + Capacity Market favor high-power chemistry with 1M+ cycle equivalent."",
        ""Recommended: LFP (CATL or Fluence) — best lifecycle value, full EU 2023/1670 compliance, 12-year warranty, 6,000+ cycles."" )",
"",
"Page 9 / Insights");

upsert("gold_country_regulations", "I3 Compliance Flag Text",
@"VAR _active_tech =
    CALCULATE(
        MAX( gold_battery_dispatch[battery_tech] ),
        gold_battery_dispatch[is_simulated] = FALSE() )
VAR _country = SELECTEDVALUE( silver_building_master[country_code], ""DE"" )
VAR _compliant =
    CALCULATE(
        MAX( gold_battery_dispatch[eu_compliant] ),
        gold_battery_dispatch[is_simulated] = FALSE() )
VAR _is_eu_member =
    CALCULATE( MAX(gold_country_regulations[is_eu_member]),
               gold_country_regulations[country_code] = _country )
RETURN
    SWITCH( TRUE(),
        ISBLANK(_active_tech),
            ""No active battery — simulation mode only."",
        _active_tech = ""NMC"" && _country IN {""DE"",""AT""},
            ""⚠ Active battery is NMC — banned in "" & _country & "" for new installs from 2025-01. Replacement window: 2027-Q1."",
        _is_eu_member && NOT _compliant,
            ""⚠ Active battery does not meet EU 2023/1670 thresholds (carbon footprint or recycled content). Mandatory replacement before 2027 in regulated tenders."",
        _is_eu_member && _compliant,
            ""✓ Active battery fully EU 2023/1670 compliant — Digital Battery Passport on file."",
        ""ℹ Active battery outside EU regulatory perimeter."" )",
"",
"Page 9 / Insights");

upsert("gold_battery_dispatch", "I4 Next Action Text",
@"VAR _yr_to_replace = [V7 Years Until Replacement]
VAR _payback = [C2 Payback Years]
RETURN
    SWITCH( TRUE(),
        ISBLANK(_yr_to_replace) && ISBLANK(_payback),
            ""Run a 12-month dispatch simulation to populate financial metrics."",
        NOT ISBLANK(_yr_to_replace) && _yr_to_replace < 2,
            ""⚠ Battery cycle headroom < 2 years. Plan replacement procurement now (lead time 8-14 weeks for LFP)."",
        NOT ISBLANK(_yr_to_replace) && _yr_to_replace < 5,
            ""Cycle headroom "" & FORMAT(_yr_to_replace, ""0.0"") & "" years. Schedule mid-life maintenance + warranty audit."",
        NOT ISBLANK(_payback) && _payback < 5,
            ""✓ Strong investment case (payback < 5 years). Recommend portfolio rollout to similar buildings."",
        ""Battery operating within design envelope. Monitor next mid-life review in 24 months."" )",
"",
"Page 9 / Insights");


// =====================================================================
// §5 — Helpers
// =====================================================================

upsert("gold_battery_dispatch", "Active Battery Label",
@"VAR _tech =
    CALCULATE(
        MAX( gold_battery_dispatch[battery_tech] ),
        gold_battery_dispatch[is_simulated] = FALSE() )
VAR _type =
    CALCULATE(
        MAX( gold_battery_dispatch[battery_type] ),
        gold_battery_dispatch[is_simulated] = FALSE() )
VAR _cap =
    CALCULATE(
        MAX( gold_battery_dispatch[capacity_kwh] ),
        gold_battery_dispatch[is_simulated] = FALSE() )
RETURN
    IF( ISBLANK(_tech), ""— No active battery —"",
        _type & "" · "" & FORMAT(_cap, ""#,0"") & "" kWh"" )",
"",
"Page 9 / Helpers");

upsert("gold_battery_dispatch", "Active Strategy Short Label",
@"VAR _s =
    CALCULATE(
        MAX( gold_battery_dispatch[strategy] ),
        gold_battery_dispatch[is_simulated] = FALSE() )
RETURN
    SWITCH( TRUE(),
        ISBLANK(_s),               ""— Select strategy —"",
        _s = ""self_consumption"",   ""● Self-Consumption"",
        _s = ""peak_shaving"",       ""● Peak-Shaving"",
        _s = ""tou"",                ""● Time-of-Use"",
        _s = ""backup"",             ""● Backup + Opportunistic"",
        _s = ""frequency_reserve"",  ""● Frequency Reserve"",
        _s = ""capacity_market"",    ""● Capacity Market"",
        _s = ""v2g"",                ""● V2G Coordination"",
        ""● "" & _s )",
"",
"Page 9 / Helpers");

upsert("gold_battery_dispat