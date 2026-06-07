// EnergyLens — ORPHAN SWEEP (kisa & paste-guvenli). TE2 C# Script -> F5 -> Ctrl+S -> Power BI Refresh.
// Silinmis tablolarda kalan TUM olculeri siler (C1_*/C2_*/C3_*/C4_*/V1_*/V2_*/V6_* ...) -> tum Missing_References kalkar.
int n=0;
foreach (var tbl in new string[]{"iot_hot_readings","gold_battery_hourly_profile"}) {
    var t = Model.Tables.FirstOrDefault(x => x.Name == tbl);
    if (t == null) { Output("yok: "+tbl); continue; }
    foreach (var m in t.Measures.ToList()) { Output("silindi: "+tbl+"."+m.Name); m.Delete(); n++; }
    try { t.Delete(); Output("tablo dusuruldu: "+tbl); } catch (System.Exception e) { Output("tablo kaldi: "+tbl); }
}
foreach (var m in Model.AllMeasures.ToList()) {
    if (m.Table != null && m.Table.Columns.Count == 0) { Output("oksuz: "+m.Table.Name+"."+m.Name); m.Delete(); n++; }
}
Output("BITTI -- "+n+" oksuz olcu silindi. Simdi Ctrl+S -> Power BI Refresh.");
