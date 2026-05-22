// =====================================================================
// Page 9 v56c — SMART boolean fix (auto-detects column types)
// =====================================================================
// Date    : 2026-05-21
// Problem : Mixed column types — gold_battery_dispatch has BOOL columns
//           (loaded via Notebook 12), but gold_battery_simulation,
//           gold_country_regulations, gold_strategy_fitness have TEXT
//           columns (loaded via Notebook 16 sample-detection that didn't
//           always trigger).
//
//           Cannot use a single comparison style for all measures.
//
// Strategy : Auto-detect each suspect column's DataType and build the
//            correct comparison string:
//              if Boolean -> "= TRUE()"  /  "= FALSE()"
//              if String  -> "= \"true\""  /  "= \"false\""
//            Inject the correct fragment into each measure.
//
// IDEMPOTENT : safe to re-run.
// =====================================================================

System.Func<string, Table> findTable = (string name) => {
    foreach (var tbl in Model.Tables) {
        if (tbl.Name == name) return tbl;
    }
    return null;
};

System.Func<string, string, string> findColumnType = (string tableName, string colName) => {
    var t = findTable(tableName);
    if (t == null) return "MISSING_TABLE";
    foreach (var c in t.Columns) {
        if (c.Name == colName) return c.DataType.ToString();
    }
    return "MISSING_COLUMN";
};

// Returns the DAX comparison fragment for a single suspect column.
// E.g. cmp("gold_battery_dispatch", "is_simulated", false)
//   -> "gold_battery_dispatch[is_simulated] = FALSE()"  if BOOL
//   -> "gold_battery_dispatch[is_simulated] = \"false\""  if TEXT
System.Func<string, string, bool, string> cmp =
    (string tableName, string colName, bool expectedTrue) =>
{
    string typ = findColumnType(tableName, colName);
    string boolLiteral = expectedTrue ? "TRUE()" : "FALSE()";
    string textLiteral = expectedTrue ? "\"true\"" : "\"false\"";
    string lhs = tableName + "[" + colName + "]";
    if (typ == "Boolean") return lhs + " = " + boolLiteral;
    return lhs + " = " + textLiteral;       // default: TEXT
};

// "not equals" variant for non-EU / non-compliant scenarios
System.Func<string, string, bool, string> ncmp =
    (string tableName, string colName, bool expectedTrue) =>
{
    string typ = findColumnType(tableName, colName);
    string boolLiteral = expectedTrue ? "TRUE()" : "FALSE()";
    string textLiteral = expectedTrue ? "\"true\"" : "\"false\"";
    string lhs = tableName + "[" + colName + "]";
    if (typ == "Boolean") return lhs + " <> " + boolLiteral;
    return lhs + " <> " + textLiteral;
};

// upsert helper
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
// PRE-FLIGHT — log all detected column types
// =====================================================================

Output("===== Column type detection =====");
string[,] probes = new string[,] {
    { "gold_battery_dispatch",      "is_simulated"        },
    { "gold_battery_dispatch",      "eu_compliant"        },
    { "gold_battery_simulation",    "is_active_strategy"  },
    { "gold_country_regulations",   "is_eu_member"        },
    { "gold_country_regulations",   "nmc_allowed_new_2025"},
    { "gold_country_regulations",   "sodium_ion_approved" },
    { "gold_country_regulations",   "solid_state_pilot"   },
    { "gold_strategy_fitness",      "is_primary"          },
    { "gold_strategy_fitness",      "is_secondary"        }
};
for (int i = 0; i < probes.GetLength(0); i++) {
    Output(string.Format("  {0,-32} {1,-22} -> {2}",
        probes[i,0], probes[i,1], findColumnType(probes[i,0], probes[i,1])));
}

