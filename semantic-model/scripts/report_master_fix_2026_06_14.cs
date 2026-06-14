// =============================================================================
// REPORT MASTER FIX v2 — 2026-06-14  (Tabular Editor 2 C# Script — paste once, F5)
// =============================================================================
// Two fixes in one paste:
//  (1) VALUE: pin every absolute gold_ghg_scope measure to ONE reporting year so
//      multi-year data stops being summed. Smart year = the latest year with the
//      MOST data = latest COMPLETE year (so the partial current year, e.g. 2026
//      ending mid-June which read far too low, is skipped on cards). A trend visual
//      with reporting_year on its axis still shows each year correctly.
//  (2) FORMAT: give each of these measures a clean "#,##0.0" format string so the
//      Scope-2 chart / trend stop showing raw floats like 34353.263600000006.
// Run -> Save -> Refresh. Frankfurt DC should read ~681 (last full year), not 148.
// =============================================================================

int _fixed = 0, _missing = 0;
System.Action<string,string,string> Pin = (name, dax, fmt) => {
    var m = Model.AllMeasures.FirstOrDefault(x => x.Name == name);
    if (m == null) { _missing++; Info("MISSING MEASURE (skipped): " + name); return; }
    m.Expression = dax;
    if (fmt != "") m.FormatString = fmt;
    _fixed++;
};

