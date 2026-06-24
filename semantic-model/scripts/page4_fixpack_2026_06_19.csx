// =============================================================================
// page4_fixpack_2026_06_19.csx  —  Tabular Editor (connect to live model, F5)
// =============================================================================
// Page 4 (Forecast & Recommendations) — measure-level fixes.
//
// FIX 1: "Savings Potential (€)" card shows (Blank) for buildings with no
//        CRITICAL recommendation (e.g. B001). The measure summed CRITICAL-only.
//        Redefine as TOTAL achievable saving (all priorities) → never blank,
//        shows the building's full opportunity. (Separate cards already cover
//        critical: "CRITICAL Actions", "Top Critical Saving".)
//
// NO-LINQ. Idempotent. Verify each measure exists before editing.
// =============================================================================

var t = Model.Tables["gold_recommendations"];

// ---- FIX 1: Savings Potential never blank --------------------------------
if (t.Measures.Contains("Savings Potential EUR CRITICAL"))
{
    var m = t.Measures["Savings Potential EUR CRITICAL"];
    m.Expression = "SUM ( gold_recommendations[annual_saving_eur] )";
    Info("FIX 1 OK: 'Savings Potential EUR CRITICAL' -> total annual saving (never blank).");
}
else
{
    Info("FIX 1 SKIP: measure 'Savings Potential EUR CRITICAL' not found.");
}

// ---- NOTE (not auto-fixed): 'Savings Annual Target EUR' = 300000 hardcoded.
// The visible cards show a SCALING goal, so this fixed measure appears UNUSED by
// the live cards. Left untouched to avoid breaking an unseen binding. If a
// dynamic target is wanted later, base it on gold_energy_ledger total cost once
// that table is added to the model (benchmark/gauge step).

Info("page4_fixpack_2026_06_19 done.");
