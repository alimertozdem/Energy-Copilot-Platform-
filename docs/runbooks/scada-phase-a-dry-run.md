# Runbook — SCADA/Solar Phase A ingestion (edge-agent → €0 Bronze landing)

Phase A of ADR-001 ([scada-solar-live-ingestion.md](../architecture/scada-solar-live-ingestion.md)):
the on-site edge agent reads inverter/SCADA telemetry, normalizes at the edge, and
POSTs 5–15 min micro-batches to `POST /ingest/telemetry`, which lands them in the
Postgres table `bronze_iot_readings`. **No Event Hub / EventStream / Eventhouse → zero
new always-on Fabric capacity.**

## What was built (2026-06-16)

- **Migration** `c3d4e5f6a7b8_bronze_iot_readings` — landing table + indexes.
- **Ingest endpoint** `POST /ingest/telemetry` (`app/routers/ingest.py`) — auth by the
  building-scoped `X-Agent-Token` (reuses `get_agent_building`); rejects any reading whose
  `building_id` ≠ the token's building, so an agent can only write its own building.
- **HttpIngestSink** (`edge-gateway/opcua_gateway.py`) — batches normalized events and POSTs
  them; selectable as `--sink http` (run_agent) or `sink.type="http"` (gateway config).
  Shared by every protocol gateway (Modbus/OPC-UA/…).
- **Simulator** `edge-gateway/sim_modbus_inverter.py` + `config.modbus.solar.sim.json`
  (stub) and `config.modbus.solar.http.example.json` (live €0 path).

## Sandbox verification (done)

Mock-Modbus → adapter normalize → `BufferedSink(http)` → mock `/ingest/telemetry`:
**10 readings / 2 batches, agent-token header present, every reading matched the
`TelemetryReading` schema (0 bad keys)**, e.g. `pv_ac_power = 10.5 kW`, `source_protocol=Modbus`.
The only untested seam is the real `pymodbus` TCP socket (sandbox has no PyPI); run the
simulator below on a machine with `pip` to close it.

## Local dry-run with the REAL Modbus socket (your machine)

Needs `pip install "pymodbus>=3.6,<3.7"  # 3.8+ rewrote the datastore; pin the classic API` (3.13 works — sim + gateway are version-tolerant). The
simulator is a SERVER: run it in its OWN terminal and leave it running, then poll from a
SECOND terminal — do NOT chain both in one shell (the server blocks, so the gateway would
hit "connection refused").

```powershell
# both terminals start here:
cd "C:\Energy Management App\Energy-copilot-platform\edge-gateway"
pip install "pymodbus>=3.6,<3.7"  # 3.8+ rewrote the datastore; pin the classic API

# TERMINAL A — inverter simulator (registers 1..6 on 127.0.0.1:15020); leave it running
python sim_modbus_inverter.py --host 127.0.0.1 --port 15020

# TERMINAL B — poll it (stub sink logs each normalized reading)
python modbus_gateway.py --config config.modbus.solar.sim.json --seconds 20 --interval 2 --sink stub
# expect events tagged building_id=B007:
#   pv_ac_power, pv_dc_power, inverter_temp, irradiance, pv_energy_today_kwh, building_power
```

## Go-live for a real site

1. **Apply the migration** (backend): `alembic upgrade head` (creates `bronze_iot_readings`).
2. **Deploy backend** so `/ingest/telemetry` is live: `az containerapp up --source .` (from `web-app/backend`).
3. **Issue an agent token** for the building (web UI, or `POST /buildings/{id}/agent-tokens`).
4. On the edge box: `export AGENT_TOKEN=<token>`, copy `config.modbus.solar.http.example.json`,
   set each device `host`/`unit_id`/`register`/`scale` from the inverter manual and
   `sink.ingest_url` to your backend `…/ingest/telemetry`, then run the agent (systemd/docker),
   `poll_seconds: 300` for a 5-min cadence.
5. **Verify**: rows arrive in `bronze_iot_readings` (filter by `building_id`); the endpoint
   returns `{accepted, rejected}`.

## Built on top of Phase A (2026-06-16)

- **Loader** `bronze_iot_readings` → `gold_solar_daily` (`app/services/solar_telemetry_rollup.py`,
  runner `scripts/run_solar_rollup.py`): generation (energy-counter delta / power integration),
  PR (IEC 61724, clamped), and — when a **building load meter** is also connected —
  self-consumption = ∫ min(P_pv, P_load) dt and export = generated − self-consumption.
- **/solar real-first**: serves `gold_solar_daily` (real telemetry) per building, falling back
  to synthetic `mv_kpi_daily`, with a data-basis badge ("Live telemetry" / "Sample data") and an
  honest self-consumption stat ("needs a load meter" until one is connected).
- To enable self-consumption for a site, add a **load-meter point** (sensor_type
  `building_power` = the building's total consumption kW) to the device config — see register 6
  in `config.modbus.solar.*.json`. Then schedule `scripts/run_solar_rollup.py`.

## Remaining / optional

- Sync the landing to Fabric Lakehouse Bronze Delta (only if/when Phase B streaming is funded —
  see ADR-001 Phase B trigger).
