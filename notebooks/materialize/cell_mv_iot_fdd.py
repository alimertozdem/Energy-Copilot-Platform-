# =============================================================================
# 50_materialize_to_postgres.ipynb  --  NEW CELL (paste at the end).
# Mirrors gold_iot_fdd -> mv_iot_fdd (Page 8 fault/waste cost = single source of truth)
# so it is verifiable in Supabase and servable by the backend pg-first path.
#
# Prereq: mv_iot_fdd exists (run mv_iot_fdd_create.sql in Supabase SQL Editor first)
# and the notebook's materialize() helper is defined (run the cells above first / Run all).
# No _where() filter -> mirrors ALL buildings (gold_iot_fdd is small and Page 8 needs all 10).
# SELECT column order MUST match the columns list (materialize inserts by position).
# =============================================================================

df = spark.sql("""
    SELECT building_id, equipment, equipment_type, fault_code, severity,
           confidence, priority_score, description, probable_cause, recommended_action,
           occurrence_count, power_waste_kw, energy_impact_kwh, cost_eur_estimate,
           grid_price, building_type, CAST(event_date AS STRING) AS event_date
    FROM gold_iot_fdd
""")

materialize(df, "mv_iot_fdd", [
    "building_id", "equipment", "equipment_type", "fault_code", "severity",
    "confidence", "priority_score", "description", "probable_cause", "recommended_action",
    "occurrence_count", "power_waste_kw", "energy_impact_kwh", "cost_eur_estimate",
    "grid_price", "building_type", "event_date",
])
print("mv_iot_fdd rows:", df.count())