Pin(@"Scope 1 Diesel tCO2e", @"VAR _years = ADDCOLUMNS ( VALUES ( gold_ghg_scope[reporting_year] ), ""@n"", CALCULATE ( COUNTROWS ( gold_ghg_scope ) ) )
VAR _maxN = MAXX ( _years, [@n] )
VAR _yr = MAXX ( FILTER ( _years, [@n] = _maxN ), gold_ghg_scope[reporting_year] )
RETURN
CALCULATE ( SUM ( gold_ghg_scope[scope1_diesel_tco2] ), gold_ghg_scope[reporting_year] = _yr )", "#,##0.0");
Pin(@"Scope 1 Gas tCO2e", @"VAR _years = ADDCOLUMNS ( VALUES ( gold_ghg_scope[reporting_year] ), ""@n"", CALCULATE ( COUNTROWS ( gold_ghg_scope ) ) )
VAR _maxN = MAXX ( _years, [@n] )
VAR _yr = MAXX ( FILTER ( _years, [@n] = _maxN ), gold_ghg_scope[reporting_year] )
RETURN
CALCULATE ( SUM ( gold_ghg_scope[scope1_gas_tco2] ), gold_ghg_scope[reporting_year] = _yr )", "#,##0.0");
Pin(@"Scope 1 Refrigerant tCO2e", @"VAR _years = ADDCOLUMNS ( VALUES ( gold_ghg_scope[reporting_year] ), ""@n"", CALCULATE ( COUNTROWS ( gold_ghg_scope ) ) )
VAR _maxN = MAXX ( _years, [@n] )
VAR _yr = MAXX ( FILTER ( _years, [@n] = _maxN ), gold_ghg_scope[reporting_year] )
RETURN
CALCULATE ( SUM ( gold_ghg_scope[scope1_refrigerant_tco2] ), gold_ghg_scope[reporting_year] = _yr )", "#,##0.0");
Pin(@"Scope 1 Total tCO2e", @"VAR _years = ADDCOLUMNS ( VALUES ( gold_ghg_scope[reporting_year] ), ""@n"", CALCULATE ( COUNTROWS ( gold_ghg_scope ) ) )
VAR _maxN = MAXX ( _years, [@n] )
VAR _yr = MAXX ( FILTER ( _years, [@n] = _maxN ), gold_ghg_scope[reporting_year] )
RETURN
CALCULATE ( SUM ( gold_ghg_scope[scope1_total_tco2] ), gold_ghg_scope[reporting_year] = _yr )", "#,##0.0");
Pin(@"Scope 1 tCO2", @"VAR _years = ADDCOLUMNS ( VALUES ( gold_ghg_scope[reporting_year] ), ""@n"", CALCULATE ( COUNTROWS ( gold_ghg_scope ) ) )
VAR _maxN = MAXX ( _years, [@n] )
VAR _yr = MAXX ( FILTER ( _years, [@n] = _maxN ), gold_ghg_scope[reporting_year] )
RETURN
CALCULATE ( SUM ( gold_ghg_scope[scope1_total_tco2] ), gold_ghg_scope[reporting_year] = _yr )", "#,##0.0");
Pin(@"Scope 2 Location tCO2", @"VAR _years = ADDCOLUMNS ( VALUES ( gold_ghg_scope[reporting_year] ), ""@n"", CALCULATE ( COUNTROWS ( gold_ghg_scope ) ) )
VAR _maxN = MAXX ( _years, [@n] )
VAR _yr = MAXX ( FILTER ( _years, [@n] = _maxN ), gold_ghg_scope[reporting_year] )
RETURN
CALCULATE ( SUM ( gold_ghg_scope[scope2_location_tco2] ), gold_ghg_scope[reporting_year] = _yr )", "#,##0.0");
Pin(@"Scope 2 Location tCO2e", @"VAR _years = ADDCOLUMNS ( VALUES ( gold_ghg_scope[reporting_year] ), ""@n"", CALCULATE ( COUNTROWS ( gold_ghg_scope ) ) )
VAR _maxN = MAXX ( _years, [@n] )
VAR _yr = MAXX ( FILTER ( _years, [@n] = _maxN ), gold_ghg_scope[reporting_year] )
RETURN
CALCULATE ( SUM ( gold_ghg_scope[scope2_location_tco2] ), gold_ghg_scope[reporting_year] = _yr )", "#,##0.0");
Pin(@"Scope 2 Market tCO2e", @"VAR _years = ADDCOLUMNS ( VALUES ( gold_ghg_scope[reporting_year] ), ""@n"", CALCULATE ( COUNTROWS ( gold_ghg_scope ) ) )
VAR _maxN = MAXX ( _years, [@n] )
VAR _yr = MAXX ( FILTER ( _years, [@n] = _maxN ), gold_ghg_scope[reporting_year] )
RETURN
CALCULATE ( SUM ( gold_ghg_scope[scope2_market_tco2] ), gold_ghg_scope[reporting_year] = _yr )", "#,##0.0");
Pin(@"Scope 3 Cat1 Embodied tCO2e", @"VAR _years = ADDCOLUMNS ( VALUES ( gold_ghg_scope[reporting_year] ), ""@n"", CALCULATE ( COUNTROWS ( gold_ghg_scope ) ) )
VAR _maxN = MAXX ( _years, [@n] )
VAR _yr = MAXX ( FILTER ( _years, [@n] = _maxN ), gold_ghg_scope[reporting_year] )
RETURN
CALCULATE ( SUM ( gold_ghg_scope[scope3_cat1_embodied_tco2] ), gold_ghg_scope[reporting_year] = _yr )", "#,##0.0");
Pin(@"Scope 3 Cat13 Leased tCO2e", @"VAR _years = ADDCOLUMNS ( VALUES ( gold_ghg_scope[reporting_year] ), ""@n"", CALCULATE ( COUNTROWS ( gold_ghg_scope ) ) )
VAR _maxN = MAXX ( _years, [@n] )
VAR _yr = MAXX ( FILTER ( _years, [@n] = _maxN ), gold_ghg_scope[reporting_year] )
RETURN
CALCULATE ( SUM ( gold_ghg_scope[scope3_cat13_leased_tco2] ), gold_ghg_scope[reporting_year] = _yr )", "#,##0.0");
Pin(@"Scope 3 Cat3 Fuel Energy tCO2e", @"VAR _years = ADDCOLUMNS ( VALUES ( gold_ghg_scope[reporting_year] ), ""@n"", CALCULATE ( COUNTROWS ( gold_ghg_scope ) ) )
VAR _maxN = MAXX ( _years, [@n] )
VAR _yr = MAXX ( FILTER ( _years, [@n] = _maxN ), gold_ghg_scope[reporting_year] )
RETURN
CALCULATE ( SUM ( gold_ghg_scope[scope3_cat3_fuelenergy_tco2] ), gold_ghg_scope[reporting_year] = _yr )", "#,##0.0");
Pin(@"Scope 3 Cat5 Waste tCO2e", @"VAR _years = ADDCOLUMNS ( VALUES ( gold_ghg_scope[reporting_year] ), ""@n"", CALCULATE ( COUNTROWS ( gold_ghg_scope ) ) )
VAR _maxN = MAXX ( _years, [@n] )
VAR _yr = MAXX ( FILTER ( _years, [@n] = _maxN ), gold_ghg_scope[reporting_year] )
RETURN
CALCULATE ( SUM ( gold_ghg_scope[scope3_cat5_waste_tco2] ), gold_ghg_scope[reporting_year] = _yr )", "#,##0.0");
Pin(@"Scope 3 Cat6 Travel tCO2e", @"VAR _years = ADDCOLUMNS ( VALUES ( gold_ghg_scope[reporting_year] ), ""@n"", CALCULATE ( COUNTROWS ( gold_ghg_scope ) ) )
VAR _maxN = MAXX ( _years, [@n] )
VAR _yr = MAXX ( FILTER ( _years, [@n] = _maxN ), gold_ghg_scope[reporting_year] )
RETURN
CALCULATE ( SUM ( gold_ghg_scope[scope3_cat6_travel_tco2] ), gold_ghg_scope[reporting_year] = _yr )", "#,##0.0");
Pin(@"Scope 3 Cat7 Commute tCO2e", @"VAR _years = ADDCOLUMNS ( VALUES ( gold_ghg_scope[reporting_year] ), ""@n"", CALCULATE ( COUNTROWS ( gold_ghg_scope ) ) )
VAR _maxN = MAXX ( _years, [@n] )
VAR _yr = MAXX ( FILTER ( _years, [@n] = _maxN ), gold_ghg_scope[reporting_year] )
RETURN
CALCULATE ( SUM ( gold_ghg_scope[scope3_cat7_commute_tco2] ), gold_ghg_scope[reporting_year] = _yr )", "#,##0.0");
Pin(@"Scope 3 Est tCO2", @"VAR _years = ADDCOLUMNS ( VALUES ( gold_ghg_scope[reporting_year] ), ""@n"", CALCULATE ( COUNTROWS ( gold_ghg_scope ) ) )
VAR _maxN = MAXX ( _years, [@n] )
VAR _yr = MAXX ( FILTER ( _years, [@n] = _maxN ), gold_ghg_scope[reporting_year] )
RETURN
CALCULATE ( SUM ( gold_ghg_scope[scope3_estimated_tco2] ), gold_ghg_scope[reporting_year] = _yr )", "#,##0.0");
Pin(@"Scope 3 Total (est.) tCO2e", @"VAR _years = ADDCOLUMNS ( VALUES ( gold_ghg_scope[reporting_year] ), ""@n"", CALCULATE ( COUNTROWS ( gold_ghg_scope ) ) )
VAR _maxN = MAXX ( _years, [@n] )
VAR _yr = MAXX ( FILTER ( _years, [@n] = _maxN ), gold_ghg_scope[reporting_year] )
RETURN
CALCULATE ( SUM ( gold_ghg_scope[scope3_estimated_tco2] ), gold_ghg_scope[reporting_year] = _yr )", "#,##0.0");
Pin(@"Total GHG Location tCO2e", @"VAR _years = ADDCOLUMNS ( VALUES ( gold_ghg_scope[reporting_year] ), ""@n"", CALCULATE ( COUNTROWS ( gold_ghg_scope ) ) )
VAR _maxN = MAXX ( _years, [@n] )
VAR _yr = MAXX ( FILTER ( _years, [@n] = _maxN ), gold_ghg_scope[reporting_year] )
RETURN
CALCULATE ( SUM ( gold_ghg_scope[total_ghg_location_tco2] ), gold_ghg_scope[reporting_year] = _yr )", "#,##0.0");
Pin(@"Total GHG Market tCO2e", @"VAR _years = ADDCOLUMNS ( VALUES ( gold_ghg_scope[reporting_year] ), ""@n"", CALCULATE ( COUNTROWS ( gold_ghg_scope ) ) )
VAR _maxN = MAXX ( _years, [@n] )
VAR _yr = MAXX ( FILTER ( _years, [@n] = _maxN ), gold_ghg_scope[reporting_year] )
RETURN
CALCULATE ( SUM ( gold_ghg_scope[total_ghg_market_tco2] ), gold_ghg_scope[reporting_year] = _yr )", "#,##0.0");

// --- special: intensity (1 decimal kgCO2/m2) ---
Pin(@"Carbon Intensity S1S2 kgCO2 m2 yr", @"VAR _years = ADDCOLUMNS ( VALUES ( gold_ghg_scope[reporting_year] ), ""@n"", CALCULATE ( COUNTROWS ( gold_ghg_scope ) ) )
VAR _maxN = MAXX ( _years, [@n] )
VAR _yr = MAXX ( FILTER ( _years, [@n] = _maxN ), gold_ghg_scope[reporting_year] )
VAR _s1s2 = CALCULATE ( SUMX ( gold_ghg_scope, gold_ghg_scope[scope1_total_tco2] + gold_ghg_scope[scope2_location_tco2] ), gold_ghg_scope[reporting_year] = _yr )
VAR _area = SUMX ( silver_building_master, silver_building_master[conditioned_area_m2] )
RETURN DIVIDE ( _s1s2 * 1000, _area )", "#,##0.0");

// --- special: scope selector ---
Pin(@"Selected Scope tCO2", @"VAR _years = ADDCOLUMNS ( VALUES ( gold_ghg_scope[reporting_year] ), ""@n"", CALCULATE ( COUNTROWS ( gold_ghg_scope ) ) )
VAR _maxN = MAXX ( _years, [@n] )
VAR _yr = MAXX ( FILTER ( _years, [@n] = _maxN ), gold_ghg_scope[reporting_year] )
RETURN
CALCULATE (
    SWITCH (
        SELECTEDVALUE ( Scope_Category[Scope] ),
        ""Scope 1 - Direct"",      SUM ( gold_ghg_scope[scope1_total_tco2] ),
        ""Scope 2 - Electricity"", SUM ( gold_ghg_scope[scope2_location_tco2] ),
        ""Scope 3 - Indirect"",    SUM ( gold_ghg_scope[scope3_estimated_tco2] ),
        BLANK ()
    ),
    gold_ghg_scope[reporting_year] = _yr
)", "#,##0.0");

Info("GHG year-pin v2 + format complete. Fixed: " + _fixed + "  Missing: " + _missing);