// Build commonly used comparison fragments
string disp_active   = cmp("gold_battery_dispatch",   "is_simulated",        false);
string sim_active    = cmp("gold_battery_simulation", "is_active_strategy",  true);
string eu_compliant_T = cmp("gold_battery_dispatch",  "eu_compliant",        true);
string eu_compliant_NT = ncmp("gold_battery_dispatch","eu_compliant",        true);
string is_eu_member_T = cmp("gold_country_regulations","is_eu_member",       true);
string is_eu_member_NT = ncmp("gold_country_regulations","is_eu_member",     true);
string nmc_allowed_T = cmp("gold_country_regulations","nmc_allowed_new_2025", true);
string nmc_allowed_NT = ncmp("gold_country_regulations","nmc_allowed_new_2025",true);
string sodium_T      = cmp("gold_country_regulations","sodium_ion_approved", true);
string sodium_NT     = ncmp("gold_country_regulations","sodium_ion_approved",true);
string ss_T          = cmp("gold_country_regulations","solid_state_pilot",   true);
string is_primary_T  = cmp("gold_strategy_fitness",   "is_primary",          true);
string is_secondary_T = cmp("gold_strategy_fitness",  "is_secondary",        true);

Output("");
Output("===== Built comparison fragments =====");
Output("  disp_active        : " + disp_active);
Output("  sim_active         : " + sim_active);
Output("  eu_compliant_T     : " + eu_compliant_T);
Output("  is_eu_member_T     : " + is_eu_member_T);
Output("  nmc_allowed_T      : " + nmc_allowed_T);
Output("");

// =====================================================================
// PATCH measures
// =====================================================================

upsert("gold_battery_dispatch", "C1 Annual Savings EUR",
"VAR _has_active = NOT ISBLANK( CALCULATE( COUNTROWS( gold_battery_dispatch ), " + disp_active + " ) )\n" +
"VAR _annual_savings = CALCULATE( SUM( gold_battery_dispatch[net_savings_eur] ), " + disp_active + ", gold_battery_dispatch[date] >= DATE(YEAR(TODAY())-1, MONTH(TODAY()), DAY(TODAY())) )\n" +
"VAR _fallback_sim = CALCULATE( AVERAGE( gold_battery_simulation[annual_savings_eur] ), " + sim_active + " )\n" +
"RETURN IF( _has_active && NOT ISBLANK(_annual_savings) && _annual_savings > 0, _annual_savings, _fallback_sim )",
"€ #,##0", "Page 9 / KPI");

upsert("gold_battery_simulation", "C2 Payback Years",
"VAR _payback = CALCULATE( AVERAGE( gold_battery_simulation[payback_years] ), " + sim_active + " )\n" +
"RETURN IF( ISBLANK(_payback) || _payback >= 99, BLANK(), ROUND(_payback, 1) )",
"0.0 \"yr\"", "Page 9 / KPI");

upsert("gold_battery_dispatch", "C3 CO2 Avoided Tonnes Annual",
"VAR _co2_kg = CALCULATE( SUM( gold_battery_dispatch[co2_avoided_kg] ), " + disp_active + ", gold_battery_dispatch[date] >= DATE(YEAR(TODAY())-1, MONTH(TODAY()), DAY(TODAY())) )\n" +
"RETURN DIVIDE( _co2_kg, 1000 )",
"#,0.0 \"tCO₂\"", "Page 9 / KPI");

upsert("gold_battery_dispatch", "C4 Round Trip Efficiency Pct",
"VAR _rte = CALCULATE( AVERAGE( gold_battery_dispatch[round_trip_efficiency_percent] ), " + disp_active + " )\n" +
"RETURN DIVIDE( _rte, 100 )",
"0.0%", "Page 9 / KPI");

