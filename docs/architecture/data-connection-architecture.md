# EnergyLens — Data Connection Architecture

_Status: decided 2026-06-05. Supersedes the ad-hoc "data_source dropdown" approach._

## 1. Problem

EnergyLens needs each customer building's energy data in the gold KPI layer. Building
automation is heterogeneous (BACnet/IP, Modbus TCP, MQTT, REST/proprietary), usually
**on-premise behind a firewall**, and most building owners do **not** know their register
maps / device addresses (that is integrator knowledge). The connection strategy must:

- work for a **non-technical owner** (zero infrastructure), and
- scale to an **integrator-grade live connection**, and
- **reuse** the existing Fabric pipeline + `notebooks/iot/00_iot_adapter_framework.py`
  (which normalizes any protocol payload to one standard schema but does **not** itself
  connect to devices).

## 2. Decision — Tiered ingestion, one convergence

Three ingestion paths, chosen by customer capability. All converge to the same
normalized schema → silver → gold, so the dashboards/advisor never care which path a
building used.

### Tier 1 — Upload / Manual baseline  ✅ BUILT
- Customer uploads a **consumption CSV / utility bills**, or types monthly readings.
- Stored in Postgres `building_consumption` (one row per `YYYY-MM`).
- Addressed by the building **UUID**, so it works for buildings still pending a Fabric
  bridge (`fabric_building_id` NULL) — the common state right after onboarding.
- Use: the non-technical owner, or a fast "see value today" start.
- _Built: `building_consumption` table (migration `e1a7c4f29b80`), `POST/GET
  /buildings/{uuid}/consumption`, client-side CSV parser, `ConsumptionUploadModal`._

### Tier 2 — Edge agent + auto-discovery  ▶ PRIMARY for live data
- A lightweight **on-site edge gateway** (container/agent the customer or their
  integrator deploys) that:
  - **auto-discovers** devices (BACnet WhoIs, Modbus probe),
  - reads them and runs the existing **adapter framework** to normalize,
  - **pushes outbound** to Azure Event Hub → EventStream → Lakehouse/KQL (the pipeline
    that already exists). Outbound push solves the firewall/on-prem problem (no inbound).
- Product side: the **Devices & Connections** page shows discovered devices + points;
  the only manual step is **mapping each point → `sensor_type` + zone**.
- Recommended primary path for live monitoring — minimal manual config, scales.

### Tier 3 — Manual device config + template library  ▶ fallback / no-edge
- For customers who can't run an edge agent, or want explicit control, or have a
  cloud-reachable device/API. A **Devices & Connections** flow to add a device manually:
  - protocol + connection params (Modbus: IP/port/unit-id; BACnet: device instance;
    MQTT: broker/topics; REST: endpoint/auth),
  - a **register/point map** built by hand **or picked from a device-template library**
    (pre-built maps for common meters/controllers, e.g. Schneider PM5560), then
  - the same **point → sensor_type + zone** mapping.
- Drives either an edge agent's config or a cloud-side poller.

## 3. Convergence (all tiers → one schema)

Standard normalized record (from the adapter framework):
`device_id · building_id · sensor_type · sensor_location · reading_value · reading_unit ·
source_protocol · timestamp · reading_quality`

- **Live (Tier 2/3):** → Event Hub → EventStream → Lakehouse/KQL → gold.
- **Baseline (Tier 1):** → `building_consumption` → (next) monthly gold KPIs.

## 4. Backend data model (needed for Tier 2/3)

Onboarding currently stashes high-level config (protocols, sensor types, zones, data
method) as **JSON on the module `notes`** — fine for intent, not for live config. The
Devices & Connections flow needs proper tables:

- **`device`** — `id, building_id (FK), protocol, name, connection_config (JSONB:
  ip/port/unit_id/broker/endpoint/…), status, last_seen_at`.
- **`sensor_point`** — `id, device_id (FK), point_ref (register/object/topic),
  sensor_type, zone, unit, scale, enabled`. This is the **point → sensor map**.

## 5. Product surfaces

- **Onboarding** = inventory ("what do you have"): building profile + systems + IoT
  protocols/sensor-types/zones + data method. ✅ done (stored in module notes JSON).
- **Devices & Connections** (new) = the technical wiring + point→sensor mapping (Tier 2/3).
- **Upload modal** = Tier 1 baseline. ✅ done.

## 6. Roadmap & status

1. ✅ **Tier 1 CSV/bill upload** — `building_consumption` + endpoints + modal.
2. ▶ **Compute monthly KPIs from the uploaded baseline** so dashboards/advisor light up
   for upload-only buildings (currently the upload stores + summarizes only).
3. ▶ **Devices & Connections page** — Tier 3 manual device config + template library +
   point→sensor mapping (`device` + `sensor_point` tables).
4. ▶ **Edge agent** — the on-site gateway + auto-discovery (Tier 2). The data-collection
   layer the adapter framework was always missing.
5. ◦ **PDF / photo bill OCR** — Tier 1 enrichment; needs OCR/LLM (credits).
6. ◦ **Self-serve Fabric bridging (Access Layer 3)** — let a customer unlock the full Fabric
   analytics for a *pending* building (`fabric_building_id` NULL → live), **data-tier-aware**
   (unlock only the pages the data earns) and **AI-guided**. Today this bridge is manual
   (founder `/admin`). See [`self-serve-fabric-bridging.md`](./self-serve-fabric-bridging.md).
   _PLAN — awaiting approval._

## 7. Open decisions (Mert / founder)

- **Edge agent: build vs partner.** Build a small agent, or integrate an off-the-shelf
  BACnet/Modbus→MQTT gateway? (Affects time-to-market vs control.)
- **Template library** — source + maintenance model for device register maps.
- **Baseline→KPI compute location** — Postgres aggregation vs push uploads into Fabric.
- **Edge auth/onboarding** — how an edge agent authenticates + binds to a building.

---

_Principle: onboarding stays fast (inventory); the technical wiring lives in a dedicated
Devices & Connections flow; an edge agent (outbound push + auto-discovery) is the
recommended primary for live data; CSV/manual is the universal quick-start. All paths
converge to the same normalized → gold pipeline._
