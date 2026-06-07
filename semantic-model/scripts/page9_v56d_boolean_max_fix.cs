// =====================================================================
// Page 9 v56d — Boolean MAX fix
// =====================================================================
// Date    : 2026-05-21
// Problem : DAX MAX() cannot work with Boolean values. After Notebook
//           16b loaded gold_country_regulations and gold_strategy_fitness
//           with proper Boolean casting, measures using MAX(boolCol) fail
//           with "The function MAX cannot work with values of type Boolean".
// Fix     : Replace MAX(boolCol) with SELECTEDVALUE(boolCol) since these
//           queries filter to a single row anyway (e.g. country_code = _country).
//           Also replace text comparisons (= "true") with Boolean comparisons
//           (= TRUE()) for now-Boolean columns.
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
// C5 EU Compliance Status Text — uses SELECTEDVALUE for Boolean
// =====================================================================
upsert("gold_battery_simulation", "C5 EU Compliance Status Text",
@"VAR _active_tech =
    CALCULATE(
        MAX( gold_battery_dispatch[battery_tech] ),
        gold_battery_dispatch[is_simulated] = FALSE()
    )
VAR _country = SELECTEDVALUE( silver_building_master[country_code], ""DE"" )
VAR _is_eu_member =
    CALCULATE( SELECTEDVALUE(gold_country_regulations[is_eu_member]),
               gold_country_regulations[country_code] = _country )
VAR _nmc_allowed =
    CALCULATE( SELECTEDVALUE(gold_country_regulations[nmc_allowed_new_2025]),
               gold_country_regulations[country_code] = _country )
VAR _battery_eu_compliant =
    CALCULATE(
        SELECTEDVALUE( gold_battery_dispatch[eu_compliant] ),
        gold_battery_dispatch[is_simulated] = FALSE()
    )
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

// =====================================================================
// V5 Country Chemistry Flag — SELECTEDVALUE for Boolean
// =====================================================================
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

// =====================================================================
// I2 Chemistry Recommendation Text
// =====================================================================
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
            ""Sodium-Ion (CATL Naxtra) — superior cold-weather performance below -10C, lowest carbon footprint (28 kg CO2/kWh), available Q3 2026 in "" & _country & ""."",
        _country IN {""DE"",""AT""} && _nmc_ok = FALSE(),
            ""LFP (CATL or Fluence) — NMC chemistry banned for new installs in "" & _country & "" per BattG 2025. LFP yields 6000+ cycles and full EU 2023/1542 compliance."",
        _country = ""NL"",
            ""LFP-V2G (BYD Battery-Box HVS) — Netherlands has most mature V2G regulation. Bidirectional charger + EV fleet integration yields ~30% additional revenue."",
        _country = ""UK"",
            ""LFP-Supercap-Hybrid (Skeleton SkelGrid) — UK Dynamic Containment + Capacity Market favor high-power chemistry with 1M+ cycle equivalent."",
        ""LFP (CATL or Fluence) — best lifecycle value, full EU 2023/1542 compliance, 12-year warranty, 6000+ cycles."" )",
"", "Page 9 / Insights");

// =====================================================================
// I3 Compliance Flag Text
// =====================================================================
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
            ""Active battery does not meet EU 2023/1542 thresholds (carbon footprint or recycled content). Mandatory replacement before 2027 in regulated tenders."",
        _is_eu_member = TRUE() && _compliant = TRUE(),
            ""Active battery fully EU 2023/1542 compliant — Digital Battery Passport on file."",
        ""Active battery outside EU regulatory perimeter."" )",
"", "Page 9 / Insights");

// =====================================================================
// I1 Strategy Recommendation Text — Boolean comparison for is_primary/secondary
// =====================================================================
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

Output("Page 9 v56d Boolean MAX fix COMPLETE. Save (Ctrl+S), refresh Power BI.");
