# ADR-001: SCADA / Inverter Live Telemetry Ingestion (Solar)

**Status:** Accepted — Phase A **BUILT + sandbox-verified 2026-06-16** (pending migration apply + backend deploy). Phase B (real-time streaming) deferred.
**Date:** 2026-06-16
**Deciders:** Ali Mert Özdemir (founder · product owner · energy reviewer)
**Related:** [iot-capacity-decision.md](iot-capacity-decision.md) · [iot-page8-fdd-architecture.md](iot-page8-fdd-architecture.md) · [data-connection-architecture.md](data-connection-architecture.md) · `edge-gateway/` · `notebooks/iot/`

## Context

EnergyLens must connect **real** SCADA / inverter telemetry to replace the synthetic
generators that currently feed the solar gold columns (`silver_solar_generation_clean`
→ `03_gold_kpi_engine`). Forces at play:

- **Assets already built.** `edge-gateway/` implements tested Python adapters for
  Modbus TCP, BACnet/IP, MQTT 5.0, OPC-UA and REST. `notebooks/iot/` has the IoT
  adapter framework, bronze IoT ingestion, processing (11b) and FDD (11c).
  `semantic-model/kql/iot_schema.kql` defines the real-time schema. The Page 8
  reference is Event Hub → EventStream → Eventhouse(KQL) + Lakehouse.
- **Capacity cost is the dominant constraint pre-revenue.** EventStream + Eventhouse
  run on always-on Fabric capacity (CU). Working figures [Muhtemel — re-verify against
  current Azure pricing]: Fabric **F2 ≈ €242/mo** 24/7 (≈ €87 paused), **F64 ≈ €7,740/mo**;
  Azure **Event Hub ≈ €11–22/mo** (1 TU). (The "€32" figure in older notes is wrong.)
- **Latency need is modest.** Inverter/SCADA telemetry is meaningful at **5–15 min**
  granularity; this is the analytics/billing standard. Sub-minute real-time only adds
  value for live ops dashboards (Page 8) and fast fault detection.
- **No real device endpoint is connected yet.** "Live setup" today means provisioning
  the path and pointing the agent at a real inverter (or a SunSpec simulator).
- **Margin strategy** (established): defer always-on streaming capacity until the first
  paying IoT/real-time customer ("① Decouple", see iot-capacity-decision.md).

## Decision

Adopt a **phased** ingestion architecture:

- **Phase A (now):** existing **edge-agent → micro-batch (5–15 min) → Lakehouse Bronze**.
  Reuse the edge-gateway protocol adapters (Modbus TCP / SunSpec and OPC-UA are the
  inverter/SCADA primaries). **No Event Hub, no EventStream, no Eventhouse** → **zero new
  always-on capacity**.
- **Phase B (trigger: first paying real-time/IoT customer, or a high-frequency fleet):**
  insert **Event Hub → EventStream → Eventhouse** for sub-minute streaming (Page 8
  flagship), keeping the **same Bronze contract** so silver/gold logic is unchanged.

## Options Considered

### Option A — Edge-agent → micro-batch → Lakehouse Bronze  *(CHOSEN, Phase A)*
| Dimension | Assessment |
|-----------|------------|
| Complexity | Low–Med (agent already built) |
| Cost | ~€0 marginal (reuse Container App + Lakehouse storage) |
| Scalability | Med (ample for many buildings @ 5–15 min) |
| Team familiarity | High |
| Latency | 5–15 min (batch) |

**Pros:** zero always-on capacity; reuses built gateways; covers on-prem &
network-isolated SCADA; clean upgrade seam to Phase B; honest with current
data-sourcing reality.
**Cons:** not real-time; needs a batch scheduler; no live KQL hot-path yet.

### Option B — Edge-agent → Event Hub → EventStream → Eventhouse + Lakehouse  *(Phase B / Page 8)*
| Dimension | Assessment |
|-----------|------------|
| Complexity | High |
| Cost | High (Fabric capacity always-on + Event Hub) |
| Scalability | High (true streaming) |
| Team familiarity | Med |
| Latency | Sub-minute |

**Pros:** real-time, flagship Page 8, scales to high-frequency fleets.
**Cons:** recurring capacity cost not justified pre-revenue; over-engineered for the
solar analytics cadence.

### Option C — Vendor cloud API pull (SolarEdge / SMA / Fronius / Huawei FusionSolar)
| Dimension | Assessment |
|-----------|------------|
| Complexity | Med (per-vendor adapters) |
| Cost | Low (scheduled job) |
| Scalability | Med (API rate limits) |
| Team familiarity | Med |
| Latency | 5–15 min+ (polling) |

