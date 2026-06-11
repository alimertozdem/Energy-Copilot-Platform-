# EnergyLens — IoT Real-Time Capacity Model (Decision Record)

_Status: **DECIDED 2026-06-11** — founder (Mert) approved **Option ① "Decouple"** as the
production default. Supersedes the implicit "EventStream-on-Fabric is the only live path"
assumption in [`iot-page8-fdd-architecture.md`](./iot-page8-fdd-architecture.md). **Today the
platform stays in Option ④ (static-snapshot, €0);** ① activates with the first paying IoT
customer._

## 1. The question this answers

IoT telemetry streams 24/7, so the component that **receives** it (EventStream) and the store
it **lands in** (Eventhouse/KQL) must run continuously. Continuous = the capacity never
pauses = it bills 24/7. "Make Page 8 live" therefore reduces to one decision:
**what runs 24/7, and who pays for it?**

This is different from the medallion notebooks, which run for minutes on demand and then
stop. The cost of *batch analytics* is bounded; the cost of *always-on ingestion* is the real
variable, and the four options below are four different answers to it.

## 2. Options considered

| # | Option | Who pays / runs 24/7 | Pro | Con |
|---|---|---|---|---|
| **①** | **Decouple** (cheap primitives) | Event Hubs + existing Container App | Lowest 24/7 cost; no always-on Fabric; matches "separate ingestion from logic" | Two stores (hot + historical); a little more plumbing |
| ② | Single shared Fabric F-SKU (multi-tenant) | One founder-owned F2–F8, always on | Simplest mental model; single stack | Highest fixed monthly cost; grows with streaming buildings |
| ③ | Deploy-to-tenant | Customer-owned F-capacity | Zero capacity cost for us; data residency | Not clean SaaS; per-customer install; hard to update centrally |
| ④ | Static-snapshot (defer) | Nothing 24/7 | €0; perfect for demo/sales/trial | Not actually live |

## 3. Decision

**Production default = ① Decouple.** Today = **④** static-snapshot (€0). **②** is the simpler
fallback if the decoupling plumbing is deferred to ship a first customer fast; **③** is
reserved for enterprise deals that mandate data residency. These are not mutually exclusive —
④ now, ① as the live default, ③ for specific enterprise contracts.

## 4. Architecture — the decoupled live path

```
On-site sensors / edge-gateway  (BACnet · Modbus · MQTT · OPC-UA · REST)
        │  outbound push  (solves firewall / on-prem; no inbound)
        ▼
Azure Event Hubs                 ← always-on, cheap "mailbox" (durable buffer)
        │
        ▼
Container App processor          ← ALREADY running for the backend; normalizes via
   (00_iot_adapter_framework)       any protocol payload → one standard event schema
        │
        ├──► Hot store (Postgres / ADX)        ← Page 8 real-time reads here (seconds-fresh)
        │
        └──► micro-batch → Fabric Lakehouse Bronze   ← historical / analytical only
                              │
                              ▼
                 11b_iot_processing → silver/gold → 11c_iot_fdd (AFDD, 12 rules)
                              │
                              ▼
                       Power BI Page 8  (historical + fault diagnostics)
```

**Key property:** this preserves Page 8's existing **two-mode Silver/Gold contract**
unchanged. The decoupled processor simply becomes one more **Bronze producer** (alongside the
static generator and the direct-EventStream path). Everything downstream — silver, gold, DAX,
visuals — never changes. Switching a customer from ④ → ① is a producer swap, not a rebuild.

## 5. Why ① (rationale)

- **Lowest always-on cost.** Only Event Hubs + the already-paid Container App run 24/7; Fabric
  runs in short batches and can stay small or pause. No always-on premium Fabric capacity.
- **Matches `CLAUDE.md`** — *"separate ingestion, transformation, and business logic."*
  Ingestion lives on cheap streaming primitives; business logic stays in Fabric.
- **F64 is not required.** EnergyLens embeds via **app-owns-data** (service principal + embed
  token), which works on **any** F-SKU. F64's real significance is org-wide *free* Power BI
  viewing — irrelevant to embedded customers. And real-time reads hit the hot store, which
  doesn't consume Fabric capacity at all.
- **Graceful degradation already exists.** Page 8 falls back to static-snapshot for demos /
  trial-expired windows with zero downstream change.

## 6. Cost shape (verify live Azure pricing before quoting)

- **Event Hubs** — Basic/Standard, small fixed + per-million-events; tiny vs Fabric.
- **Container App** — already paid for the backend; marginal cost of the processor ≈ €0.
- **Hot store** — Postgres already exists; add ADX only if telemetry volume outgrows Postgres.
- **Fabric** — batch compute + storage only; no always-on streaming capacity.

_Exact € figures change by region/tier — pull current Azure pricing when preparing a customer
quote. The architectural point (F64 unnecessary; no always-on Fabric) holds regardless._

## 7. Migration trigger & path

- **Now → first paying IoT customer:** stay in ④. Page 8 demoable at €0.
- **First IoT customer:** stand up Event Hubs + the processor's hot-store sink (①). The
  edge-gateway already pushes to Event Hub; only the **hot-store sink** + the **Page 8
  real-time read** are net-new.
- **If deferred for speed:** ② (single shared F2–F8) — flip the existing EventStream path on
  and accept the always-on cost.
- **Enterprise / data residency:** ③ deploy-to-tenant, customer-owned capacity.

## 8. Open items

- Hot-store choice: Postgres (reuse) vs ADX (scale) — decide once telemetry volume is estimated.
- Processor hosting: reuse the backend Container App vs a dedicated one (isolation).
- Event Hubs retention / back-pressure policy.
- Page 8 real-time read path against the hot store (today Page 8 reads gold Delta only).
