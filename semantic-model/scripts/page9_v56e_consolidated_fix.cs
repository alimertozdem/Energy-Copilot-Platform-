// =====================================================================
// Page 9 v56e — CONSOLIDATED fix (Boolean MAX + V7 -3.3yr + V1 enhance)
// =====================================================================
// Date: 2026-05-21
// Includes:
//   1. C5, V5, I1, I2, I3 — Boolean MAX -> SELECTEDVALUE fixes
//   2. V7 Cycles Used + Years Until Replacement — HASONEVALUE guards
//      (fixes -3,3 yr bug at portfolio level)
//   3. V1 — new [V1 Best Strategy For Building Type] badge measure
//      (use as second column in matrix)
//   4. V4 Monthly Net Savings + CO2 measures (for new visual)
// =====================================================================

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
    if (t == null) { Output("[SKIP] Table not found: " + tableName); return; }
    Measure existing = null;
    foreach (var tbl in Model.Tables) {
        foreach (var m in tbl.Measures) {
            if (m.Name == measureName) { existing = m; break; }
        }
        if (existing != null) break;
    }
    if (existing != null) {
        if (existing.Table.Name != tableName) {
            existing.Delete();
            var m = t.AddMeasure(measureName, expression);
            if (!string.IsNullOrEmpty(format)) m.FormatString = format;
            if (!string.IsNullOrEmpty(folder)) m.DisplayFolder = folder;
            Output("[REHOME] " + tableName + "." + measureName);
        } else {
            existing.Expression = expression;
            if (!string.IsNullOrEmpty(format)) existing.FormatString = format;
            if (!string.IsNullOrEmpty(folder)) existing.DisplayFolder = folder;
            Output("[UPDATE] " + tableName + "." + measureName);
        }
    } else {
        var m = t.AddMeasure(measureName, expression);
        if (!string.IsNullOrEmpty(format)) m.FormatString = format;
        if (!string.IsNullOrEmpty(folder)) m.DisplayFolder = folder;
        Output("[CREATE] " + tableName + "." + measureName);
    }
};

// =====================================================================
// PART 1 — Boolean MAX fixes (C5, V5, I1, I2, I3)
// =====================================================================

upsert("gold_battery_simulation", "C5 EU Compliance Status Text",
@"VAR _active_tech =
    CALCULATE( MAX( gold_battery_dispatch[battery_tech] ),
               gold_battery_dispatch[is_simulated] = FALSE() )
VAR _country = SELECTEDVALUE( silver_building_master[country_code], ""DE"" )
VAR _is_eu_member =
    CALCULATE( SELECTEDVALUE(gold_country_regulations[is_eu_member]),
               gold_country_regulations[country_code] = _country )
VAR _nmc_allowed =
    CALCULATE( SELECTEDVALUE(gold_country_regulations[nmc_allowed_new_2025]),
               gold_country_regulations[country_code] = _country )
VAR _battery_eu_compliant =
    CALCULATE( SELECTEDVALUE( gold_battery_dispatch[eu_compliant] ),
               gold_battery_dispatch[is_simulated] = FALSE() )
RETURN
    SWITCH( TRUE(),
        ISBLANK(_active_tech),                                   ""— No active battery"",
        _active_tech = ""NMC"" && _country IN {""DE"",""AT""} && _nmc_allowed = FALSE(),
                            ""NMC banned for new installs in "" & _country,
        _battery_eu_compliant = FALSE() && _is_eu_member = TRUE(),
                            ""Non-compliant under EU 2023/1542"",
        _is_eu_member = TRUE() && _battery_eu_compliant = TRUE(),
                            ""EU 2023/1542 compliant"",
        _is_eu_member = FALSE(), ""Outside EU framework"",
        ""Status unknown"" )",
"", "Page 9 / KPI");

upsert("gold_country_regulations", "V5 Country Chemistry Flag",
@"VAR _country = SELECTEDVALUE( gold_country_regulations[country_code] )
VAR _chem    = SELECTEDVALUE( gold_battery_technologies[battery_type] )
VAR _is_eu   = CALCULATE( SELECTEDVALUE(gold_country_regulations[is_eu_member]),
                          gold_country_regulations[country_code] = _country )
VAR _nmc_ok  = CALCULATE( SELECTEDVALUE(gold_country_regulations[nmc_allowed_new_2025]),
                          gold_country_regulations[country_code] = _country )
VAR _sodium_ok = CALCULATE( SELECTEDVALUE(gold_country_regulations[sodium_ion_approved]),
                            gold_country_regulations[country_code] = _country )
VAR _ss_ok   = CALCULATE( SELECTEDVALUE(gold_country_regulations[solid_state_pilot]),
                          gold_country_regulations[country_code] = _country )
RETURN
    SWITCH( TRUE(),
        ISBLANK(_country) || ISBLANK(_chem), BLANK(),
        _chem = ""LFP"", 1,
        _chem = ""LFP-V2G"", IF(_is_eu = TRUE(), 1, 0),
        _chem = ""LFP-Supercap-Hybrid"", 1,
        _chem = ""NMC"" && _nmc_ok = TRUE(), 0,
        _chem = ""NMC"" && _nmc_ok = FALSE(), -1,
        _chem = ""Second-Life NMC"", IF(_is_eu = TRUE(), 0, -1),
        _chem = ""NCA"", 0,
        _chem = ""Sodium-Ion"" && _sodium_ok = TRUE(), 1,
        _chem = ""Sodium-Ion"" && _sodium_ok = FALSE(), 0,
        _chem = ""Solid-State"" && _ss_ok = TRUE(), 1,
        _chem = ""Solid-State"", 0,
        0 )",
"0", "Page 9 / V5");

