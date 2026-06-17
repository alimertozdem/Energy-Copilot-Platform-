# EnergyLens — Estimation Engine — Architecture Brief

> **Status:** DRAFT v0.2 — pending product-owner approval (energy-domain gate, Mert). BMAD phase: **Architecture**.
> **Scope:** the transparent data-estimation engine that is the **shared core** under all three commercial
> pillars (multi-segment B2B deep-analysis · commercial large-site · residential per-unit).
> **Cost model:** **two tiers, one engine.** Tier A (screening) is **Postgres-only, €0**. Tier B (deep
> analysis) **feeds Microsoft Fabric** and runs only for paid customers (batch, pausable capacity).
> **Energy-honesty contract:** every output is a labelled estimate — a **range**, a **method**, a
> **confidence**, and **editable** inputs. Never a single false-precise number.

> **v0.2 revision (2026-06-17, per product-owner):** the engine must (a) draw on **all platform data
> sources**, not one pillar's inputs, and (b) **feed Fabric** for the deep-analysis tier. This brief
> reconciles both with the standing **Free = Postgres-only / €0** constraint — see §0 and §2.

---

## 0. The honest starting point (why this document exists)

Three verified facts frame every decision below:

1. **The engine that exists today is shallow.** `web-app/backend/app/services/baseline_estimate.py`
   is a **7-entry hardcoded intensity dict** (building type → EUI band × floor area, then × real
   tariff/grid factor). It ignores building **vintage**, **climate**, any **partial bill** the customer
   already holds, and carries **no confidence score**. *[Kesin — verified in code, 2026-06-17]*
2. **The richer reference knowledge lives in Fabric, not Postgres.** `ref_building_type_profiles`
   (9 archetypes + load profiles + heating shares) and `ref_envelope_u_by_vintage` (era → U-values)
   are Fabric Delta tables. *[Kesin]*
3. **But the platform's gold data is already mirrored INTO Postgres.** The Fabric→Postgres
   materialization (`mv_` tables in Supabase, shipped 2026-06-16) means the engine can read most
   platform data **without a live Fabric bridge** — which is exactly how we satisfy "cover all our
   databases' data" while keeping the free path at €0. *[Kesin mv_ exists · Muhtemel coverage
   sufficient — to confirm in the Data phase]*

**The tension to resolve (stated first).** The product-owner wants the engine to *cover all data* and
*feed Fabric*. Taken naively that breaks the **Free = Postgres-only, €0** rule (unit-economics review).
**Reconciliation:** split the engine into two tiers — a free Postgres-only screening tier that reads the
`mv_` mirror (so it already "covers all data"), and a paid deep tier that feeds Fabric (batch, pausable,
revenue-justified). Both wants are met; the margin is not touched.

**Consequence for build order.** "Make the engine the best it can be" is mostly **(a) port the reference
knowledge into Postgres, (b) stack evidence layers, (c) wire a gated feed to Fabric** — not a green-field
build. The dominant accuracy lever remains **anchoring to whatever partial bill the customer already has**;
exotic data acquisition (satellite, 3D, footprint scraping) before bill-anchoring is the feature-trap.

---

## 1. Requirements

### Functional
- From partial / missing inputs (type, area, year built, location, optional partial bill, optional tariff
  override) produce: **annual final energy (kWh/yr)**, **EUI (kWh/m²/yr)**, **annual cost (€)**, **annual
  CO₂ (kg)** — each as a **range** with a **confidence tier** and a **method string**.
- **Cover all platform data:** read a building's available evidence from ANY source — uploaded bills,
  building metadata, reference tables, and `mv_` mirrored Fabric gold (all in Postgres); plus live Fabric
  gold on the deep tier only.
- **Refine progressively**: each new piece of evidence narrows the range and raises confidence.
- **Feed Fabric (Tier B):** hand assembled + estimated inputs to Fabric notebooks for deep physics /
  simulation, for paid customers, as a batch job.
- Every input is **editable**; re-running is **deterministic**.
- Serve all three pillars through **thin output adapters** — no pillar-specific math in the core.

