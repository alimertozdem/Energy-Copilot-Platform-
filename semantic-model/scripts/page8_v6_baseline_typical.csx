// page8_v6_baseline_typical.csx
// Tabular Editor 2 - C# Script. NO LINQ. Idempotent. Run: F5 -> Ctrl+S -> Refresh.
//
// Problem: the "Latest Day" chart's Baseline line was a flat ~120 kW (the synthetic
// baseline_value, constant for all buildings) far above actual load (~70 kW) -> never
// approached, so "power vs baseline / red = leaking" was meaningless and the C1 card
// traffic-light was always green (false "all good").
//
// Fix: redefine the baseline as the building's OWN TYPICAL load = mean building_kwh
// over all loaded data (REMOVEFILTERS the time columns so it is a flat reference, and
// sensor_location so it stays building-level). Now "above typical = investigate" is a
// real signal, and C1 green/amber/red (p vs b*1.05 / b*1.2) actually fires on spikes.
// LIVE-READY: when streaming arrives, the typical mean updates with the data.
//
// AFTER RUNNING (PBI Desktop): rename the chart legend field "Baseline" -> "Typical"
// (double-click it in the visual's field well), title "Latest Day" -> "Building & HVAC
// Power - recent (kW)", and add Y-axis title "kW".

int n = 0;
foreach (var t in Model.Tables)
{
    foreach (var m in t.Measures)
    {
        if (m.Name == "Realtime Building Baseline kW")
        {
            m.Expression = @"CALCULATE ( AVERAGE ( gold_iot_realtime[reading_value_avg] ), gold_iot_realtime[sensor_type] = ""building_kwh"", REMOVEFILTERS ( gold_iot_realtime[timestamp] ), REMOVEFILTERS ( gold_iot_realtime[hour_bucket] ), REMOVEFILTERS ( gold_iot_realtime[hour_of_day] ), REMOVEFILTERS ( gold_iot_realtime[event_date] ), REMOVEFILTERS ( gold_iot_realtime[sensor_location] ) )";
            m.FormatString = "#,##0.0";
            n++;
        }
    }
}
Info("Realtime Building Baseline kW -> typical mean: " + n + " (expected 1). Ctrl+S + Refresh, then relabel legend/title in PBI Desktop.");
