// =============================================================================
// FIX — Page 8 IoT visuals don't follow the building slicer
// Tabular Editor 2 C# Script — paste once, F5, Save, Refresh.
// =============================================================================
// Root cause: NONE of the IoT measures filter by building (they only filter by
// sensor_type / event_date), so the building slicer can only reach them through a
// model RELATIONSHIP — and that relationship is missing. Result: every IoT visual
// shows the all-buildings average no matter which building is selected.
//
// This connects the IoT fact tables to the building dimension
// (silver_building_master[building_id]) as one-to-many, single cross-filter
// (building filters IoT). It is defensive: skips a table if the relationship
// already exists, and if a table has no building_id column it just PRINTS that
// table's columns (so we can see the real key) instead of failing.
//
// After running, select a building on Page 8 — Power, Zone Comfort, FDD, Waste
// should all change. If the Info log shows "NO building_id" for a table, send me
// that line and I'll adjust to the real column.
// =============================================================================

var master = Model.Tables.FirstOrDefault(t => t.Name == "silver_building_master");
if (master == null) { Info("ABORT: silver_building_master table not found."); return; }
var mKey = master.Columns.FirstOrDefault(c => c.Name.ToLower() == "building_id");
if (mKey == null) { Info("ABORT: silver_building_master has no building_id column."); return; }

string[] iotTables = { "gold_iot_realtime", "gold_iot_fdd", "gold_iot_daily_summary" };
int made = 0, skipped = 0, problems = 0;

foreach (var tn in iotTables)
{
    var t = Model.Tables.FirstOrDefault(x => x.Name == tn);
    if (t == null) { Info("skip (table not in model): " + tn); continue; }

    var key = t.Columns.FirstOrDefault(c => c.Name.ToLower() == "building_id");
    if (key == null)
    {
        problems++;
        Info("NO building_id in " + tn + ". Columns = " + string.Join(", ", t.Columns.Select(c => c.Name)));
        continue;
    }

    bool exists = Model.Relationships.Any(r =>
        (r.FromTable == t && r.ToTable == master) ||
        (r.FromTable == master && r.ToTable == t));
    if (exists) { skipped++; Info("already related (skip): " + tn); continue; }

    try
    {
        var rel = Model.AddRelationship();
        rel.FromColumn = key;     // many side  (IoT fact)
        rel.ToColumn = mKey;      // one side   (building dimension)
        rel.IsActive = true;
        made++;
        Info("CREATED: silver_building_master[building_id] 1--* " + tn + "[building_id]");
    }
    catch (System.Exception ex)
    {
        problems++;
        Info("FAILED " + tn + ": " + ex.Message);
    }
}

Info("Done. created=" + made + " skipped=" + skipped + " problems=" + problems);
