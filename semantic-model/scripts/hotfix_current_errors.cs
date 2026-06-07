// EnergyLens — HOTFIX (mevcut hataları kapatır). TE2 C# Script -> F5 -> Ctrl+S -> Power BI Refresh.
// Kısa script: P3 status (MAX->count), Page 8 IoT (REMOVEFILTERS('Date') kaldır),
// Page 9 RTE (x100), Page 10 specific-yield (kolon-bagimsiz). Idempotent.
System.Action<string,string,string,string> U = (tbl,nm,ex,fmt) => {
    if(!Model.Tables.Any(t=>t.Name==tbl)){ Output("skip (no table): "+nm); return; }
    var m=Model.AllMeasures.FirstOrDefault(x=>x.Name==nm);
    if(m==null) m=Model.Tables[tbl].AddMeasure(nm,ex); else m.Expression=ex;
    if(fmt!=null) m.FormatString=fmt;
    Output("ok: "+nm);
};

// Page 3 — durum (Boolean MAX hatasi giderildi)
U("gold_anomaly_log","P3 Anomaly Status",
  "VAR o=CALCULATE(COUNTROWS(gold_anomaly_log),gold_anomaly_log[is_resolved]=FALSE()) RETURN IF(o>0,\"Open\",\"Resolved\")",null);

// Page 8 — IoT 'Today' olculeri (REMOVEFILTERS('Date') KALDIRILDI)
U("gold_iot_fdd","IoT FDD Findings Today","CALCULATE(COUNTROWS(gold_iot_fdd),gold_iot_fdd[event_date]=TODAY())","#,##0");
U("gold_iot_fdd","IoT FDD High Today","CALCULATE(COUNTROWS(gold_iot_fdd),gold_iot_fdd[severity]=\"High\",gold_iot_fdd[event_date]=TODAY())","#,##0");
U("gold_iot_fdd","IoT FDD Cost Today EUR","CALCULATE(SUM(gold_iot_fdd[cost_eur_estimate]),gold_iot_fdd[event_date]=TODAY())","#,##0.00");
U("gold_iot_fdd","IoT Total Cost Today EUR","CALCULATE(SUM(gold_iot_fdd[cost_eur_estimate]),gold_iot_fdd[event_date]=TODAY())+CALCULATE(SUM(gold_iot_realtime[cost_eur_window]),gold_iot_realtime[event_date]=TODAY())","#,##0.00");
U("gold_iot_fdd","IoT FDD Diagnoses Today","CALCULATE(COUNTROWS(gold_iot_fdd),gold_iot_fdd[event_date]=TODAY())","#,##0");
U("gold_iot_fdd","IoT FDD Energy Impact kWh Today","CALCULATE(SUM(gold_iot_fdd[energy_impact_kwh]),gold_iot_fdd[event_date]=TODAY())","#,##0.0");

// Page 9 — RTE yuzdeye (x100)
U("gold_battery_dispatch","C4 Round Trip Efficiency Pct","AVERAGE(gold_battery_dispatch[round_trip_efficiency])*100","0.0");

// Page 10 — specific yield (uretim/kapasite, kolon-bagimsiz)
U("gold_kpi_daily","Avg Solar Specific Yield kWh kWp",
  "AVERAGEX(VALUES(gold_kpi_daily[building_id]),DIVIDE(CALCULATE(SUM(gold_kpi_daily[solar_generated_kwh])),CALCULATE(MAX(gold_kpi_daily[pv_capacity_kwp]))))","#,##0.0");

Output("HOTFIX DONE -> Ctrl+S -> Power BI Refresh.");
