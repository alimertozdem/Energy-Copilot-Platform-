// =============================================================================
// Energy Copilot Platform — Page 5 v54 INSTALL (Decision-Support Layer)
// File: semantic-model/scripts/page5_v54_install.cs
// Date: 2026-05-19
//
// PURPOSE
//   Sayfa 5'e decision-support katmanı ekler:
//     - 1 UPDATE: Energy per Occupant Goal kWh (portfolio 650 -> 1200)
//     - 4 NEW:    Ghost Load Risk Status, Ghost Load Annual Cost EUR,
//                 Occupied Hours Variance Hours, Occupancy Top Insight
//
// IDEMPOTENT
//   Re-run safe. Measure varsa update edilir, yoksa create edilir.
//
// USAGE
//   1. Power BI Desktop'ta .pbix aç
//   2. External Tools -> Tabular Editor 2
//   3. File -> New Script (veya C# Script tab acik ise icerigi sil)
//   4. Bu dosyayi yapistir
//   5. F5 (Run Script)
//   6. Output: "v54 install complete. Updated: 1, Created: 4"
//   7. Ctrl+S -> Save
//   8. Power BI Desktop'a don -> Home -> Refresh (model refresh)
//   9. Yeni measure'lari card visual'lara bind et (docs/page5_v54_visual_plan.md)
//
// DEPENDENCIES — SELF-CONTAINED
//   - Tables: gold_occupancy_profile, gold_kpi_daily, silver_building_master
//   - Tablodan direkt hesaplar; başka measure'a bağımlı değil
//     (chain dependency yok — 02_dax_measures.dax veya v29 deploy edilmemiş
//     olsa bile çalışır)
//
// NOTE: TE2 nuance — Measure.Table read-only. Home table sadece
//       Table.AddMeasure() ile create anında set edilebilir. Bir measure'ı
//       baska tabloya tasimak icin Delete + Re-create gerekir.
// =============================================================================

const string FOLDER_DECISION = "Page 5 - Decision Support";
const string FOLDER_DENSITY  = "Page 5 - Energy Density";

// ----- TABLE REFERENCES -----
Table tblOcc = null;
Table tblKpi = null;
foreach (var t in Model.Tables)
{
    if (t.Name == "gold_occupancy_profile") tblOcc = t;
    if (t.Name == "gold_kpi_daily")         tblKpi = t;
}
if (tblOcc == null) { Error("Table 'gold_occupancy_profile' bulunamadi."); return; }
if (tblKpi == null) { Error("Table 'gold_kpi_daily' bulunamadi."); return; }

// ----- COUNTERS -----
int updatedCount = 0;
int createdCount = 0;

// ----- UPSERT HELPER -----
// Existing measure varsa expression/format/folder update.
// Yoksa target table'a create. Home table tasima desteklenmez (TE2 limit).
System.Action<Table, string, string, string, string> upsert = (targetTable, name, expression, format, folder) =>
{
    Measure existing = null;
    foreach (var m in Model.AllMeasures)
    {
        if (m.Name == name) { existing = m; break; }
    }

    if (existing != null)
    {
        existing.Expression = expression;
        if (!string.IsNullOrEmpty(format)) existing.FormatString = format;
        if (!string.IsNullOrEmpty(folder)) existing.DisplayFolder = folder;
        Info("UPDATED: " + name + "  (home: " + existing.Table.Name + ")");
        updatedCount++;
    }
    else
    {
        var m = targetTable.AddMeasure(name, expression);
        if (!string.IsNullOrEmpty(format)) m.FormatString = format;
        if (!string.IsNullOrEmpty(folder)) m.DisplayFolder = folder;
        Info("CREATED: " + name + "  (home: " + targetTable.Name + ")");
        createdCount++;
    }
};

Info("=== v54 PAGE 5 INSTALL ===");
Info("");


// ─────────────────────────────────────────────────────────────────────────────
// 1. UPDATE — Energy per Occupant Goal kWh (portfolio default 650 -> 1200)
// ─────────────────────────────────────────────────────────────────────────────

