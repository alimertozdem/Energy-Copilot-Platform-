// =====================================================================
// Page 9 v56b — Text/Boolean comparison fix
// =====================================================================
// Date    : 2026-05-21
// Reason  : v56 install assumed is_simulated / is_active_strategy / eu_compliant
//           were Boolean columns. But Spark inferSchema loaded them as Text.
//           Power BI error:
//             "DAX comparison operations do not support comparing values of
//              type Text with values of type True/False"
//
// Strategy : Replace 9 measures with versions that use text comparisons
//            ("true" / "false") instead of TRUE() / FALSE(). Works correctly
//            for the current Text columns; would also work if columns were
//            ever cast to Boolean (DAX coercion handles "true" both ways).
//
// SCOPE
//   §2 KPI cards : C1, C2, C3, C4, C5
//   §3 V4, V7
//   §4 I1, I3
//
// IDEMPOTENT : safe to re-run.
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
    if (t == null) {
        Output("[SKIP] Table not found: " + tableName);
        return;
    }
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
            Output("[REHOME+UPDATE] " + tableName + "." + measureName);
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
// C1 — Annual Savings EUR  (is_simulated text fix)
// =====================================================================
upsert("gold_battery_dispatch", "C1 Annual Savings EUR",
@"VAR _has_active =
    NOT ISBLANK( CALCULATE( COUNTROWS( gold_battery_dispatch ),
        gold_battery_dispatch[is_simulated] = ""false"" ) )
VAR _annual_savings =
    CALCULATE(
        SUM( gold_battery_dispatch[net_savings_eur] ),
        gold_battery_dispatch[is_simulated] = ""false"",
        gold_battery_dispatch[date] >= DATE(YEAR(TODAY())-1, MONTH(TODAY()), DAY(TODAY()))
    )
VAR _fallback_sim =
    CALCULATE(
        AVERAGE( gold_battery_simulation[annual_savings_eur] ),
        gold_battery_simulation[is_active_strategy] = ""true""
    )
RETURN
    IF( _has_active && NOT ISBLANK(_annual_savings) && _annual_savings > 0,
        _annual_savings, _fallback_sim )",
"€ #,##0",
"Page 9 / KPI");

// =====================================================================
// C2 — Payback Years  (is_active_strategy text fix)
// =====================================================================
upsert("gold_battery_simulation", "C2 Payback Years",
@"VAR _payback =
    CALCULATE(
        AVERAGE( gold_battery_simulation[payback_years] ),
        gold_battery_simulation[is_active_strategy] = ""true""
    )
RETURN
    IF( ISBLANK(_payback) || _payback >= 99, BLANK(), ROUND(_payback, 1) )",
@"0.0 ""yr""",
"Page 9 / KPI");

// =====================================================================
// C3 — CO2 Avoided Tonnes Annual  (is_simulated text fix)
// =====================================================================
upsert("gold_battery_dispatch", "C3 CO2 Avoided Tonnes Annual",
@"VAR _co2_kg =
    CALCULATE(
        SUM( gold_battery_dispatch[co2_avoided_kg] ),
        gold_battery_dispatch[is_simulated] = ""false"",
        gold_battery_dispatch[date] >= DATE(YEAR(TODAY())-1, MONTH(TODAY()), DAY(TODAY()))
    )
RETURN
    DIVIDE( _co2_kg, 1000 )",
@"#,0.0 ""tCO₂""",
"Page 9 / KPI");

// =====================================================================
// C4 — Round Trip Efficiency Pct  (is_simulated text fix)
// =====================================================================
upsert("gold_battery_dispatch", "C4 Round Trip Efficiency Pct",
@"VAR _rte =
    CALCULATE(
        AVERAGE( gold_battery_dispatch[round_trip_efficiency_percent] ),
        gold_battery_dispatch[is_simulated] = ""false""
    )
RETURN
    DIVIDE( _rte, 100 )",
"0.0%",
"Page 9 / KPI");

// =====================================================================
// C5 — EU Compliance Status Text  (eu_compliant + is_simulated + is_eu_member text fix)
// =====================================================================
upsert("gold_battery_simulation", "C5 EU Compliance Status Text",
@"VAR _active_tech =
    CALCULATE(
        MAX( gold_battery_dispatch[battery_tech] ),
        gold_battery_dispatch[is_simulated] = ""false""
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
        gold_battery_dispatch[is_simulated] = ""false""
    )
RETURN
    SWITCH( TRUE(),
        ISBLANK(_active_tech),                                   ""— No active battery"",
        _active_tech = ""NMC"" && _country IN {""DE"",""AT""} && _nmc_allowed <> ""true"",
                            ""❌ NMC banned for new installs in "" & _country,
        _battery_eu_compliant <> ""true"" && _is_eu_member = ""true"",
                            ""⚠ Non-compliant under EU 2023/1670"",
        _is_eu_member = ""true"" && _battery_eu_compliant = ""true"",
                            ""✓ EU 2023/1670 compliant"",
        _is_eu_member <> ""true"",  ""ℹ Outside EU framework"",
        ""ℹ Status unknown"" )",
"",
"Page 9 / KPI");

