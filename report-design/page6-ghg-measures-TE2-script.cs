// ============================================================================
// Tabular Editor 2 — C# script: Page 6 GHG measures (full Scope 1/2/3)
// KULLANIM: TE2'de modeli aç → "C# Script" sekmesi → bunu yapıştır → Run (▶)
//           → sonra Save (Ctrl+S) ile modele yaz. (Model refresh gerekebilir.)
// gold_ghg_scope tablosu + yeni kolonlar modelde OLMALI (önce 09 cell1+cell2 koştur
// ve tabloyu modele schema-refresh ettir). Script idempotent: tekrar çalıştırılabilir.
// ============================================================================
var t = Model.Tables["gold_ghg_scope"];
string folder = "GHG Scopes";

// İsim -> DAX (sayısal ölçüler, format #,0.0)
var measures = new Dictionary<string,string> {
    {"Scope 1 Gas tCO2e",              "SUM ( gold_ghg_scope[scope1_gas_tco2] )"},
    {"Scope 1 Diesel tCO2e",           "SUM ( gold_ghg_scope[scope1_diesel_tco2] )"},
    {"Scope 1 Refrigerant tCO2e",      "SUM ( gold_ghg_scope[scope1_refrigerant_tco2] )"},
    {"Scope 1 Total tCO2e",            "SUM ( gold_ghg_scope[scope1_total_tco2] )"},
    {"Scope 2 Location tCO2e",         "SUM ( gold_ghg_scope[scope2_location_tco2] )"},
    {"Scope 2 Market tCO2e",           "SUM ( gold_ghg_scope[scope2_market_tco2] )"},
    {"Scope 2 Market vs Location tCO2e","[Scope 2 Market tCO2e] - [Scope 2 Location tCO2e]"},
    {"Scope 3 Cat1 Embodied tCO2e",    "SUM ( gold_ghg_scope[scope3_cat1_embodied_tco2] )"},
    {"Scope 3 Cat3 Fuel Energy tCO2e", "SUM ( gold_ghg_scope[scope3_cat3_fuelenergy_tco2] )"},
    {"Scope 3 Cat5 Waste tCO2e",       "SUM ( gold_ghg_scope[scope3_cat5_waste_tco2] )"},
    {"Scope 3 Cat6 Travel tCO2e",      "SUM ( gold_ghg_scope[scope3_cat6_travel_tco2] )"},
    {"Scope 3 Cat7 Commute tCO2e",     "SUM ( gold_ghg_scope[scope3_cat7_commute_tco2] )"},
    {"Scope 3 Cat13 Leased tCO2e",     "SUM ( gold_ghg_scope[scope3_cat13_leased_tco2] )"},
    {"Scope 3 Total (est.) tCO2e",     "SUM ( gold_ghg_scope[scope3_estimated_tco2] )"},
    {"Total GHG Location tCO2e",       "SUM ( gold_ghg_scope[total_ghg_location_tco2] )"},
    {"Total GHG Market tCO2e",         "SUM ( gold_ghg_scope[total_ghg_market_tco2] )"},
};

foreach(var kv in measures) {
    var m = t.Measures.FirstOrDefault(x => x.Name == kv.Key);
    if(m == null) m = t.AddMeasure(kv.Key);
    m.Expression   = kv.Value;
    m.DisplayFolder = folder;
    m.FormatString = "#,0.0";
}

// Etiket ölçüleri (metin — sayı formatı yok)
var s2 = t.Measures.FirstOrDefault(x => x.Name == "Scope 2 Method") ?? t.AddMeasure("Scope 2 Method");
s2.Expression =
"SWITCH ( SELECTEDVALUE ( gold_ghg_scope[scope2_method], \"mixed\" ), " +
"\"market_based_contract\", \"Contract (GoO / PPA)\", " +
"\"residual_mix_no_instrument\", \"Residual mix (no instrument)\", " +
"\"location_fallback_full_disclosure\", \"Location (full-disclosure)\", " +
"SELECTEDVALUE ( gold_ghg_scope[scope2_method], \"mixed\" ) )";
s2.DisplayFolder = folder;

var s3 = t.Measures.FirstOrDefault(x => x.Name == "Scope 3 Disclosure Label") ?? t.AddMeasure("Scope 3 Disclosure Label");
s3.Expression =
"IF ( SELECTEDVALUE ( gold_ghg_scope[scope3_disclosure_grade] ) = FALSE (), " +
"\"Estimated — not disclosure-grade\", \"Disclosure-grade\" )";
s3.DisplayFolder = folder;

Info("Bitti: " + (measures.Count + 2) + " ölçü eklendi/güncellendi. Şimdi Save (Ctrl+S).");