upsert(tblOcc, "Energy per Occupant Goal kWh",
@"VAR _selected_buildings = DISTINCTCOUNT(gold_occupancy_profile[building_id])
VAR _building_type =
    IF(_selected_buildings = 1,
        CALCULATE(
            SELECTEDVALUE(silver_building_master[building_type]),
            TREATAS(VALUES(gold_occupancy_profile[building_id]),
                    silver_building_master[building_id])),
        ""Portfolio"")
RETURN
    SWITCH(TRUE(),
        _building_type = ""Office"",      250,
        _building_type = ""Retail"",      320,
        _building_type = ""Hotel"",       900,
        _building_type = ""Healthcare"", 1100,
        _building_type = ""Education"",   250,
        _building_type = ""Logistics"",  1000,
        1200)",
"#,##0",
FOLDER_DENSITY);


// ─────────────────────────────────────────────────────────────────────────────
// 2a. CREATE — Ghost Load Risk Pct (base measure, self-contained)
// ─────────────────────────────────────────────────────────────────────────────

upsert(tblOcc, "Ghost Load Risk Pct",
@"VAR _after_hours_avg =
    CALCULATE(
        AVERAGE(gold_occupancy_profile[occupancy_probability]),
        gold_occupancy_profile[hour_of_day] >= 20
            || gold_occupancy_profile[hour_of_day] < 7)
VAR _total_avg = AVERAGE(gold_occupancy_profile[occupancy_probability])
RETURN
    IF(NOT ISBLANK(_total_avg) && _total_avg > 0,
       ROUND(DIVIDE(_after_hours_avg, _total_avg) * 100, 1),
       BLANK())",
"0.0",
FOLDER_DECISION);


// ─────────────────────────────────────────────────────────────────────────────
// 2b. CREATE — Ghost Load Risk Status (text label, self-contained)
// ─────────────────────────────────────────────────────────────────────────────

upsert(tblOcc, "Ghost Load Risk Status",
@"VAR _after_hours_avg =
    CALCULATE(
        AVERAGE(gold_occupancy_profile[occupancy_probability]),
        gold_occupancy_profile[hour_of_day] >= 20
            || gold_occupancy_profile[hour_of_day] < 7)
VAR _total_avg = AVERAGE(gold_occupancy_profile[occupancy_probability])
VAR _pct =
    IF(_total_avg > 0,
       DIVIDE(_after_hours_avg, _total_avg) * 100,
       BLANK())
RETURN
    SWITCH(TRUE(),
        ISBLANK(_pct),  ""—"",
        _pct < 20,      ""Efficient"",
        _pct < 35,      ""Review schedule"",
                        ""Critical ghost load"")",
"",
FOLDER_DECISION);


// ─────────────────────────────────────────────────────────────────────────────
// 3. CREATE — Ghost Load Annual Cost EUR (financial impact)
// ─────────────────────────────────────────────────────────────────────────────

upsert(tblKpi, "Ghost Load Annual Cost EUR",
@"VAR _after_hours_avg =
    CALCULATE(
        AVERAGE(gold_occupancy_profile[occupancy_probability]),
        gold_occupancy_profile[hour_of_day] >= 20
            || gold_occupancy_profile[hour_of_day] < 7)
VAR _total_avg = AVERAGE(gold_occupancy_profile[occupancy_probability])
VAR _phantom_pct =
    IF(_total_avg > 0,
       DIVIDE(_after_hours_avg, _total_avg) * 100,
       BLANK())
VAR _annual_kwh = CALCULATE(SUM(gold_kpi_daily[total_consumption_kwh]))
VAR _baseload_factor = 0.20
VAR _eur_per_kwh = 0.20
VAR _wasted_kwh = _annual_kwh * (_phantom_pct / 100) * _baseload_factor
VAR _wasted_eur = _wasted_kwh * _eur_per_kwh
RETURN
    IF(NOT ISBLANK(_wasted_eur) && _wasted_eur > 0,
       ROUND(_wasted_eur, 0),
       BLANK())",
"\"€\"#,##0",
FOLDER_DECISION);


// ─────────────────────────────────────────────────────────────────────────────
// 4. CREATE — Occupied Hours Variance Hours (actual - goal)
// ─────────────────────────────────────────────────────────────────────────────