### Non-functional
- **Free / screening path = €0:** Postgres-only, deterministic Python, no live Fabric, no paid API, no
  LLM in the numeric path. *(Load-bearing for the Free tier's margin.)*
- **Deep path = revenue-justified:** uses **pausable** Fabric capacity (batch, not always-on), gated to
  paid tiers — consistent with the ① Decouple principle.
- **Fast & synchronous** on Tier A (pure functions over a few rows + small reference tables, ~ms).
- **Auditable** — every number traceable to a formula + a source row (the B2B trust currency).

### Constraints
- Solo founder, time-boxed, **€0** for the free path.
- **Build on** `baseline_estimate.py`, `baseline_kpi.py`, `reference_factors`, and the existing `mv_`
  mirror — do not rebuild.
- **DE-first.** **No open public EPC register exists for Germany** (Germany is the only EU country
  without an EPC database; a central one is only *planned*, ~2026). Footprint **height** data is sparse
  (~20% of Microsoft ML footprints). *[Kesin — web-verified 2026-06-17]*
- Comprehensive **data intake** is cheap and fine; comprehensive **output adapters all at once** is the
  feature-trap. Design broad, **validate on one reference set first**.

---

## 2. High-level design — assembler → Tier A pipeline → gated Tier B feed

```
                       ┌─ SOURCE ASSEMBLER (a building's available evidence) ──────────┐
INPUT / metadata ─────▶│ uploaded bills · building meta · reference tables ·           │
                       │ mv_ mirrored Fabric gold (Postgres)   [+ live Fabric gold,    │
                       │                                        deep tier only]        │
                       └───────────────────────────────┬──────────────────────────────┘
                                                        ▼
  ╔════════════════ TIER A — SCREENING (free · Postgres-only · €0) ═══════════════════╗
  ║ L0 archetype prior   type → EUI band × area              ref_archetype_intensity  ║
  ║ L1 vintage adjust    year_built → era → shift band       ref_vintage_eui_factor   ║
  ║ L2 HDD normalise     region → HDD → scale HEATING share  ref_climate_hdd (free)   ║
  ║ L3 geometry fallback area missing? footprint × storeys   MS/OSM (gap-fill only)   ║
  ║ L4 partial-bill ANCHOR any real kWh/€ → anchor + blend   ↓↓ strongest lever       ║
  ║ L5 EPC anchor        region-gated (UK yes · DE no)                                ║
  ║ OUTPUT  energy {low,point,high} · confidence · method · editable                  ║
  ║         cost = energy × tariff(country,year)   CO₂ = energy × grid_factor(...)     ║
  ╚═══════════════════════════════════════╤═══════════════════════════════════════════╝
                                          │  (paid / deep tier only — batch, pausable)
                                          ▼
  ╔════════════════ TIER B — DEEP ANALYSIS (paid · feeds Fabric) ═════════════════════╗
  ║ engine hands assembled + estimated inputs → Fabric notebooks:                     ║
  ║ retrofit physics (ΔU×A×Gt÷η) · NPV / scenario sim · anomaly · battery dispatch     ║
  ║ → deeper, simulation-grade outputs (still indicative until a real on-site audit)  ║
  ╚═══════════════════════════════════════════════════════════════════════════════════╝
```

Tier A's cost / CO₂ step **reuses `reference_factors` exactly as today** (real tariff + grid factor),
keeping the documented *electricity-equivalent proxy* caveat for mixed-fuel (e.g. gas-heated) buildings.

### Tier A vs Tier B

| | **Tier A — Screening** | **Tier B — Deep analysis** |
|---|---|---|
| Who | Free / all users | Paid customers |
| Compute | Postgres, deterministic Python | Fabric (Spark notebooks) |
| Cost | **€0 marginal** | Pausable F-SKU, batch, revenue-justified |
| Reads | bills · meta · ref tables · `mv_` gold | + live Fabric gold |
| Output | range + confidence + method | physics / simulation / scenarios |
| Latency | synchronous (~ms) | batch (minutes) |

---

## 3. Storage — port reference knowledge into Postgres; reuse the mv_ mirror

To keep Tier A Fabric-independent, mirror the reference knowledge as small, **versioned** Postgres tables
(one seed script = one source of truth), and **reuse the existing `mv_` mirror** for platform gold data:

| Table | Holds | Sourced from |
|---|---|---|
| `ref_archetype_intensity` | type → EUI low/typical/high · heating share · monthly shape | `ref_building_type_profiles` (Fabric) + approved EUI ranges |
| `ref_vintage_eui_factor` | construction era → EUI multiplier band | `ref_envelope_u_by_vintage` (Fabric) |
| `ref_climate_hdd` | region / postcode → HDD normal (heating degree-days) | DWD / open-meteo (free) |
| *(reuse)* `reference_factors` | tariff + grid emission factor by country/year | already in Postgres |
| *(reuse)* `mv_*` gold mirror | real KPIs/consumption where a building is already bridged | Fabric→Postgres materialization (2026-06-16) |

Porting is a few hundred rows. *[Muhtemel]* It removes today's "Fabric holds the intelligence, Postgres
holds a 7-line dict" split and lets Tier A do archetype + vintage + climate reasoning with **zero** live
Fabric dependency.

---

## 4. KPIs the engine emits (energy-kpi-designer template)

**KPI — Estimated EUI (energy use intensity)** — *the exemplar; energy, cost & CO₂ follow the same discipline.*
- **Business purpose:** screen a building's energy performance when little/no data exists; rank a
  portfolio; flag retrofit candidates.
- **Formula:** `EUI = annual_final_energy_kWh / heated_floor_area_m²`, where annual energy is the archetype
  band (L0) shifted by vintage (L1), heating-portion climate-normalised (L2), then anchored to any partial
  bill (L4).
- **Required inputs:** building type *(or default)*, floor area *(or footprint-derived, L3)*; optional year
  built, region HDD, partial bill.
- **Grain:** per building, annual (run-rate).
- **Assumptions:** archetype bands are EU typicals (total final energy = heating + electricity); only the
  **heating share** is HDD-sensitive (base/plug load is not); a real building can sit ±30%+ inside its type
  → hence a band, never a point. *[Tahmin — archetype]*
- **Interpretation:** compare against the archetype's good/average/poor benchmark; distance from the
  median signals retrofit upside.
- **Validation:** backtest vs known-consumption buildings (§6).
- **Limitations:** **not** weather-corrected unless L2 fired; **not** fuel-split until a bill arrives;
  Datacenter deliberately **not modelled** (IT load dominates → no honest area estimate).

*Estimated annual energy*, *cost (€)* and *CO₂ (kg)* reuse the same band + real tariff/grid factors,
carrying the mixed-fuel proxy caveat. All four are emitted as `{low, point, high}` with a shared
confidence tier.

---

## 5. Trade-offs (explicit)

- **Deterministic vs ML** → **deterministic.** Explainable, €0, and we have no labelled training set yet.
- **"Cover all data" via live Fabric vs the mv_ mirror** → **mv_ mirror.** Tier A reads platform gold from
  Postgres, so it covers all data **without** a live bridge → €0 holds. Live Fabric read is Tier B only.
- **Feed Fabric: batch vs always-on** → **batch + pausable**, paid tier only. Protects the free margin.
- **Footprint auto-fetch vs user-entered area** → **prefer user area; footprint is a gap-filler only**
  (heights sparse → wide band).
- **Single shared engine vs per-pillar engines** → **single** (the thesis). Risk: over-generalisation.
  Mitigation: thin per-pillar **output adapters**; core math stays pillar-agnostic; validate on one set.
- **EPC as a data source** → **region-gated.** DE has none today; the DE path must not depend on it.

---

## 6. Validation — backtest (honesty made measurable)

On buildings with known consumption (`B001–B003`, `B011`, plus public Heizspiegel-type benchmarks), run
Tier A **with the bill withheld** and compare the predicted band to actual. Report: (a) point-estimate
error %, (b) **calibration** — did actual fall inside the predicted band, per confidence tier. A confidence
tier whose observed hit-rate doesn't match its claim gets recalibrated. This is the credibility proof a B2B
buyer will demand, and the **first concrete target** (a technical anchor, not a commercial pillar lock-in).

---

## 7. What I'd revisit as it grows

- Add **L5 EPC anchor** for DE when the planned central register lands.
- Expand the **Tier B Fabric feed** to more notebooks (simulation, anomaly, battery) as paid demand appears.
- **Recalibrate archetype bands** against accumulated real customer consumption (the data flywheel).

---

## 8. Open decisions (need product-owner approval)

1. **Tier split.** Confirm: Tier A free/Postgres-only (reads `mv_` mirror to "cover all data"); Tier B
   feeds Fabric, paid + batch + pausable. *(This is the reconciliation of "cover all data + feed Fabric"
   with "€0 free".)*
2. **No commercial beachhead lock.** Engine designed broad (all sources, both tiers); thin output adapters
   added later. First concrete target = the §6 **backtest** on existing buildings.
3. **EPC handling.** DE EPC treated as unavailable; rely on L0–L4. EPC-anchor = UK-only / future-DE.
4. **Footprint.** Gap-filler fallback only — not a Day-1 auto-fetch dependency.

> On approval, the next BMAD step is **Data**: input schema + the Postgres reference tables in §3 +
> confirming `mv_` gold coverage.