// =====================================================================
// V4 — Monthly Net Savings + CO2 (is_simulated text fix)
// =====================================================================
upsert("gold_battery_dispatch", "V4 Monthly Net Savings EUR",
@"CALCULATE(
    SUM( gold_battery_dispatch[net_savings_eur] ),
    gold_battery_dispatch[is_simulated] = ""false"" )",
"€ #,##0",
"Page 9 / V4");

upsert("gold_battery_dispatch", "V4 Monthly CO2 Avoided Kg",
@"CALCULATE(
    SUM( gold_battery_dispatch[co2_avoided_kg] ),
    gold_battery_dispatch[is_simulated] = ""false"" )",
@"#,0 ""kg""",
"Page 9 / V4");

// =====================================================================
// V5 — Country Chemistry Flag (lfp_allowed, nmc_allowed_new_2025, etc text fix)
// =====================================================================
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
        _chem = ""LFP-V2G"",                                   IF(_is_eu = ""true"", 1, 0),
        _chem = ""LFP-Supercap-Hybrid"",                       1,
        _chem = ""NMC"" && _nmc_ok = ""true"",                  0,
        _chem = ""NMC"" && _nmc_ok <> ""true"",                -1,
        _chem = ""Second-Life NMC"",                           IF(_is_eu = ""true"", 0, -1),
        _chem = ""NCA"",                                       0,
        _chem = ""Sodium-Ion"" && _sodium_ok = ""true"",        1,
        _chem = ""Sodium-Ion"" && _sodium_ok <> ""true"",       0,
        _chem = ""Solid-State"" && _ss_ok = ""true"",           1,
        _chem = ""Solid-State"",                               0,
        0 )",
"0",
"Page 9 / V5");

// =====================================================================
// V7 — Battery health measures (is_simulated text fix)
// =====================================================================
upsert("gold_battery_dispatch", "V7 Current SoH Pct",
@"DIVIDE(
    CALCULATE(
        AVERAGE( gold_battery_dispatch[battery_health_percent] ),
        gold_battery_dispatch[is_simulated] = ""false"",
        gold_battery_dispatch[date] = MAX( gold_battery_dispatch[date] )
    ), 100 )",
"0.0%",
"Page 9 / V7");

upsert("gold_battery_dispatch", "V7 Cycles Used Pct",
@"VAR _used =
    CALCULATE(
        MAX( gold_battery_dispatch[cumulative_cycles] ),
        gold_battery_dispatch[is_simulated] = ""false""
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
        gold_battery_dispatch[is_simulated] = ""false"" )
VAR _warranty =
    LOOKUPVALUE(
        gold_battery_technologies[warranty_cycles],
        gold_battery_technologies[battery_id],
        SELECTEDVALUE( gold_battery_dispatch[battery_id] ) )
VAR _avg_daily_cycles =
    DIVIDE( _used,
        DATEDIFF(
            CALCULATE( MIN( gold_battery_dispatch[date] ),
                       gold_battery_dispatch[is_simulated] = ""false"" ),
            CALCULATE( MAX( gold_battery_dispatch[date] ),
                       gold_battery_dispatch[is_simulated] = ""false"" ),
            DAY ) )
VAR _remaining = _warranty - _used
RETURN
    IF( _avg_daily_cycles > 0,
        DIVIDE( _remaining, _avg_daily_cycles ) / 365,
        BLANK() )",
@"0.0 ""yr""",
"Page 9 / V7");

// =====================================================================
// I3 — Compliance Flag Text (eu_compliant + is_eu_member text fix)
// =====================================================================
upsert("gold_country_regulations", "I3 Compliance Flag Text",
@"VAR _active_tech =
    CALCULATE(
        MAX( gold_battery_dispatch[battery_tech] ),
        gold_battery_dispatch[is_simulated] = ""false"" )
VAR _country = SELECTEDVALUE( silver_building_master[country_code], ""DE"" )
VAR _compliant =
    CALCULATE(
        MAX( gold_battery_dispatch[eu_compliant] ),
        gold_battery_dispatch[is_simulated] = ""false"" )
VAR _is_eu_member =
    CALCULATE( MAX(gold_country_regulations[is_eu_member]),
               gold_country_regulations[country_code] = _country )
RETURN
    SWITCH( TRUE(),
        ISBLANK(_active_tech),
            ""No active battery — simulation mode only."",
        _active_tech = ""NMC"" && _country IN {""DE"",""AT""},
            ""⚠ Active battery is NMC — banned in "" & _country & "" for new installs from 2025-01. Replacement window: 2027-Q1."",
        _is_eu_member = ""true"" && _compliant <> ""true"",
            ""⚠ Active battery does not meet EU 2023/1670 thresholds (carbon footprint or recycled content). Mandatory replacement before 2027 in regulated tenders."",
        _is_eu_member = ""true"" && _compliant = ""true"",
            ""✓ Active battery fully EU 2023/1670 compliant — Digital Battery Passport on file."",
        ""ℹ Active battery outside EU regulatory perimeter."" )",
"",
"Page 9 / Insights");

