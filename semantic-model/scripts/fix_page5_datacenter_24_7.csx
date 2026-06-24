// fix_page5_datacenter_24_7.csx
// Tabular Editor 2 - Advanced Scripting (C# Script tab). NO LINQ. Idempotent.
//
// Adds "Data_Center" to the 24/7 ghost-load threshold set (alongside Hotel/Healthcare),
// so a data centre's legitimate ~constant 24/7 baseload is NOT flagged as ghost load
// once B009's occupancy profile is loaded.
//
// ENERGY ASSUMPTION (veto-able): a data centre runs ~constant around the clock; its
// after-hours load is legitimate baseload, not schedulable waste. "Lab" is intentionally
// NOT included (mixed: freezers/fume-hoods partly legitimate, partly real waste).
//
// Run AFTER fix_page5_ghost_gate.csx (this string-replaces the threshold set it produced).
// HOW TO RUN: External Tools -> Tabular Editor -> C# Script -> paste -> Run (F5) -> Save -> republish.

string oldSet = "{ \"Hotel\", \"Healthcare\" }";
string newSet = "{ \"Hotel\", \"Healthcare\", \"Data_Center\" }";

int seen = 0;
int changed = 0;
foreach (var m in Model.AllMeasures)
{
    if (m.Name == "Ghost Load Risk Status"
        || m.Name == "Occupancy Top Insight"
        || m.Name == "Ghost Load Annual Cost EUR")
    {
        seen++;
        string e = m.Expression;
        if (e.IndexOf(oldSet) >= 0)
        {
            m.Expression = e.Replace(oldSet, newSet);
            changed++;
        }
    }
}

Info("Measures seen: " + seen + " (expect 3). 24/7 set updated: " + changed
    + ". If changed < 3, the threshold string spacing differs - tell Claude, do not save.");