upsert(tblOcc, "Occupied Hours Variance Hours",
@"VAR _occupied_threshold = 0.30
VAR _occupied_hours_per_week =
    CALCULATE(
        COUNTROWS(gold_occupancy_profile),
        gold_occupancy_profile[occupancy_probability] >= _occupied_threshold)
VAR _actual = DIVIDE(_occupied_hours_per_week, 7)
VAR _selected_buildings = DISTINCTCOUNT(gold_occupancy_profile[building_id])
VAR _building_type =
    IF(_selected_buildings = 1,
        CALCULATE(
            SELECTEDVALUE(silver_building_master[building_type]),
            TREATAS(VALUES(gold_occupancy_profile[building_id]),
                    silver_building_master[building_id])),
        ""Portfolio"")
VAR _goal =
    SWITCH(TRUE(),
        _building_type = ""Office"",       9,
        _building_type = ""Retail"",      12,
        _building_type = ""Hotel"",       18,
        _building_type = ""Healthcare"",  20,
        _building_type = ""Education"",    8,
        _building_type = ""Logistics"",   14,
        10)
RETURN
    IF(NOT ISBLANK(_actual) && _goal > 0,
       ROUND(_actual - _goal, 1),
       BLANK())",
"+0.0;-0.0;0",
FOLDER_DECISION);


// ─────────────────────────────────────────────────────────────────────────────
// 5. CREATE — Occupancy Top Insight (prescriptive text)
// ─────────────────────────────────────────────────────────────────────────────

upsert(tblOcc, "Occupancy Top Insight",
@"VAR _after_hours_avg =
    CALCULATE(
        AVERAGE(gold_occupancy_profile[occupancy_probability]),
        gold_occupancy_profile[hour_of_day] >= 20
            || gold_occupancy_profile[hour_of_day] < 7)
VAR _total_avg = AVERAGE(gold_occupancy_profile[occupancy_probability])
VAR _phantom =
    IF(_total_avg > 0,
       DIVIDE(_after_hours_avg, _total_avg) * 100,
       BLANK())
VAR _hours_variance = [Occupied Hours Variance Hours]
VAR _annual_cost = [Ghost Load Annual Cost EUR]
VAR _cost_text = IF(ISBLANK(_annual_cost), ""n/a"", ""EUR "" & FORMAT(_annual_cost, ""#,##0""))
RETURN
    SWITCH(TRUE(),
        ISBLANK(_phantom),
            ""Insufficient occupancy data. Verify gold_occupancy_profile load (notebook v1.3.0)."",
        _phantom >= 35,
            ""CRITICAL ghost load. Schedule HVAC/lighting off after 20h. "" &
            ""Est. saving: "" & _cost_text & ""/yr. See Page 4 for recommendations."",
        _phantom >= 20,
            ""MODERATE after-hours waste. Review lighting + plug-load scheduling. "" &
            ""Est. saving: "" & _cost_text & ""/yr. See Page 4 for recommendations."",
        NOT ISBLANK(_hours_variance) && _hours_variance < -1.5,
            ""Under-utilized portfolio ("" & FORMAT(_hours_variance, ""0.0"") &
            ""h below goal). Consider tenant mix review or space consolidation."",
        ""Healthy utilization pattern. No immediate action required."")",
"",
FOLDER_DECISION);


// ─────────────────────────────────────────────────────────────────────────────
// COMPLETION REPORT
// ─────────────────────────────────────────────────────────────────────────────

Info("");
Info("=== v54 INSTALL COMPLETE ===");
Info("Updated: " + updatedCount + " measure(s)");
Info("Created: " + createdCount + " measure(s)");
Info("Display folders:");
Info("  - " + FOLDER_DECISION);
Info("  - " + FOLDER_DENSITY);
Info("");
Info("NEXT STEPS:");
Info("  1. Ctrl+S to save model");
Info("  2. Power BI Desktop -> Home -> Refresh");
Info("  3. Bind new measures to Page 5 visuals (see docs/page5_v54_visual_plan.md)");