**Pros:** no on-site agent for cloud-connected inverters; fast for specific brands.
**Cons:** per-vendor maintenance; rate limits; not real-time; **excludes on-prem /
isolated SCADA**; data flows via a third-party cloud. Best as an *optional complementary*
connector, not the backbone.

## Trade-off Analysis

- **Capacity cost is the deciding force.** Only Option B adds recurring Fabric capacity;
  A and C avoid it. Pre-revenue, that rules B out as the starting point.
- **A vs C:** A generalizes (any protocol, on-prem, isolated networks) and reuses already-built
  assets; C is brand-specific and cloud-dependent. → **A as backbone, C as an optional
  per-brand fast-path** for customers whose inverters are already cloud-connected.
- **Latency:** solar PR / yield / self-consumption are hourly–daily KPIs; 5–15 min batch
  fully serves them. Real-time is a Page-8 / live-ops concern → defer to B.
- **Contract stability:** defining the Bronze schema now (aligned to `silver_iot_normalized`
  + `iot_schema.kql`) means Phase B swaps only the *transport*, not the analytics.

## Consequences

- **Easier:** a real solar data path with no new cost; reuses the gateways; strengthens the
  honesty/reality layer (real telemetry, not synthetic).
- **Harder:** need a batch scheduler, agent deployment + auth, and device onboarding; a
  5–15 min latency ceiling until Phase B.
- **Revisit at the Phase B trigger:** first paying real-time/IoT customer, or a fleet beyond
  ~a few hundred high-frequency points.

## Phase A — architecture detail

1. **Edge agent** (`edge-gateway/run_agent.py`) polls the inverter/SCADA: **Modbus TCP /
   SunSpec** (primary), **OPC-UA** (vendor SCADA), REST/MQTT fallback. Normalizes to standard
   units (kW, kWh, W/m², °C, %) via the adapter framework.
2. **Buffer + batch:** the agent buffers locally and pushes a batch every 5–15 min.
3. **Bronze:** `bronze_iot_raw` (protocol-native) → `silver_iot_normalized` → solar gold
   columns. Real `generated / self_consumed / exported / irradiance` replace the synthetic
   `silver_solar_generation_clean` inputs for connected buildings.
4. **Data-quality guard already in place:** `PR_MAX_PLAUSIBLE` clamp in `03_gold_kpi_engine`
   protects the performance-ratio KPI against bad/low-sun sensor readings.

## Open sub-decisions (quick call before build)

1. **Bronze write path:** (a) agent → FastAPI ingest endpoint → Lakehouse *(reuses auth,
   works through Azure egress)* vs (b) agent → OneLake/Parquet direct *(fewer hops, needs
   OneLake creds on the edge)*. Lean (a).
2. **First real device / pilot:** which inverter/SCADA brand + protocol? SunSpec/Modbus is the
   safe default; SolarEdge/SMA if we pilot the cloud-API path. Until a device exists, a
   **SunSpec Modbus simulator** validates the path end-to-end.
3. **Scheduler:** Fabric Data Pipeline (uses capacity briefly) vs **backend Container App cron**
   (zero marginal). Lean Container App cron for Phase A.

## Action Items

1. [x] Bronze write path = agent → FastAPI `/ingest/telemetry` → Postgres `bronze_iot_readings` (migration `c3d4e5f6a7b8`). Lakehouse-Bronze sync deferred to a later loader (backend cannot reach Fabric SQL on Azure; Postgres-first matches the live arch).
2. [ ] Write the Phase A Bronze schema doc (align `iot_schema.kql` / `silver_iot_normalized`).
3. [x] `sim_modbus_inverter.py` + `config.modbus.solar.sim.json` / `.http.example.json` added; mock E2E dry-run verified (10 readings, schema match).
4. [x] Agent batch → `/ingest/telemetry` → `bronze_iot_readings` wired via `HttpIngestSink` (€0, no Event Hub). Runbook: docs/runbooks/scada-phase-a-dry-run.md.
5. [ ] Map real solar telemetry into the gold solar columns; retire the synthetic generator for connected buildings.
6. [x] Phase B is **activation-ready (dormant, EUR0)**: `EventHubSink` + `MultiSink` (`--sink tee`) in the agent, Eventhouse schema + mapping (`semantic-model/kql/iot_schema.kql`), provisioning script (`scripts/fabric_deploy/provision_eventhub.sh`), activation runbook (`docs/runbooks/scada-phase-b-activation.md`). Activate on the first paying real-time customer.
