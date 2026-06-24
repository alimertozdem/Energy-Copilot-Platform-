// fix_page5_ghost_gate.csx
// Tabular Editor 2 - Advanced Scripting (C# Script tab). NO LINQ.
//
// APPROVED FIX (Mert, 2026-06-21, "gate" option):
//   Ghost-load verdict / % / € are shown ONLY for a single selected building.
//   At portfolio (>1 building) they blank out -> "Assess at building level".
//   This kills the false portfolio €323k that counted the 24/7 hospital's
//   legitimate after-hours baseload as waste. Building-level logic is unchanged
//   (Frankfurt/Healthcare -> "Efficient" still correct).
//
// Also: deletes the junk empty measure named "Measure" on gold_occupancy_profile.
//
// NOT touched here (separate items):
//   - Report-level cards (e.g. "After-Hours Activity Share %" flat goal) -> PBI Desktop
//   - Data_Center/Lab 24/7 threshold (energy assumption, pending approval; B009 has no profile yet)
//   - Duplicate "...Headcount ...Calc" twins (visual-binding risk; confirm first)
//
// HOW TO RUN: open the .pbix you publish from -> External Tools -> Tabular Editor
//   -> C# Script tab -> paste -> Run (F5) -> Save -> republish.

string daxPct =
@"VAR _selected_buildings = DISTINCTCOUNT ( gold_occupancy_profile[building_id] )
VAR _after_hours_avg =
    CALCULATE (
        AVERAGE ( gold_occupancy_profile[occupancy_probability] ),
        gold_occupancy_profile[hour_of_day] >= 20
            || gold_occupancy_profile[hour_of_day] < 7
    )
VAR _total_avg = AVERAGE ( gold_occupancy_profile[occupancy_probability] )
RETURN
    IF (
        _selected_buildings <> 1,
        BLANK (),
        IF (
            NOT ISBLANK ( _total_avg ) && _total_avg > 0,
            ROUND ( DIVIDE ( _after_hours_avg, _total_avg ) * 100, 1 ),
            BLANK ()
        )
    )";

string daxStatus =
@"VAR _after_hours_avg =
    CALCULATE (
        AVERAGE ( gold_occupancy_profile[occupancy_probability] ),
        gold_occupancy_profile[hour_of_day] >= 20
            || gold_occupancy_profile[hour_of_day] < 7
    )
VAR _total_avg = AVERAGE ( gold_occupancy_profile[occupancy_probability] )
VAR _pct =
    IF ( _total_avg > 0, DIVIDE ( _after_hours_avg, _total_avg ) * 100, BLANK () )
VAR _selected_buildings = DISTINCTCOUNT ( gold_occupancy_profile[building_id] )
VAR _building_type =
    IF (
        _selected_buildings = 1,
        CALCULATE (
            SELECTEDVALUE ( silver_building_master[building_type] ),
            TREATAS ( VALUES ( gold_occupancy_profile[building_id] ), silver_building_master[building_id] )
        ),
        ""Portfolio""
    )
VAR _critical_threshold =
    SWITCH (
        TRUE (),
        _building_type IN { ""Hotel"", ""Healthcare"" }, 130,
        _building_type = ""Logistics"", 60,
        35
    )
VAR _review_threshold = _critical_threshold * 0.6
RETURN
    SWITCH (
        TRUE (),
        _selected_buildings <> 1, ""Assess at building level"",
        ISBLANK ( _pct ), ""—"",
        _pct < _review_threshold, ""Efficient"",
        _pct < _critical_threshold, ""Review schedule"",
        ""Critical ghost load""
    )";

string daxCost =
@"VAR _after_hours_avg =
    CALCULATE (
        AVERAGE ( gold_occupancy_profile[occupancy_probability] ),
        gold_occupancy_profile[hour_of_day] >= 20
            || gold_occupancy_profile[hour_of_day] < 7
    )
VAR _total_avg = AVERAGE ( gold_occupancy_profile[occupancy_probability] )
VAR _phantom_pct =
    IF ( _total_avg > 0, DIVIDE ( _after_hours_avg, _total_avg ) * 100, BLANK () )
VAR _selected_buildings = DISTINCTCOUNT ( gold_occupancy_profile[building_id] )
VAR _building_type =
    IF (
        _selected_buildings = 1,
        CALCULATE (
            SELECTEDVALUE ( silver_building_master[building_type] ),
            TREATAS ( VALUES ( gold_occupancy_profile[building_id] ), silver_building_master[building_id] )
        ),
        ""Portfolio""
    )
