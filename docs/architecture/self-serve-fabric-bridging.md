# EnergyLens — Self-Serve Fabric Bridging (Access Layer 3)

_Status: **PLAN** — proposed 2026-06-06, awaiting founder approval before any build._
_Relates to: [`data-connection-architecture.md`](./data-connection-architecture.md) (tiered ingestion), [`unified-access-model.md`](./unified-access-model.md) (RLS / Nav / Subscription)._

## 1. The bottleneck

Every building is born in **Postgres with a UUID** at onboarding. Its `fabric_building_id`
stays **NULL** until someone **bridges** the building into Microsoft Fabric. Today that
bridge is **100 % manual**: the founder opens `/admin`, runs the medallion notebooks by
hand, then PATCHes a `fabric_building_id` onto the building.

Consequence:

- A new customer **can** self-serve **Tier-1 baseline analytics** — upload a CSV / PDF bill
  → Postgres-side KPIs (EUI, energy, carbon, cost) + the advisor. **No Fabric needed.**
- But the **full Power BI experience** (the 9/10-page reports: forecasting, HVAC analytics,
  battery strategy, IoT monitoring) is gated behind a **human**.

That doesn't scale and blocks true self-onboarding. **Goal (founder, 2026-06-06): make
bridging self-serve and, ideally, AI-guided in-app — as easy as possible.**

## 2. What "bridging" mechanically requires

Going from *pending* (Postgres-only) to *bridged* (live in Fabric) is four steps:

1. **Land data in Bronze.** Push the building's data into a Fabric bronze table. For an
   upload-only building that means its `building_consumption` rows; for a live building the
   agent already streams to Event Hub → EventStream → Lakehouse.
2. **Transform Silver → Gold.** Run the existing medallion notebooks (parameterised by
   building) to clean/normalise (silver) and aggregate to KPIs (gold).
3. **Assign + link the ID.** Mint a `fabric_building_id` (e.g. `B0xx`), write it into the
   gold building dimension (`silver_building_master` / `dim_building`), and update Postgres
   `buildings.fabric_building_id` so the app flips the building from pending → live.
4. **Wire RLS + semantic model.** Add the building to the Power BI RLS mapping so the
   customer sees only their own building, and refresh the semantic model.

## 3. The honest constraint (read this first)

**Analytics depth is bounded by the data a building actually has.** The 9-page reports were
built on a curated demo dataset (hourly sub-metered HVAC, battery scenarios, IoT streams).
A customer who uploaded **12 monthly kWh numbers** cannot populate forecasting / HVAC /
battery / IoT pages — bridging them in would render mostly empty visuals.

The good news: the app **already** handles this honestly via **module-gating** (Pages 8/9
lock with no IoT / battery — see `unified-access-model.md`). So self-serve bridging must be
**data-tier-aware**: unlock exactly the pages the data earns, and say so plainly. This
matches `CLAUDE.md`'s rule — *state assumptions, don't invent unrealistic logic.*

> **"Bridge" ≠ "turn on all 9 pages."** It = *provision the building in Fabric, push
> whatever data it has, unlock the pages that data earns.*

## 4. Mechanism options & trade-offs

| Option | What it is | Pro | Con |
|---|---|---|---|
| **A — Postgres-only "shadow"** | Never bridge SMEs; build more Postgres-computed analytics (trend, YoY, benchmark). Bridge only IoT/battery customers. | Zero Fabric automation, €0 capacity per customer, instant | Two analytics codebases; Postgres can't match Power-BI depth |
| **B — Automated Fabric pipeline** | `POST /buildings/{id}/bridge` → service principal lands data in bronze, triggers the parameterised silver→gold **job** (Fabric Job Scheduler REST), assigns id, wires RLS | True self-serve, real Fabric analytics | Needs SP + capacity **running** (cost), parameterised notebooks, semantic-model auto-refresh, robust error handling |
| **C — Semi-automated "request" queue** | Customer clicks *Unlock full analytics* → writes a `bridge_request` row + notifies founder → founder runs the (parameterised) pipeline with one command → status flips | Low infra, keeps a **human QA gate** (energy-logic correctness), fits trial / startup-credit limits | Not instant; doesn't scale to hundreds |
| **D — AI-guided in-app wizard** | A Copilot flow **on top of** B or C: detects what data the building has, explains in plain language what each tier unlocks, runs a data-readiness check, pre-fills config, then triggers (B) or files (C) | Best UX; honest expectation-setting; the founder's "ideally" | It's a UX layer, **not** a bridging mechanism — still needs B or C underneath |

## 5. Recommended plan — data-tier-aware, phased