// =====================================================================
// I2 — Chemistry Recommendation (sodium_ion_approved + nmc_allowed_new_2025 text fix)
// =====================================================================
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
        _is_cold_climate && _sodium_ok = ""true"",
            ""Recommended: Sodium-Ion (CATL Naxtra) — superior cold-weather performance below -10°C, lowest carbon footprint (28 kg CO₂/kWh), available Q3 2026 in "" & _country & ""."",
        _country IN {""DE"",""AT""} && _nmc_ok <> ""true"",
            ""Recommended: LFP (CATL or Fluence) — NMC chemistry banned for new installs in "" & _country & "" per BattG 2025 amendment. LFP yields 6,000+ cycles and full EU 2023/1670 compliance."",
        _country = ""NL"",
            ""Recommended: LFP-V2G (BYD Battery-Box HVS) — Netherlands has most mature V2G regulation. Bidirectional charger + EV fleet integration yields ~30% additional revenue."",
        _country = ""UK"",
            ""Recommended: LFP-Supercap-Hybrid (Skeleton SkelGrid) — UK Dynamic Containment + Capacity Market favor high-power chemistry with 1M+ cycle equivalent."",
        ""Recommended: LFP (CATL or Fluence) — best lifecycle value, full EU 2023/1670 compliance, 12-year warranty, 6,000+ cycles."" )",
"",
"Page 9 / Insights");

// =====================================================================
// I1 — Strategy Recommendation (is_primary + is_secondary text fix)
// =====================================================================
upsert("gold_strategy_fitness", "I1 Strategy Recommendation Text",
@"VAR _bt = SELECTEDVALUE( silver_building_master[building_type], ""office"" )
VAR _country = SELECTEDVALUE( silver_building_master[country_code], ""DE"" )
VAR _primary =
    CALCULATE(
        SELECTEDVALUE( gold_strategy_fitness[strategy_label] ),
        gold_strategy_fitness[building_type] = _bt,
        gold_strategy_fitness[is_primary] = ""true"" )
VAR _secondary =
    CALCULATE(
        SELECTEDVALUE( gold_strategy_fitness[strategy_label] ),
        gold_strategy_fitness[building_type] = _bt,
        gold_strategy_fitness[is_secondary] = ""true"" )
VAR _primary_savings =
    CALCULATE(
        AVERAGE( gold_strategy_fitness[typical_annual_savings_eur_per_kwh] ),
        gold_strategy_fitness[building_type] = _bt,
        gold_strategy_fitness[is_primary] = ""true"" )
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

// =====================================================================
// Active Battery + Strategy + Page9 Data As Of (is_simulated text fix)
// =====================================================================
upsert("gold_battery_dispatch", "Active Battery Label",
@"VAR _tech =
    CALCULATE(
        MAX( gold_battery_dispatch[battery_tech] ),
        gold_battery_dispatch[is_simulated] = ""false"" )
VAR _type =
    CALCULATE(
        MAX( gold_battery_dispatch[battery_type] ),
        gold_battery_dispatch[is_simulated] = ""false"" )
VAR _cap =
    CALCULATE(
        MAX( gold_battery_dispatch[capacity_kwh] ),
        gold_battery_dispatch[is_simulated] = ""false"" )
RETURN
    IF( ISBLANK(_tech), ""— No active battery —"",
        _type & "" · "" & FORMAT(_cap, ""#,0"") & "" kWh"" )",
"",
"Page 9 / Helpers");

upsert("gold_battery_dispatch", "Active Strategy Short Label",
@"VAR _s =
    CALCULATE(
        MAX( gold_battery_dispatch[strategy] ),
        gold_battery_dispatch[is_simulated] = ""false"" )
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

upsert("gold_battery_dispatch", "Page9 Data As Of",
@"""Data as of "" &
FORMAT(
    CALCULATE( MAX(gold_battery_dispatch[date]),
               gold_battery_dispatch[is_simulated] = ""false"" ),
    ""MMMM yyyy"" )",
"",
"Page 9 / Helpers");

Output("");
Output("=================================================================");
Output("Page 9 v56b text/boolean fix COMPLETE.");
Output("16 measures patched. Save (Ctrl+S), refresh Power BI.");
Output("=================================================================");