upsert("gold_battery_simulation", "C5 EU Compliance Status Text",
"VAR _active_tech = CALCULATE( MAX( gold_battery_dispatch[battery_tech] ), " + disp_active + " )\n" +
"VAR _country = SELECTEDVALUE( silver_building_master[country_code], \"DE\" )\n" +
"VAR _is_eu_member = CALCULATE( MAX(gold_country_regulations[is_eu_member]), gold_country_regulations[country_code] = _country )\n" +
"VAR _nmc_allowed_flag = CALCULATE( MAX(gold_country_regulations[nmc_allowed_new_2025]), gold_country_regulations[country_code] = _country )\n" +
"VAR _battery_eu_compliant = CALCULATE( MAX( gold_battery_dispatch[eu_compliant] ), " + disp_active + " )\n" +
"VAR _isEU = _is_eu_member & \"\" = \"true\" || _is_eu_member & \"\" = \"True\" || _is_eu_member & \"\" = \"TRUE\"\n" +
"VAR _nmcOK = _nmc_allowed_flag & \"\" = \"true\" || _nmc_allowed_flag & \"\" = \"True\" || _nmc_allowed_flag & \"\" = \"TRUE\"\n" +
"VAR _isCompliant = _battery_eu_compliant & \"\" = \"true\" || _battery_eu_compliant & \"\" = \"True\" || _battery_eu_compliant & \"\" = \"TRUE\"\n" +
"RETURN SWITCH( TRUE(),\n" +
"    ISBLANK(_active_tech), \"— No active battery\",\n" +
"    _active_tech = \"NMC\" && _country IN {\"DE\",\"AT\"} && NOT _nmcOK, \"❌ NMC banned for new installs in \" & _country,\n" +
"    NOT _isCompliant && _isEU, \"⚠ Non-compliant under EU 2023/1670\",\n" +
"    _isEU && _isCompliant, \"✓ EU 2023/1670 compliant\",\n" +
"    NOT _isEU, \"ℹ Outside EU framework\",\n" +
"    \"ℹ Status unknown\" )",
"", "Page 9 / KPI");

upsert("gold_battery_dispatch", "V4 Monthly Net Savings EUR",
"CALCULATE( SUM( gold_battery_dispatch[net_savings_eur] ), " + disp_active + " )",
"€ #,##0", "Page 9 / V4");

upsert("gold_battery_dispatch", "V4 Monthly CO2 Avoided Kg",
"CALCULATE( SUM( gold_battery_dispatch[co2_avoided_kg] ), " + disp_active + " )",
"#,0 \"kg\"", "Page 9 / V4");

upsert("gold_country_regulations", "V5 Country Chemistry Flag",
"VAR _country = SELECTEDVALUE( gold_country_regulations[country_code] )\n" +
"VAR _chem = SELECTEDVALUE( gold_battery_technologies[battery_type] )\n" +
"VAR _is_eu_raw = CALCULATE( MAX(gold_country_regulations[is_eu_member]), gold_country_regulations[country_code] = _country )\n" +
"VAR _nmc_ok_raw = CALCULATE( MAX(gold_country_regulations[nmc_allowed_new_2025]), gold_country_regulations[country_code] = _country )\n" +
"VAR _sodium_ok_raw = CALCULATE( MAX(gold_country_regulations[sodium_ion_approved]), gold_country_regulations[country_code] = _country )\n" +
"VAR _ss_ok_raw = CALCULATE( MAX(gold_country_regulations[solid_state_pilot]), gold_country_regulations[country_code] = _country )\n" +
"VAR _is_eu = _is_eu_raw & \"\" IN {\"true\",\"True\",\"TRUE\"}\n" +
"VAR _nmc_ok = _nmc_ok_raw & \"\" IN {\"true\",\"True\",\"TRUE\"}\n" +
"VAR _sodium_ok = _sodium_ok_raw & \"\" IN {\"true\",\"True\",\"TRUE\"}\n" +
"VAR _ss_ok = _ss_ok_raw & \"\" IN {\"true\",\"True\",\"TRUE\"}\n" +
"RETURN SWITCH( TRUE(),\n" +
"    ISBLANK(_country) || ISBLANK(_chem), BLANK(),\n" +
"    _chem = \"LFP\", 1,\n" +
"    _chem = \"LFP-V2G\", IF(_is_eu, 1, 0),\n" +
"    _chem = \"LFP-Supercap-Hybrid\", 1,\n" +
"    _chem = \"NMC\" && _nmc_ok, 0,\n" +
"    _chem = \"NMC\" && NOT _nmc_ok, -1,\n" +
"    _chem = \"Second-Life NMC\", IF(_is_eu, 0, -1),\n" +
"    _chem = \"NCA\", 0,\n" +
"    _chem = \"Sodium-Ion\" && _sodium_ok, 1,\n" +
"    _chem = \"Sodium-Ion\" && NOT _sodium_ok, 0,\n" +
"    _chem = \"Solid-State\" && _ss_ok, 1,\n" +
"    _chem = \"Solid-State\", 0,\n" +
"    0 )",
"0", "Page 9 / V5");

