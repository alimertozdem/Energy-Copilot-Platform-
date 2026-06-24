# ============================================================================
# 50_materialize — Section 4) gold_hvac_analytics -> mv_hvac_analytics
# Paste this as a NEW cell in the Fabric notebook 50_materialize_to_postgres,
# AFTER cell 11 (mv_kpi_daily) and BEFORE the final "Done — verify" cell.
# Requires: _where(), materialize() helpers already defined (cells 5).
# Pre-req: mv_hvac_analytics table created once (run mv_hvac_analytics.sql).
# ============================================================================

# Bare table name => Fabric catalog resolution (dbo.gold_hvac_analytics),
# NOT the flat Tables/ ABFS path. This is the SAFE form: mv_building_master
# uses the same bare-name pattern and returns all 10 buildings, not a stale 6.
df_hvac = spark.sql(f"""
    SELECT building_id, CAST(year_month AS DATE) AS year_month,
           reporting_year, reporting_month,
           total_consumption_kwh, heating_energy_kwh, cooling_energy_kwh,
           ventilation_kwh, hvac_total_kwh, non_hvac_kwh,
           hvac_share_pct, heating_share_pct, cooling_share_pct,
           hdd_monthly, cdd_monthly,
           cop_actual_avg, scop_rolling,
           heat_loss_kwh, heat_loss_kwh_m2,
           u_composite, insulation_score, hvac_efficiency_score,
           system_type, system_label, renovation_priority, renovation_reason,
           updated_at
    FROM gold_hvac_analytics {_where()}
""")

# Inline sanity guard — catches a stale flat-path read (would show 6) and the
# B011-B015 test-building leak (master has only B001-B010).
print("HVAC distinct buildings:", df_hvac.select("building_id").distinct().count())
print("HVAC distinct months   :", df_hvac.select("year_month").distinct().count())
print("HVAC building_ids       :",
      sorted([r.building_id for r in df_hvac.select("building_id").distinct().collect()]))

materialize(df_hvac, "mv_hvac_analytics",
    ["building_id","year_month","reporting_year","reporting_month",
     "total_consumption_kwh","heating_energy_kwh","cooling_energy_kwh",
     "ventilation_kwh","hvac_total_kwh","non_hvac_kwh",
     "hvac_share_pct","heating_share_pct","cooling_share_pct",
     "hdd_monthly","cdd_monthly",
     "cop_actual_avg","scop_rolling",
     "heat_loss_kwh","heat_loss_kwh_m2",
     "u_composite","insulation_score","hvac_efficiency_score",
     "system_type","system_label","renovation_priority","renovation_reason",
     "updated_at"])
