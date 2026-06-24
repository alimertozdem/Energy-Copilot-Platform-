// fix_page6_co2_trend_annualize.csx
// Tabular Editor 2 - Advanced Scripting (C# Script tab). NO LINQ. Idempotent.
//
// Creates 3 dedicated annualized measures for the "CO2 Emission Trend (Annual)" chart.
// Each chart series sums CO2 over a calendar year; the current INCOMPLETE year (only a
// few months of data) plunges. These trend measures annualize the partial year
// (x 365/days) ONLY when the context is a SINGLE calendar year with < 330 days of data.
// => a full year is unchanged, and any multi-year / full-range context (cards) keeps
//    factor = 1, so nothing else in the model is affected. Originals are NOT modified.
//
// AFTER RUNNING: in PBI Desktop, rebind the CO2 Emission Trend's 3 Y-series to:
//   Total CO2 Emissions Trend tCO2  (replaces report-level 'Total CO2 Emissions tCO2 Display')
//   Net Carbon Footprint Trend tCO2 (replaces 'Net Carbon Footprint tCO2')
//   Total CO2 Savings Trend tCO2    (replaces 'Total CO2 Savings from Solar tCO2')
//
// HOW TO RUN: External Tools -> Tabular Editor -> C# Script -> paste -> Run (F5) -> Save -> publish.

string head =
@"VAR _minY = YEAR ( CALCULATE ( MIN ( gold_kpi_daily[date] ) ) )
VAR _maxY = YEAR ( CALCULATE ( MAX ( gold_kpi_daily[date] ) ) )
VAR _days = CALCULATE ( DISTINCTCOUNT ( gold_kpi_daily[date] ) )
VAR _factor = IF ( _minY = _maxY && _days > 0 && _days < 330, DIVIDE ( 365.0, _days ), 1 )
RETURN ";

var t = Model.Tables["gold_kpi_daily"];

string[] names = new string[] {
    "Total CO2 Emissions Trend tCO2",
    "Net Carbon Footprint Trend tCO2",
    "Total CO2 Savings Trend tCO2"
};
string[] bases = new string[] {
    "[Total CO2 Emissions tCO2]",
    "[Net Carbon Footprint tCO2]",
    "[Total CO2 Savings from Solar tCO2]"
};

int made = 0;
int updated = 0;
for (int i = 0; i < names.Length; i++)
{
    string expr = head + bases[i] + " * _factor";
    Measure found = null;
    foreach (var m in t.Measures)
    {
        if (m.Name == names[i]) { found = m; }
    }
    if (found == null)
    {
        var nm = t.AddMeasure(names[i], expr);
        nm.FormatString = "#,##0.0";
        nm.DisplayFolder = "Page 6 ESG (v57)";
        made++;
    }
    else
    {
        found.Expression = expr;
        updated++;
    }
}

Info("CO2 trend measures - created: " + made + ", updated: " + updated + " (expected 3 total).");
