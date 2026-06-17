# CRREM: swapping in the official licensed pathways

The app ships **illustrative** 1.5 °C decarbonisation pathways so the stranding /
CRREM capability works today. The **method** is CRREM-standard; only the curve
*values* are placeholders. This note is the one-operation procedure to replace them
with the official licensed dataset.

## Why it's illustrative today

Embedding the official CRREM pathways in commercial software requires a **CRREM
License Partner agreement** (the curves are licensed/copyrighted). Obtaining that is
a commercial step — not code. Until then we use clearly-labelled indicative anchors.
Do **not** paste official CRREM numbers into the repo without the agreement.

## Single source of truth

All pathway data lives in `web-app/frontend/lib/crrem.ts` in one object:

```ts
export let CRREM_DATASET: CrremDataset = { source: "illustrative", ... }
```

Every consumer — `pathwayValue`, `pathwayPoints`, `pathwayStart`, the stranding
functions, the /compliance visuals, the report PDFs, and the building Heating & HVAC
stranding panel — reads from this object. Change it once; everything follows.

## Data shape to drop in

```ts
type CrremCurve = {
  anchors?: [number, number]        // [start@startYear, end@endYear] — illustrative shape
  points?: Record<number, number>   // year -> kgCO2/m2.yr — OFFICIAL shape (takes precedence)
}

type CrremDataset = {
  source: "illustrative" | "official"
  version: string                   // e.g. "CRREM-2024.1"
  scenario: string                  // "1.5C"
  metric: string                    // "carbon_kgco2_m2"
  startYear: number
  endYear: number
  defaultRegion: string             // "DEFAULT" fallback when a country is absent
  regions: Record<string, Record<string, CrremCurve>>  // region -> assetType -> curve
}
```

Official curves are **per country** and **year-indexed**, so use `points` (not
`anchors`) and one entry per ISO country code, e.g.:

```ts
regions: {
  DE: {
    Office:      { points: { 2025: 41, 2030: 28, 2040: 11, 2050: 4 } },
    Residential: { points: { 2025: 38, 2030: 25, 2040: 9,  2050: 3 } },
    _default:    { points: { 2025: 45, 2030: 30, 2040: 12, 2050: 5 } },
    // ...all asset types...
  },
  FR: { /* ... */ },
  // ...
}
```

`pathwayValue(type, year, region)` linearly interpolates between the surrounding
year points; `region` falls back to `defaultRegion` when a country is missing, and
asset type falls back to `_default`.

## The swap (one operation)

Either replace the `CRREM_DATASET` literal in `lib/crrem.ts`, **or** load it at app
start without touching the literal:

```ts
import { loadOfficialCrrem } from "@/lib/crrem"
import officialCrrem from "@/data/crrem-official.json" // licensed, git-ignored

loadOfficialCrrem({ ...officialCrrem, source: "official" })
```

Keep the licensed JSON **out of version control** (git-ignore it) unless the license
permits redistribution.

## What updates automatically

- `crremSource()` returns `"official"`, so the UI captions flip from
  "Illustrative pathways" to "Official CRREM pathways (<version>)" on both
  `/compliance` (CrremStranding) and the building Heating & HVAC stranding panel.
- Stranding years, sparklines, and report PDFs recompute against the official curves.
- Per-country accuracy turns on automatically once buildings pass a `region`/country
  to `pathwayValue` (wire `building.country_code` at the call sites when going live).

## Asset-type keys

`Office, Retail, Logistics, Warehouse, Hotel, Healthcare, Education, Data_Center, Lab`
plus `_default`. Note the app's building types use `Datacenter` (no underscore) and
include `Residential`/`Mixed`; add those keys to each region (and align the naming)
when loading official data so they don't fall through to `_default`.
