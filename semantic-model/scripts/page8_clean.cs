// EnergyLens — PAGE 8 (Real-Time IoT) TEMIZ OLCU KURULUMU. TE2 C# Script -> F5 -> Ctrl+S -> Refresh.
// O sayfanin TUM olculerini idempotent kurar/gunceller (var olani gunceller). Tek-satir DAX, paste-guvenli.
System.Action<string,string,string,string,string> U = (tbl,nm,ex,fmt,fld) => { if(!Model.Tables.Any(t=>t.Name==tbl)){Output("ATLA (tablo yok): "+nm);return;} var m=Model.AllMeasures.FirstOrDefault(x=>x.Name==nm); if(m==null)m=Model.Tables[tbl].AddMeasure(nm,ex); else m.Expression=ex; if(fmt!=null)m.FormatString=fmt; if(fld!=null)m.DisplayFolder=fld; Output("ok: "+nm); };
string F="IoT (Page 8)";
// --- C1 Real-Time Building Power (sensor_type DOGRULA: 'building_kwh') ---
U("gold_iot_realtime","Realtime Building Power kW",@"CALCULATE( AVERAGE(gold_iot_realtime[reading_value_avg]), gold_iot_realtime[sensor_type]=""building_kwh"" )","#,##0.0",F);
// --- C2 Zone Comfort Compliance (EN 16798) ---
U("gold_iot_realtime","IoT Zone Setpoint Compliance Pct",@"CALCULATE( AVERAGE(gold_iot_realtime[in_setpoint_pct]), gold_iot_realtime[sensor_type] IN {""HVAC_temp"",""humidity"",""CO2""} )","0.0",F);
U("gold_iot_realtime","IoT Zone Compliance Display",@"VAR p=[IoT Zone Setpoint Compliance Pct] RETURN IF(ISBLANK(p),""-- %"", FORMAT(ROUND(p,0),""0"") & ""% in setpoint (EN 16798)"")",null,F);
U("gold_iot_realtime","IoT Zone Compliance Color",@"VAR p=[IoT Zone Setpoint Compliance Pct] RETURN SWITCH(TRUE(), ISBLANK(p),""#AAAAAA"", p>=90,""#2ECC40"", p>=75,""#FF851B"",""#FF4136"")",null,F);
// --- C3 Indoor Air Quality - CO2 ---
U("gold_iot_realtime","IoT CO2 Live",@"CALCULATE( AVERAGE(gold_iot_realtime[reading_value_avg]), gold_iot_realtime[sensor_type]=""CO2"" )","#,##0",F);
U("gold_iot_realtime","IoT CO2 Display",@"VAR c=[IoT CO2 Live] RETURN SWITCH(TRUE(), ISBLANK(c),""--"", c<800,""Good ""&FORMAT(c,""0"")&"" ppm"", c<=1200,""Fair ""&FORMAT(c,""0"")&"" ppm"",""Poor ""&FORMAT(c,""0"")&"" ppm"")",null,F);
U("gold_iot_realtime","IoT CO2 Color",@"VAR c=[IoT CO2 Live] RETURN SWITCH(TRUE(), ISBLANK(c),""#AAAAAA"", c<800,""#2ECC40"", c<=1200,""#FF851B"",""#FF4136"")",null,F);
// --- C4 Active Alerts + Estimated Cost ---
U("gold_iot_fdd","IoT FDD High Today",@"CALCULATE( COUNTROWS(gold_iot_fdd), gold_iot_fdd[severity]=""High"", gold_iot_fdd[event_date]=TODAY() )","#,##0",F);
U("gold_iot_fdd","IoT FDD Cost Today EUR",@"CALCULATE( SUM(gold_iot_fdd[cost_eur_estimate]), gold_iot_fdd[event_date]=TODAY() )","#,##0.00",F);
U("gold_iot_fdd","IoT C4 Label v59",@"VAR f=[IoT FDD High Today] VAR c=[IoT FDD Cost Today EUR] RETURN IF(f=0 && (c=0 || ISBLANK(c)),""All Clear"", FORMAT(f,""0"") & "" faults - Est. EUR "" & FORMAT(ROUND(c,0),""0"") & "" today"")",null,F);
U("gold_iot_fdd","IoT C4 Color v59",@"VAR f=[IoT FDD High Today] RETURN SWITCH(TRUE(), ISBLANK(f) || f=0,""#2ECC40"", f<=2,""#FF851B"",""#FF4136"")",null,F);
// --- V2 Sensor Uptime (matrix) ---
U("gold_iot_daily_summary","V2 Sensor Uptime Pct",@"AVERAGE( gold_iot_daily_summary[sensor_uptime_pct] )","0.0",F);
U("gold_iot_daily_summary","V2 Uptime Color Index",@"VAR u=[V2 Sensor Uptime Pct] RETURN SWITCH(TRUE(), ISBLANK(u),""#AAAAAA"", u>=95,""#2ECC40"", u>=85,""#FF851B"",""#FF4136"")",null,F);
// --- FDD ozet kartlari ---
U("gold_iot_fdd","IoT FDD Diagnoses Today",@"CALCULATE( COUNTROWS(gold_iot_fdd), gold_iot_fdd[event_date]=TODAY() )","#,##0",F);
U("gold_iot_fdd","IoT FDD Max Priority",@"MAXX( gold_iot_fdd, gold_iot_fdd[priority_score] )","0",F);
U("gold_iot_fdd","IoT FDD Avg Confidence Pct",@"VAR c=AVERAGE(gold_iot_fdd[confidence]) RETURN IF(ISBLANK(c),""--"",FORMAT(c,""0%""))",null,F);
U("gold_iot_fdd","IoT FDD Energy Impact kWh Today",@"CALCULATE( SUM(gold_iot_fdd[energy_impact_kwh]), gold_iot_fdd[event_date]=TODAY() )","#,##0.0",F);
// --- FDD tablo (satir-bazli) ---
U("gold_iot_fdd","IoT FDD Priority Band",@"VAR p=SELECTEDVALUE(gold_iot_fdd[priority_score]) RETURN SWITCH(TRUE(), ISBLANK(p),""--"", p>=60,""Urgent"", p>=35,""High"", p>=20,""Medium"",""Low"")",null,F);
U("gold_iot_fdd","IoT FDD Priority Color",@"VAR p=SELECTEDVALUE(gold_iot_fdd[priority_score]) RETURN SWITCH(TRUE(), ISBLANK(p),""#AAAAAA"", p>=60,""#FF4136"", p>=35,""#FF851B"", p>=20,""#FFDC00"",""#2ECC40"")",null,F);
U("gold_iot_fdd","IoT FDD Row Confidence",@"VAR c=SELECTEDVALUE(gold_iot_fdd[confidence]) RETURN IF(ISBLANK(c),""--"",FORMAT(c,""0%""))",null,F);
U("gold_iot_fdd","IoT FDD Row Cost Label",@"VAR c=SELECTEDVALUE(gold_iot_fdd[cost_eur_estimate]) RETURN IF(ISBLANK(c) || c=0,""--"",""Est. EUR "" & FORMAT(c,""0.00""))",null,F);
Output("PAGE 8 OLCULER HAZIR. Ctrl+S -> Power BI Refresh. Sonra eski kirik gorselleri silip bu olculerle kur.");