VAR _critical_threshold =
    SWITCH (
        TRUE (),
        _building_type IN { ""Hotel"", ""Healthcare"" }, 130,
        _building_type = ""Logistics"", 60,
        35
    )
VAR _annual_kwh = CALCULATE ( SUM ( gold_kpi_daily[total_consumption_kwh] ) )
VAR _baseload_factor = 0.20
VAR _eur_per_kwh = 0.20
VAR _excess_pct = MAX ( _phantom_pct - _critical_threshold, 0 )
VAR _wasted_kwh = _annual_kwh * ( _excess_pct / 100 ) * _baseload_factor
VAR _wasted_eur = _wasted_kwh * _eur_per_kwh
RETURN
    IF (
        _selected_buildings = 1
            && NOT ISBLANK ( _phantom_pct )
            && _phantom_pct >= _critical_threshold
            && _wasted_eur > 0,
        ROUND ( _wasted_eur, 0 ),
        BLANK ()
    )";

string daxInsight =
@"VAR _after_hours_avg =
    CALCULATE (
        AVERAGE ( gold_occupancy_profile[occupancy_probability] ),
        gold_occupancy_profile[hour_of_day] >= 20
            || gold_occupancy_profile[hour_of_day] < 7
    )
VAR _total_avg = AVERAGE ( gold_occupancy_profile[occupancy_probability] )
VAR _phantom =
    IF ( _total_avg > 0, DIVIDE ( _after_hours_avg, _total_avg ) * 100, BLANK () )
VAR _selected_buildings = DISTINCTCOUNT ( gold_occupancy_profile[building_id] )
VAR _building_type =
    IF (
        _selected_buildings = 1,
        CALCULATE (
            SELECTEDVALUE ( silver_building_master[building_type] ),
            TREATAS ( VALUES ( gold_occupancy_profile[building_id] ), silver_building_master[building_id] )
        ),
        ""Portfolio""
    )
VAR _is_24_7 = _building_type IN { ""Hotel"", ""Healthcare"" }
VAR _critical_threshold =
    SWITCH (
        TRUE (),
        _is_24_7, 130,
        _building_type = ""Logistics"", 60,
        35
    )
VAR _hours_variance = [Occupied Hours Variance Hours]
VAR _annual_cost = [Ghost Load Annual Cost EUR]
VAR _cost_text =
    IF ( ISBLANK ( _annual_cost ), ""n/a"", ""EUR "" & FORMAT ( _annual_cost, ""#,##0"" ) )
RETURN
    SWITCH (
        TRUE (),
        _selected_buildings <> 1,
            ""Select a single building to assess ghost-load. Portfolio rollup is not shown."",
        ISBLANK ( _phantom ),
            ""Insufficient occupancy data. Verify gold_occupancy_profile load."",
        _is_24_7 && _phantom < _critical_threshold,
            ""Normal 24/7 operation profile. After-hours activity is expected for "" & _building_type & "" buildings. No ghost-load concern."",
        _phantom >= _critical_threshold,
            ""CRITICAL ghost load. Schedule HVAC/lighting off after 20h. Est. saving: "" & _cost_text & ""/yr. See Page 4 for recommendations."",
        _phantom >= _critical_threshold * 0.6,
            ""MODERATE after-hours waste. Review lighting + plug-load scheduling. See Page 4 for recommendations."",
        NOT ISBLANK ( _hours_variance ) && _hours_variance < -1.5,
            ""Under-utilized portfolio ("" & FORMAT ( _hours_variance, ""0.0"" ) & ""h below goal). Consider tenant mix review or space consolidation."",
        ""Healthy utilization pattern. No immediate action required.""
    )";

int updated = 0;
foreach (var m in Model.AllMeasures)
{
    if (m.Name == "Ghost Load Risk Pct") { m.Expression = daxPct; updated++; }
    else if (m.Name == "Ghost Load Risk Status") { m.Expression = daxStatus; updated++; }
    else if (m.Name == "Ghost Load Annual Cost EUR") { m.Expression = daxCost; updated++; }
    else if (m.Name == "Occupancy Top Insight") { m.Expression = daxInsight; updated++; }
}

// Remove the junk empty measure literally named "Measure" on gold_occupancy_profile
Measure junk = null;
foreach (var m in Model.AllMeasures)
{
    if (m.Name == "Measure" && m.Table.Name == "gold_occupancy_profile") { junk = m; }
}
if (junk != null) { junk.Delete(); }

Info("Ghost measures updated: " + updated + " (expected 4). Junk 'Measure' removed: " + (junk != null));
