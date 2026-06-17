# =============================================================================
# 91_rebind_directlake.py — FIX: "DMTS_MonikerWithUnboundDataSources"
# -----------------------------------------------------------------------------
# Updating a DirectLake semantic model via the REST API (updateDefinition) can
# leave the model UNBOUND from its lakehouse → "Cannot load model". This re-binds
# EnergyCopilotModel to its lakehouse. The trimmed measures stay; only the
# connection is restored.
#
# RUN in a Fabric notebook. If the import fails, run this in a cell first:
#     %pip install semantic-link-labs
# =============================================================================
import sempy_labs

sempy_labs.directlake.update_direct_lake_model_lakehouse_connection(
    dataset="EnergyCopilotModel",
    lakehouse="EnergyCopilotLakehouse",
    workspace="Energy-Copilot-Platform",
)
print("Re-bind requested. Now refresh EnergyCopilotModel — it should load with the clean measure list.")