upsert("gold_country_regulations", "V5 Country Chemistry Symbol",
"VAR _f = [V5 Country Chemistry Flag]\n" +
"RETURN SWITCH( TRUE(),\n" +
"    ISBLANK(_f), \"—\",\n" +
"    _f = 1, \"✓\",\n" +
"    _f = 0, \"⚠\",\n" +
"    _f = -1, \"✗\",\n" +
"    \"\" )",
"", "Page 9 / V5");

upsert("gold_battery_dispatch", "V7 Current SoH Pct",
"DIVIDE( CALCULATE( AVERAGE( gold_battery_dispatch[battery_health_percent] ), " + disp_active + ", gold_battery_dispatch[date] = MAX( gold_battery_dispatch[date] ) ), 100 )",
"0.0%", "Page 9 / V7");

upsert("gold_battery_dispatch", "V7 Cycles Used Pct",
"VAR _used = CALCULATE( MAX( gold_battery_dispatch[cumulative_cycles] ), " + disp_active + " )\n" +
"VAR _warranty = LOOKUPVALUE( gold_battery_technologies[warranty_cycles], gold_battery_technologies[battery_id], SELECTEDVALUE( gold_battery_dispatch[battery_id] ) )\n" +
"RETURN DIVIDE( _used, _warranty )",
"0.0%", "Page 9 / V7");

upsert("gold_battery_dispatch", "V7 Years Until Replacement",
"VAR _used = CALCULATE( MAX( gold_battery_dispatch[cumulative_cycles] ), " + disp_active + " )\n" +
"VAR _warranty = LOOKUPVALUE( gold_battery_technologies[warranty_cycles], gold_battery_technologies[battery_id], SELECTEDVALUE( gold_battery_dispatch[battery_id] ) )\n" +
"VAR _avg_daily_cycles = DIVIDE( _used, DATEDIFF( CALCULATE( MIN( gold_battery_dispatch[date] ), " + disp_active + " ), CALCULATE( MAX( gold_battery_dispatch[date] ), " + disp_active + " ), DAY ) )\n" +
"VAR _remaining = _warranty - _used\n" +
"RETURN IF( _avg_daily_cycles > 0, DIVIDE( _remaining, _avg_daily_cycles ) / 365, BLANK() )",
"0.0 \"yr\"", "Page 9 / V7");

upsert("gold_strategy_fitness", "I1 Strategy Recommendation Text",
"VAR _bt = SELECTEDVALUE( silver_building_master[building_type], \"office\" )\n" +
"VAR _country = SELECTEDVALUE( silver_building_master[country_code], \"DE\" )\n" +
"VAR _primary = CALCULATE( SELECTEDVALUE( gold_strategy_fitness[strategy_label] ), gold_strategy_fitness[building_type] = _bt, " + is_primary_T + " )\n" +
"VAR _secondary = CALCULATE( SELECTEDVALUE( gold_strategy_fitness[strategy_label] ), gold_strategy_fitness[building_type] = _bt, " + is_secondary_T + " )\n" +
"VAR _primary_savings = CALCULATE( AVERAGE( gold_strategy_fitness[typical_annual_savings_eur_per_kwh] ), gold_strategy_fitness[building_type] = _bt, " + is_primary_T + " )\n" +
"VAR _cap = SELECTEDVALUE( silver_building_master[battery_capacity_kwh], 100 )\n" +
"VAR _est_eur = ROUND( _primary_savings * _cap, -2 )\n" +
"RETURN \"For this \" & _bt & \" building in \" & _country & \", primary strategy: \" & _primary & IF( NOT ISBLANK(_secondary), \" (combined with \" & _secondary & \")\", \"\" ) & \". Estimated annual savings ≈ €\" & FORMAT( _est_eur, \"#,0\" ) & \" (range ±25%).\"",
"", "Page 9 / Insights");

