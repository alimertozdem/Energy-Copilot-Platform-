# Runbook — SCADA/IoT Phase B activation (real-time streaming)

ADR-001 Phase B. **Status: activation-ready, DORMANT (EUR0).** Everything needed to
turn on sub-minute real-time ingestion (Page 8 flagship) is built; no Azure/Fabric
resources are provisioned, so it costs nothing until activated. Marketing-honest
phrasing: *"real-time streaming ingestion is architected and can be enabled"* — not
*"running"*.

## Already built (the "ready" part)

- **Edge agent** already speaks Event Hub: `EventHubSink` + `MultiSink` (`--sink tee`)
  in `edge-gateway/` → it can stream to Event Hub AND keep the EUR0 batch landing at
  the same time, so /solar + gold keep working during Phase B.
- **Eventhouse schema + mapping**: `semantic-model/kql/iot_schema.kql` (`iot_hot_readings`
  + `iot_readings_mapping`) — its JSON paths match the agent's normalized event exactly,
  so no transform is needed between Phase A and Phase B.
- **Provisioning script** (dormant): `scripts/fabric_deploy/provision_eventhub.sh`.
- This runbook.

## When to activate

First paying real-time/IoT customer, or a high-frequency fleet that needs sub-minute
dashboards / fast fault detection. Until then, Phase A (5–15 min batch) fully serves
solar/energy KPIs.

## Cost (verify before activating) [Muhtemel]

- Azure Event Hub namespace (Standard, 1 TU): ~EUR11–22/mo.
- Fabric EventStream + Eventhouse: run on Fabric capacity (F-SKU, **always-on**) —
  the dominant cost (F2 ≈ EUR242/mo 24/7). This is the reason Phase B is gated on revenue.

## Activation steps

1. **Provision Event Hub**: `az login` then `RG=energylens-rt LOCATION=germanywestcentral
   scripts/fabric_deploy/provision_eventhub.sh`. Note the printed `EVENTHUB_CONN`.
2. **Create the Eventhouse**: in Fabric, create a KQL Database `iot_eventhouse`, open a
   Queryset, run `semantic-model/kql/iot_schema.kql` top-to-bottom (creates
   `iot_hot_readings` + the `iot_readings_mapping` ingestion mapping + anomaly tables).
3. **Create the EventStream** (Fabric → Real-Time hub → Eventstream):
   - Source: the Azure Event Hub from step 1 (`iot-raw`).
   - Destination A: Eventhouse `iot_hot_readings`, JSON mapping `iot_readings_mapping`.
   - Destination B (optional cold path): Lakehouse `bronze_iot_raw` (Delta).
4. **Flip the edge agent** to dual mode so real-time AND batch run together:
   `python run_agent.py --platform <api> --agent-token <T> --sink tee
   --eh-conn "$EVENTHUB_CONN" --eh-name iot-raw --ingest-url <api>/ingest/telemetry`.
   (Stream-only: `--sink eventhub`. Batch-only / Phase A: `--sink http`.)
5. **Verify**: run the sample KQL queries at the bottom of `iot_schema.kql` (latest
   reading per sensor, uptime %, CO₂ status); Page 8 dashboards light up.

## Keeping /solar + gold working in Phase B

`--sink tee` keeps the Phase A path (→ `bronze_iot_readings` → `run_solar_rollup` →
`gold_solar_daily` → /solar) running unchanged, in parallel with the real-time stream.
No extra work needed. (Alternative: a scheduled KQL→Postgres export, if you prefer
stream-only on the edge.)

## Teardown (stop the cost)

Flip the agent back to `--sink http`; `az group delete -n energylens-rt --yes`; pause
the Fabric capacity. Phase A continues at EUR0.