upsert("gold_country_regulations", "I2 Chemistry Recommendation Text",
@"VAR _country = SELECTEDVALUE( silver_building_master[country_code], ""DE"" )
VAR _is_cold_climate = _country IN {""FI"",""NO"",""SE"",""DK"",""AT""}
VAR _nmc_ok =
    CALCULATE( SELECTEDVALUE(gold_country_regulations[nmc_allowed_new_2025]),
               gold_country_regulations[country_code] = _country )
VAR _sodium_ok =
    CALCULATE( SELECTEDVALUE(gold_country_regulations[sodium_ion_approved]),
               gold_country_regulations[country_code] = _country )
RETURN
    SWITCH( TRUE(),
        _is_cold_climate && _sodium_ok = TRUE(),
            ""Sodium-Ion (CATL Naxtra) — superior cold-weather performance below -10C. Lowest carbon footprint. Available Q3 2026 in "" & _country & ""."",
        _country IN {""DE"",""AT""} && _nmc_ok = FALSE(),
            ""LFP (CATL or Fluence) — NMC banned for new installs in "" & _country & "" per BattG 2025. 6000+ cycles, full EU compliance."",
        _country = ""NL"",
            ""LFP-V2G (BYD Battery-Box HVS) — Netherlands has most mature V2G regulation. ~30% additional revenue with EV fleet."",
        _country = ""UK"",
            ""LFP-Supercap-Hybrid (Skeleton) — UK Dynamic Containment + Capacity Market favor high-power chemistry."",
        ""LFP (CATL or Fluence) — best lifecycle value, EU 2023/1542 compliant, 12-year warranty."" )",
"", "Page 9 / Insights");

upsert("gold_country_regulations", "I3 Compliance Flag Text",
@"VAR _active_tech =
    CALCULATE( MAX( gold_battery_dispatch[battery_tech] ),
               gold_battery_dispatch[is_simulated] = FALSE() )
VAR _country = SELECTEDVALUE( silver_building_master[country_code], ""DE"" )
VAR _compliant =
    CALCULATE( SELECTEDVALUE( gold_battery_dispatch[eu_compliant] ),
               gold_battery_dispatch[is_simulated] = FALSE() )
VAR _is_eu_member =
    CALCULATE( SELECTEDVALUE(gold_country_regulations[is_eu_member]),
               gold_country_regulations[country_code] = _country )
RETURN
    SWITCH( TRUE(),
        ISBLANK(_active_tech),
            ""No active battery — simulation mode only."",
        _active_tech = ""NMC"" && _country IN {""DE"",""AT""},
            ""Active battery is NMC — banned in "" & _country & "" for new installs from 2025-01. Replacement window: 2027-Q1."",
        _is_eu_member = TRUE() && _compliant = FALSE(),
            ""Active battery does not meet EU 2023/1542 thresholds. Mandatory replacement before 2027 in regulated tenders."",
        _is_eu_member = TRUE() && _compliant = TRUE(),
            ""Active battery fully EU 2023/1542 compliant — Digital Battery Passport on file."",
        ""Active battery outside EU regulatory perimeter."" )",
"", "Page 9 / Insights");