upsert("gold_country_regulations", "I2 Chemistry Recommendation Text",
"VAR _country = SELECTEDVALUE( silver_building_master[country_code], \"DE\" )\n" +
"VAR _is_cold_climate = _country IN {\"FI\",\"NO\",\"SE\",\"DK\",\"AT\"}\n" +
"VAR _nmc_ok_raw = CALCULATE( MAX(gold_country_regulations[nmc_allowed_new_2025]), gold_country_regulations[country_code] = _country )\n" +
"VAR _sodium_ok_raw = CALCULATE( MAX(gold_country_regulations[sodium_ion_approved]), gold_country_regulations[country_code] = _country )\n" +
"VAR _nmc_ok = _nmc_ok_raw & \"\" IN {\"true\",\"True\",\"TRUE\"}\n" +
"VAR _sodium_ok = _sodium_ok_raw & \"\" IN {\"true\",\"True\",\"TRUE\"}\n" +
"RETURN SWITCH( TRUE(),\n" +
"    _is_cold_climate && _sodium_ok, \"Recommended: Sodium-Ion (CATL Naxtra) — superior cold-weather performance below -10°C, lowest carbon footprint (28 kg CO₂/kWh), available Q3 2026 in \" & _country & \".\",\n" +
"    _country IN {\"DE\",\"AT\"} && NOT _nmc_ok, \"Recommended: LFP (CATL or Fluence) — NMC chemistry banned for new installs in \" & _country & \" per BattG 2025 amendment. LFP yields 6,000+ cycles and full EU 2023/1670 compliance.\",\n" +
"    _country = \"NL\", \"Recommended: LFP-V2G (BYD Battery-Box HVS) — Netherlands has most mature V2G regulation. Bidirectional charger + EV fleet integration yields ~30% additional revenue.\",\n" +
"    _country = \"UK\", \"Recommended: LFP-Supercap-Hybrid (Skeleton SkelGrid) — UK Dynamic Containment + Capacity Market favor high-power chemistry with 1M+ cycle equivalent.\",\n" +
"    \"Recommended: LFP (CATL or Fluence) — best lifecycle value, full EU 2023/1670 compliance, 12-year warranty, 6,000+ cycles.\" )",
"", "Page 9 / Insights");

upsert("gold_country_regulations", "I3 Compliance Flag Text",
"VAR _active_tech = CALCULATE( MAX( gold_battery_dispatch[battery_tech] ), " + disp_active + " )\n" +
"VAR _country = SELECTEDVALUE( silver_building_master[country_code], \"DE\" )\n" +
"VAR _compliant_raw = CALCULATE( MAX( gold_battery_dispatch[eu_compliant] ), " + disp_active + " )\n" +
"VAR _is_eu_raw = CALCULATE( MAX(gold_country_regulations[is_eu_member]), gold_country_regulations[country_code] = _country )\n" +
"VAR _isCompliant = _compliant_raw & \"\" IN {\"true\",\"True\",\"TRUE\"}\n" +
"VAR _isEU = _is_eu_raw & \"\" IN {\"true\",\"True\",\"TRUE\"}\n" +
"RETURN SWITCH( TRUE(),\n" +
"    ISBLANK(_active_tech), \"No active battery — simulation mode only.\",\n" +
"    _active_tech = \"NMC\" && _country IN {\"DE\",\"AT\"}, \"⚠ Active battery is NMC — banned in \" & _country & \" for new installs from 2025-01. Replacement window: 2027-Q1.\",\n" +
"    _isEU && NOT _isCompliant, \"⚠ Active battery does not meet EU 2023/1670 thresholds (carbon footprint or recycled content). Mandatory replacement before 2027 in regulated tenders.\",\n" +
"    _isEU && _isCompliant, \"✓ Active battery fully EU 2023/1670 compliant — Digital Battery Passport on file.\",\n" +
"    \"ℹ Active battery outside EU regulatory perimeter.\" )",
"", "Page 9 / Insights");

