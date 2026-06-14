// =============================================================================
// FIX — Page 1 "Avg EUI" shown per-day (5.07) with an absurd -1323% vs a generic
// 0.27 goal. Two new measures: annual EUI (industry-standard unit) + a building-
// type-aware annual target so the variance is meaningful.
// Tabular Editor 2 C# Script — paste once, F5, Save.
// =============================================================================
// AFTER running: on the Page-1 EUI card, swap the Value field to
// [Avg EUI Annual kWh m2 yr] and the goal/target to [EUI Target Annual kWh m2 yr],
// and change the visual TITLE from "(kWh/m²/day)" to "(kWh/m²/yr)" (title is a
// visual property, can't be set from DAX).
//
// PROPOSED type benchmarks (kWh/m²/yr) — ENERGY REVIEW NEEDED (Mert): rough EU
// operational-EUI bands. A datacenter is ~1700 (very intensive), an office ~130.
// Tune the numbers in the SWITCH below to your own benchmarks.
// =============================================================================

var t = Model.Tables.FirstOrDefault(x => x.Name == "gold_kpi_daily");
if (t == null) { Info("ABORT: gold_kpi_daily not found."); return; }

// 1) Annual EUI = the existing per-day area-weighted EUI x 365.25
{
    var name = "Avg EUI Annual kWh m2 yr";
    var m = Model.AllMeasures.FirstOrDefault(x => x.Name == name) ?? t.AddMeasure(name);
    m.Expression = "[Avg EUI Area-Weighted (kWh/m2/day)] * 365.25";
    m.FormatString = "#,##0";
    m.DisplayFolder = "EUI";
}

// 2) Building-type-aware annual target (area-weighted across the visible buildings,
//    so it works for a single selected building AND the whole portfolio).
{
    var name = "EUI Target Annual kWh m2 yr";
    var m = Model.AllMeasures.FirstOrDefault(x => x.Name == name) ?? t.AddMeasure(name);
    m.Expression =
@"VAR _benchOf =
    // per-building annual EUI benchmark (kWh/m2/yr) by building_type
    SUMX (
        VALUES ( silver_building_master[building_id] ),
        VAR _bt = LOWER ( CALCULATE ( SELECTEDVALUE ( silver_building_master[building_type] ) ) )
        VAR _area = CALCULATE ( SUM ( silver_building_master[conditioned_area_m2] ) )
        VAR _b =
            SWITCH (
                TRUE (),
                CONTAINSSTRING ( _bt, ""data"" ),       1700,
                CONTAINSSTRING ( _bt, ""health"" ),      300,
                CONTAINSSTRING ( _bt, ""hospital"" ),    300,
                CONTAINSSTRING ( _bt, ""lab"" ),         400,
                CONTAINSSTRING ( _bt, ""hotel"" ),       240,
                CONTAINSSTRING ( _bt, ""logistic"" ),    90,
                CONTAINSSTRING ( _bt, ""warehouse"" ),   90,
                CONTAINSSTRING ( _bt, ""educat"" ),      120,
                CONTAINSSTRING ( _bt, ""office"" ),      130,
                CONTAINSSTRING ( _bt, ""residential"" ), 100,
                150   // default
            )
        RETURN _area * _b
    )
VAR _area = SUMX ( VALUES ( silver_building_master[building_id] ),
                   CALCULATE ( SUM ( silver_building_master[conditioned_area_m2] ) ) )
RETURN
    DIVIDE ( _benchOf, _area )";
    m.FormatString = "#,##0";
    m.DisplayFolder = "EUI";
}

// 3) Variance vs the type-aware target (use this for the card's "-x%" caption).
{
    var name = "EUI vs Target Pct";
    var m = Model.AllMeasures.FirstOrDefault(x => x.Name == name) ?? t.AddMeasure(name);
    m.Expression =
@"VAR _e = [Avg EUI Annual kWh m2 yr]
VAR _g = [EUI Target Annual kWh m2 yr]
RETURN IF ( _g > 0, DIVIDE ( _e - _g, _g ), BLANK () )";
    m.FormatString = "+0.0%;-0.0%;0.0%";
    m.DisplayFolder = "EUI";
}

Info("EUI annual + type-aware target + variance created. Rebind the Page-1 card + edit its title to (kWh/m²/yr).");