upsert("gold_strategy_fitness", "I1 Strategy Recommendation Text",
@"VAR _bt = SELECTEDVALUE( silver_building_master[building_type], ""office"" )
VAR _country = SELECTEDVALUE( silver_building_master[country_code], ""DE"" )
VAR _primary =
    CALCULATE( SELECTEDVALUE( gold_strategy_fitness[strategy_label] ),
               gold_strategy_fitness[building_type] = _bt,
               gold_strategy_fitness[is_primary] = TRUE() )
VAR _secondary =
    CALCULATE( SELECTEDVALUE( gold_strategy_fitness[strategy_label] ),
               gold_strategy_fitness[building_type] = _bt,
               gold_strategy_fitness[is_secondary] = TRUE() )
VAR _primary_savings =
    CALCULATE( AVERAGE( gold_strategy_fitness[typical_annual_savings_eur_per_kwh] ),
               gold_strategy_fitness[building_type] = _bt,
               gold_strategy_fitness[is_primary] = TRUE() )
VAR _cap = SELECTEDVALUE( silver_building_master[battery_capacity_kwh], 100 )
VAR _est_eur = ROUND( _primary_savings * _cap, -2 )
RETURN
    ""For this "" & _bt & "" building in "" & _country & "", primary strategy: "" &
    _primary &
    IF( NOT ISBLANK(_secondary), "" (combined with "" & _secondary & "")"", """" ) &
    "". Estimated annual savings: EUR "" & FORMAT( _est_eur, ""#,0"" ) & "" (range +/-25%)."" ",
"", "Page 9 / Insights");

// =====================================================================
// PART 2 — V7 Cycles Used + Years Until Replacement — HASONEVALUE guards
// (Fixes -3,3 yr bug: only compute when single building+battery selected)
// =====================================================================

upsert("gold_battery_dispatch", "V7 Cycles Used Pct",
@"VAR _single = HASONEVALUE(silver_building_master[building_id])
VAR _used = CALCULATE( MAX( gold_battery_dispatch[cumulative_cycles] ),
                       gold_battery_dispatch[is_simulated] = FALSE() )
VAR _warranty = LOOKUPVALUE(
        gold_battery_technologies[warranty_cycles],
        gold_battery_technologies[battery_id],
        SELECTEDVALUE( gold_battery_dispatch[battery_id] ) )
RETURN
    IF( _single && NOT ISBLANK(_warranty) && _warranty > 0 && NOT ISBLANK(_used),
        DIVIDE( _used, _warranty ),
        BLANK() )",
"0.0%", "Page 9 / V7");

upsert("gold_battery_dispatch", "V7 Years Until Replacement",
@"VAR _single = HASONEVALUE(silver_building_master[building_id])
VAR _used = CALCULATE( MAX( gold_battery_dispatch[cumulative_cycles] ),
                       gold_battery_dispatch[is_simulated] = FALSE() )
VAR _warranty = LOOKUPVALUE(
        gold_battery_technologies[warranty_cycles],
        gold_battery_technologies[battery_id],
        SELECTEDVALUE( gold_battery_dispatch[battery_id] ) )
VAR _date_min = CALCULATE( MIN( gold_battery_dispatch[date] ),
                           gold_battery_dispatch[is_simulated] = FALSE() )
VAR _date_max = CALCULATE( MAX( gold_battery_dispatch[date] ),
                           gold_battery_dispatch[is_simulated] = FALSE() )
VAR _days = IF( NOT ISBLANK(_date_min) && NOT ISBLANK(_date_max),
                DATEDIFF(_date_min, _date_max, DAY), BLANK() )
VAR _avg_daily_cycles = IF( NOT ISBLANK(_days) && _days > 0,
                            DIVIDE(_used, _days), BLANK() )
VAR _remaining = _warranty - _used
RETURN
    IF( _single
        && NOT ISBLANK(_warranty)
        && NOT ISBLANK(_used)
        && _remaining > 0
        && NOT ISBLANK(_avg_daily_cycles)
        && _avg_daily_cycles > 0,
        DIVIDE( _remaining, _avg_daily_cycles ) / 365,
        BLANK() )",
@"0.0 ""yr""", "Page 9 / V7");

upsert("gold_battery_dispatch", "V7 Current SoH Pct",
@"VAR _single = HASONEVALUE(silver_building_master[building_id])
VAR _soh =
    CALCULATE( AVERAGE( gold_battery_dispatch[battery_health_percent] ),
               gold_battery_dispatch[is_simulated] = FALSE(),
               gold_battery_dispatch[date] = MAX( gold_battery_dispatch[date] ) )
RETURN
    IF( _single && NOT ISBLANK(_soh),
        DIVIDE( _soh, 100 ),
        BLANK() )",
"0.0%", "Page 9 / V7");

// =====================================================================
// PART 3 — V1 enhancement: Best Strategy For Building Type badge
// =====================================================================

upsert("gold_strategy_fitness", "V1 Best Strategy For Building Type",
@"VAR _bt = SELECTEDVALUE( gold_strategy_fitness[building_type] )
RETURN
    CALCULATE(
        SELECTEDVALUE( gold_strategy_fitness[strategy_label] ),
        gold_strategy_fitness[building_type] = _bt,
        gold_strategy_fitness[is_primary] = TRUE()
    )",
"", "Page 9 / V1");

// =====================================================================
// PART 4 — V4 Monthly Net Savings + CO2 (for new chart in empty zone)
// =====================================================================

upsert("gold_battery_dispatch", "V4 Monthly Net Savings EUR",
@"CALCULATE(
    SUM( gold_battery_dispatch[net_savings_eur] ),
    gold_battery_dispatch[is_simulated] = FALSE() )",
"€ #,##0", "Page 9 / V4");

upsert("gold_battery_dispatch", "V4 Monthly CO2 Avoided Kg",
@"CALCULATE(
    SUM( gold_battery_dispatch[co2_avoided_kg] ),
    gold_battery_dispatch[is_simulated] = FALSE() )",
@"#,0 ""kg""", "Page 9 / V4");

Output("Page 9 v56e consolidated fix COMPLETE.");
Output("- 5 Boolean MAX fixes (C5, V5, I1, I2, I3)");
Output("- 3 V7 guard fixes (SoH, Cycles Used, Yrs to Replace) — no more -3,3 yr");
Output("- 1 new V1 Best Strategy badge measure");
Output("- 2 new V4 monthly measures");
Output("Save (Ctrl+S), refresh Power BI.");