The key idea: **the AI wizard (D) is the constant customer experience; the backend matures
from *request* → *automated* underneath it, without changing the UX.**

### Phase 3.0 — Make Tier-1 self-serve excellent + honest  ✅ essentially done
Upload → baseline KPIs + advisor, **no bridge needed**. Clear messaging: *"Your building is
live with baseline analytics. Live monitoring & deep analytics unlock when you connect a
device."* Most SME customers can live here indefinitely. _(Strengthened 2026-06-06: Upload
now lives on the building's own detail page, and the CSV parser is robust to messy EU/TR/US
files.)_

### Phase 3.1 — Self-serve bridge **request** + AI wizard (C + D)  ▶ recommended first build
*Unlock full analytics* CTA on a pending building → an **AI wizard** that:
- runs a **data-readiness check** (what does this building have? what's missing for each page?),
- explains the tiers in plain language and sets honest expectations,
- files a **parameterised `bridge_request`** (building id, data sources, target tier).

The founder approves with one command. Low infra, QA-gated, works on trial / credits.

### Phase 3.2 — Automated pipeline (B) under the same wizard  ◦ later
Once the parameterised notebook + service principal + capacity are stable, flip the wizard
from *request* to **instant bridge**. Same UX; automated backend. Gated by capacity cost.

### Phase 3.3 — Self-healing / continuous  ◦ future
Auto-bridge on a data threshold — e.g. once an agent has streamed 30 days, auto-unlock
forecasting; when battery config arrives, auto-unlock Page 9.

## 6. The AI-guided wizard (the constant UX)

What the Copilot actually does (so "AI-guided" is concrete, not magic):

- **Diagnose** — reads the building's Postgres state (uploaded months? a connected agent?
  battery/solar config?) and computes a per-page readiness score.
- **Explain** — in plain language: *"You have 14 months of meter data → Overview, Trends,
  Benchmark, Targets will be rich. No sub-metering yet → HVAC analytics stays locked until a
  device is connected."*
- **Pre-fill** — assembles the bridge request / pipeline parameters automatically (no forms).
- **Trigger** — files the request (3.1) or runs the bridge (3.2), then watches status and
  reports back when the building goes live.

The "AI" earns its place in **diagnosis + plain-language guidance + config auto-fill** — not
in inventing data.

## 7. Architecture choices explained

- **Request-first (C before B).** Energy-logic correctness is a core project value; a human
  QA gate on the first bridges catches bad data / wrong units before customers see numbers.
  It also avoids running Fabric capacity per signup during the trial / startup-credit window.
- **Service principal later (B).** Automated bridging needs a Fabric SP + a parameterised
  job + semantic-model refresh — real infra worth building **after** the UX and the
  parameterised notebook are proven by 3.1.
- **Module-gating is the safety net.** Because Pages 8/9 already lock without IoT/battery,
  an over-eager bridge can't expose empty premium pages — the gate degrades gracefully.
- **Two cleaning layers stay (see §8).** Parser-at-the-door (Postgres) + medallion-silver
  (Fabric) are complementary, not redundant.

## 8. Where messy data gets cleaned (parser vs medallion)

There are **two** cleaning points, in **two** layers — a common point of confusion:

- **At the door — Postgres-side, _today_.** When a CSV/PDF is uploaded, the parser resolves
  the mess *there*: EU vs US numbers (`1.234,56` vs `1,234.56`), month names
  (`Januar`/`Şubat`), delimiter (`;` `,` tab `|`), quotes, BOM. Result: structured rows
  (`YYYY-MM`, kWh) land in Postgres. **This is not Fabric** — uploaded baselines go to
  Postgres (Tier 1), so the cleaning that matters for uploads lives in the parser.
- **In the medallion — Fabric, _once bridged_.** **Bronze** = raw as-ingested (audit trail);
  **Silver** = cleansed/normalised (type coercion, unit standardisation to °C/kWh, dedup,
  gap-fill, outlier flags); **Gold** = business aggregates (KPIs). Fabric's silver layer
  **does** clean — but only data that **enters** Fabric.

So *"won't Fabric clean it?"* is **true but partial**: Fabric cleans what reaches it. In our
architecture the uploaded baseline doesn't reach Fabric (yet), so we clean at the door. The
two layers complement each other — the parser makes data **parseable** (so it can land in
bronze at all); silver makes it **semantically clean** (units/time/dedup). Garbage that
isn't parseable never lands cleanly in bronze, which is exactly why the robust parser
matters even in a Fabric-first world.

## 9. Approval gate (founder)

