// =============================================================================
// ADD/UPDATE - Page 10: empty-state caption for the Install-solar opportunities
// table. Tabular Editor 2 C# script. Paste -> F5 -> Ctrl+S -> PBI refresh.
// =============================================================================
// A Power BI table renders nothing when it has zero rows, so a building with no
// actionable install-solar opportunity (already has PV, or its only option is an
// INFORMATIONAL / non-viable one) shows a headers-only table that looks broken.
// This measure returns a caption WHEN there is no actionable INSTALL_SOLAR row,
// and an EMPTY STRING otherwise (NOT blank) so the overlay card shows nothing
// instead of a "--" dash. The count excludes INFORMATIONAL to match a table that
// is filtered to actionable opportunities; if your table keeps INFORMATIONAL
// rows, drop that filter line.
// Put it in a CARD visual laid over the table, BACKGROUND set to transparent/Off.
// NOTE: keep DAX comment lines free of the '=' character (TE paste quirk).
// =============================================================================

int n = 0;
Table tbl = Model.Tables["gold_recommendations"];
string nm = "Install Solar Empty State";
Measure m = null;
foreach (var mm in Model.AllMeasures) { if (mm.Name == nm) { m = mm; break; } }
if (m == null) { m = tbl.AddMeasure(nm); n++; }
m.Expression =
@"// Caption only when there is no ACTIONABLE install-solar row in the current
// view; otherwise an empty string so the overlay card shows nothing (no dash).
VAR _n =
    CALCULATE (
        COUNTROWS ( gold_recommendations ),
        gold_recommendations[action_type] = ""INSTALL_SOLAR"",
        gold_recommendations[priority_label] <> ""INFORMATIONAL""
    )
RETURN
    IF ( ISBLANK ( _n ) || _n = 0, ""No install-solar opportunity for the current selection."", """" )";
m.DisplayFolder = "Solar - Realtime & Opportunity";

Info("Done. Install Solar Empty State " + (n>0 ? "created." : "updated.") + " Ctrl+S, then Refresh.");
