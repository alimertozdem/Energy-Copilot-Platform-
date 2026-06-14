// =============================================================================
// FIX — Page 9 battery "Payback Years" scenario table showing 230.6
// Tabular Editor 2 C# Script — paste once, F5, Save, Refresh.
// =============================================================================
// The scenario TABLE uses [V3 Payback Years] = AVERAGE(payback_years) straight off
// the column, with no cap. gold_battery_simulation still holds the OLD uncapped
// value (notebook 14 hasn't been re-run), so an uneconomic scenario reads 230.6.
// This caps the DISPLAY at 25 so the table can't show an absurd payback. (The card
// [C2 Payback Years] already caps, which is why it reads a sane 1.6.)
//
// PROPER source fix: re-run notebooks/simulation/14_gold_battery_simulation_v2.py
// in Fabric — it caps payback at 25 AND caps IRR at 35% (IRR_DISPLAY_CAP). This DAX
// cap is the safe stop-gap until then.
// =============================================================================

var m = Model.AllMeasures.FirstOrDefault(x => x.Name == "V3 Payback Years");
if (m == null) { Info("Measure 'V3 Payback Years' not found."); }
else {
    m.Expression =
@"VAR _p = AVERAGE ( gold_battery_simulation[payback_years] )
RETURN
    IF ( ISBLANK ( _p ), BLANK (), MIN ( _p, 25 ) )";
    m.FormatString = "0.0";
    Info("V3 Payback Years capped at 25.");
}
