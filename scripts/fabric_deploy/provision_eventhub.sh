#!/usr/bin/env bash
# =============================================================================
# Phase B real-time backbone — Azure Event Hub provisioning (DORMANT BY DEFAULT)
# =============================================================================
# Run ONLY when Phase B (real-time streaming / Page 8) is funded. Creating these
# resources starts billing: Event Hub namespace ~EUR11-22/mo (Standard, 1 TU);
# the Fabric EventStream + Eventhouse run on Fabric capacity (F-SKU, always-on)
# which is the larger cost — see docs/architecture/iot-capacity-decision.md.
# [Muhtemel — re-verify current Azure/Fabric pricing before activating.]
#
# Idempotent-ish (az create is upsert-like). Prereq: `az login`.
#   RG=energylens-rt LOCATION=germanywestcentral ./provision_eventhub.sh
# Teardown (stops cost):  az group delete -n "$RG" --yes
# =============================================================================
set -euo pipefail

RG="${RG:-energylens-rt}"
LOCATION="${LOCATION:-germanywestcentral}"      # keep data in the EU (DE)
NS="${NS:-energylens-iot}"                        # namespace name (globally unique)
HUB="${HUB:-iot-raw}"
SKU="${SKU:-Standard}"                            # Standard required for EventStream
TU="${TU:-1}"                                     # throughput units (scale later)

echo ">> RG=$RG LOCATION=$LOCATION NS=$NS HUB=$HUB SKU=$SKU TU=$TU"
az group create -n "$RG" -l "$LOCATION" -o none
az eventhubs namespace create -g "$RG" -n "$NS" -l "$LOCATION" --sku "$SKU" --capacity "$TU" -o none
az eventhubs eventhub create -g "$RG" --namespace-name "$NS" -n "$HUB" \
    --partition-count 2 --cleanup-policy Delete --retention-time-in-hours 24 -o none
# send-only rule for the edge agent (least privilege)
az eventhubs eventhub authorization-rule create -g "$RG" --namespace-name "$NS" \
    --eventhub-name "$HUB" -n agent-send --rights Send -o none
CONN=$(az eventhubs eventhub authorization-rule keys list -g "$RG" --namespace-name "$NS" \
    --eventhub-name "$HUB" -n agent-send --query primaryConnectionString -o tsv)

echo ""
echo ">> Provisioned. Set these on the edge agent (env / config), NEVER inline:"
echo "   EVENTHUB_NAME=$HUB"
echo "   EVENTHUB_CONN=$CONN"
echo ""
echo ">> Then run the agent in dual mode (real-time stream + EUR0 batch landing):"
echo "   python run_agent.py --platform <api-base> --agent-token <T> \\"
echo "       --sink tee --eh-conn \"\$EVENTHUB_CONN\" --eh-name $HUB \\"
echo "       --ingest-url <api-base>/ingest/telemetry"