Proposed: **build Phase 3.1 first** (request + AI wizard), defer 3.2/3.3 until the
parameterised pipeline + capacity story are ready.

Open questions for Mert:

1. **Approve the data-tier-aware framing?** (Bridge unlocks only the pages the data earns —
   never a blanket "all 9 pages.")
2. **3.1 request-queue first, or go straight to 3.2 automated?** (Trade-off: human QA gate +
   €0 trial cost, vs instant but needs SP + running capacity.)
3. **Where does the wizard live?** A step in `/onboarding`, an action on the building detail
   page, or inside the in-app Copilot? (Leaning: an "Unlock full analytics" panel on the
   pending building detail page, powered by the Copilot.)


---

## 10. Phase 2 build — full report set per bridge (2026-06-13) ✅ built

Phase 3.2 originally bridged only the **energy baseline** (`gold_kpi_monthly/daily`): a
bridged building went live with KPIs but GHG / GEG / recommendation reports stayed empty.
Phase 2 extends the bridge to populate the **full report set** for the one new building, by
**reusing the existing batch notebooks** (single source of truth — no logic duplication, no
drift), each made runnable for a single building.

### 10.1 Notebook parameterisation (`BRIDGE_BUILDING_ID`)

Three batch notebooks gained an optional **parameter cell** `BRIDGE_BUILDING_ID = ""`:

| Notebook | Reads | Scoped write |
|---|---|---|
| `09_ghg_scope_engine` | `gold_kpi_daily`, dim, ref factors | MERGE on `(building_id, year_month)` |
| `05_compliance_checker` | dim U-values/year, `gold_kpi_monthly` | MERGE on `building_id` (+ `rule_code` for issues) |
| `06_recommendation_engine` | dim, `gold_kpi_monthly`, compliance | **delete-by-building + append** (multi-row/building) |

- **Empty (default) → full batch, byte-for-byte unchanged** — the daily pipeline is unaffected.
- **Set (e.g. `B012`) → single-building incremental:** reads filtered to that building, write
  touches only its rows. Every other customer's gold rows stay intact (key-matched MERGE /
  scoped delete — never a table overwrite).

### 10.2 Dimension carries the compliance inputs

`40_bridge_baseline` now writes the envelope/fuel fields into `silver_building_master` using
the **exact** column names 05/09 read (`wall_u_value`, `roof_u_value`, `window_u_value`,
`insulation_year`, `year_built`, `energy_certificate`, `has_gas_heating`). Without these the
GEG check reads nulls and stays locked. Values flow from the onboarding wizard →
orchestrator `_building_meta` → notebook param.

### 10.3 Orchestrator chain (best-effort reports)

`bridge_orchestrator` Step 3 runs, in order:

```
40 baseline (REQUIRED) -> 09 GHG -> 05 GEG/compliance -> 06 recommendations
```

- **Baseline required** — a failure aborts the bridge (no `fabric_building_id` write-back).
- **Reports best-effort** — a failure is a `warning` step; the chain continues and the
  building still goes live with the baseline + whatever succeeded. The readiness map / Data
  Score then shows which reports are available. A transient GHG hiccup can't block go-live.
- A report notebook whose **env id is unset is cleanly skipped** — wire ids in over time.
- `fabric_jobs.trigger_notebook(id, params)` is the generic primitive; `trigger_bridge_notebook`
  is now a thin wrapper over it.

### 10.4 New env vars (all optional)

```bash
FABRIC_GHG_NOTEBOOK_ID=                 # 09_ghg_scope_engine item GUID
FABRIC_COMPLIANCE_NOTEBOOK_ID=          # 05_compliance_checker item GUID
FABRIC_RECOMMENDATION_NOTEBOOK_ID=      # 06_recommendation_engine item GUID
```

Unset -> that report is skipped (baseline still bridges). See `fabric-bridge-setup.md` 5b, 7.

### 10.5 Trigger model (unchanged: founder-in-loop now, full-auto behind a flag)

`BRIDGE_AUTOMATION_ENABLED=false` keeps the `/admin` "Go" gate — the safety valve at pilot
scale. Flipping to full-auto later is a flag + a queue, no change to the chain. That decision
is a **capacity/cost** one (always-on EUR vs on-demand resume + queue + abuse control).

### 10.6 Energy honesty

Bridged reports inherit each notebook's **stated assumptions** and `data_grade` /
`disclosure_grade` flags (e.g. 09's Scope-1 gas proxy when no metered gas exists; 06's plus or
minus 30% estimated band). Nothing is fabricated — bridged rows are flagged baseline/estimated
where the underlying data is.