upsert("gold_battery_dispatch", "I4 Next Action Text",
"VAR _yr_to_replace = [V7 Years Until Replacement]\n" +
"VAR _payback = [C2 Payback Years]\n" +
"RETURN SWITCH( TRUE(),\n" +
"    ISBLANK(_yr_to_replace) && ISBLANK(_payback), \"Run a 12-month dispatch simulation to populate financial metrics.\",\n" +
"    NOT ISBLANK(_yr_to_replace) && _yr_to_replace < 2, \"⚠ Battery cycle headroom < 2 years. Plan replacement procurement now (lead time 8-14 weeks for LFP).\",\n" +
"    NOT ISBLANK(_yr_to_replace) && _yr_to_replace < 5, \"Cycle headroom \" & FORMAT(_yr_to_replace, \"0.0\") & \" years. Schedule mid-life maintenance + warranty audit.\",\n" +
"    NOT ISBLANK(_payback) && _payback < 5, \"✓ Strong investment case (payback < 5 years). Recommend portfolio rollout to similar buildings.\",\n" +
"    \"Battery operating within design envelope. Monitor next mid-life review in 24 months.\" )",
"", "Page 9 / Insights");

upsert("gold_battery_dispatch", "Active Battery Label",
"VAR _tech = CALCULATE( MAX( gold_battery_dispatch[battery_tech] ), " + disp_active + " )\n" +
"VAR _type = CALCULATE( MAX( gold_battery_dispatch[battery_type] ), " + disp_active + " )\n" +
"VAR _cap = CALCULATE( MAX( gold_battery_dispatch[capacity_kwh] ), " + disp_active + " )\n" +
"RETURN IF( ISBLANK(_tech), \"— No active battery —\", _type & \" · \" & FORMAT(_cap, \"#,0\") & \" kWh\" )",
"", "Page 9 / Helpers");

upsert("gold_battery_dispatch", "Active Strategy Short Label",
"VAR _s = CALCULATE( MAX( gold_battery_dispatch[strategy] ), " + disp_active + " )\n" +
"RETURN SWITCH( TRUE(),\n" +
"    ISBLANK(_s), \"— Select strategy —\",\n" +
"    _s = \"self_consumption\", \"● Self-Consumption\",\n" +
"    _s = \"peak_shaving\", \"● Peak-Shaving\",\n" +
"    _s = \"tou\", \"● Time-of-Use\",\n" +
"    _s = \"backup\", \"● Backup + Opportunistic\",\n" +
"    _s = \"frequency_reserve\", \"● Frequency Reserve\",\n" +
"    _s = \"capacity_market\", \"● Capacity Market\",\n" +
"    _s = \"v2g\", \"● V2G Coordination\",\n" +
"    \"● \" & _s )",
"", "Page 9 / Helpers");

upsert("gold_battery_dispatch", "Page9 Data As Of",
"\"Data as of \" & FORMAT( CALCULATE( MAX(gold_battery_dispatch[date]), " + disp_active + " ), \"MMMM yyyy\" )",
"", "Page 9 / Helpers");

Output("");
Output("=================================================================");
Output("Page 9 v56c smart fix COMPLETE. Save (Ctrl+S), refresh Power BI.");
Output("=================================================================");
