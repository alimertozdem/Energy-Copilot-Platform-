/**
 * Portfolio bulk import — client helpers (CSV → typed rows → POST /buildings/bulk).
 *
 * The CSV is parsed in the browser into normalized building rows so the user can
 * preview + fix before committing. Tolerant of real-world exports: strips a BOM,
 * auto-detects the delimiter (, ; tab |), respects quoted fields, and matches
 * header aliases (EN/DE) case-insensitively. Types mirror backend
 * app/schemas/buildings.py (BulkBuildingRow / BulkImportResponse).
 *
 * building_id is never sent — the backend creates building shells in the caller's
 * org (admin/manager gate), each with the 'meters' module enabled and no Fabric
 * data yet. A baseline / live source is added per building afterwards.
 */

export const BUILDING_TYPES = [
  "Office",
  "Retail",
  "Hotel",
  "Healthcare",
  "Logistics",
  "Datacenter",
  "Residential",
  "Mixed",
] as const

const EPC_CLASSES = ["A", "B", "C", "D", "E", "F", "G"] as const

export type BulkBuildingRow = {
  name: string
  building_type: string | null
  city: string | null
  country_code: string | null
  floor_area_m2: number | null
  construction_year: number | null
  epc_class: string | null
  heating_system: string | null
}

/** A parsed row plus UI metadata (validity + non-fatal issues). */
export type ParsedRow = BulkBuildingRow & {
  line: number // 1-based source line (for error messages)
  valid: boolean // false → excluded from import (name missing)
  issues: string[] // soft warnings (e.g. unknown building type → blanked)
}

export type ParseResult = {
  rows: ParsedRow[]
  headerError: string | null // fatal (e.g. no recognizable header) → blocks import
}

export type BulkImportRowResult = {
  index: number
  name: string
  ok: boolean
  id: string | null
  error: string | null
}

export type BulkImportResponse = {
  created: number
  failed: number
  results: BulkImportRowResult[]
}

export type Result<T> = { ok: true; data: T } | { ok: false; error: string }

// Header alias → canonical field. Lower-cased, punctuation-stripped on lookup.
const HEADER_ALIASES: Record<string, keyof BulkBuildingRow> = {
  name: "name",
  building: "name",
  buildingname: "name",
  gebaeude: "name",
  gebäude: "name",
  objekt: "name",
  type: "building_type",
  buildingtype: "building_type",
  typ: "building_type",
  city: "city",
  stadt: "city",
  ort: "city",
  country: "country_code",
  countrycode: "country_code",
  land: "country_code",
  area: "floor_area_m2",
  floorarea: "floor_area_m2",
  flooraream2: "floor_area_m2",
  m2: "floor_area_m2",
  flaeche: "floor_area_m2",
  fläche: "floor_area_m2",
  year: "construction_year",
  yearbuilt: "construction_year",
  constructionyear: "construction_year",
  baujahr: "construction_year",
  epc: "epc_class",
  epcclass: "epc_class",
  energieausweis: "epc_class",
  heating: "heating_system",
  heatingsystem: "heating_system",
  heizung: "heating_system",
}

const norm = (h: string) => h.trim().toLowerCase().replace(/[^a-z0-9äöü]/g, "")

/** Split one CSV line honoring quotes. */
function splitLine(line: string, delim: string): string[] {
  const out: string[] = []
  let cur = ""
  let inQuotes = false
  for (let i = 0; i < line.length; i++) {
    const c = line[i]
    if (inQuotes) {
      if (c === '"') {
        if (line[i + 1] === '"') {
          cur += '"'
          i++
        } else inQuotes = false
      } else cur += c
    } else if (c === '"') inQuotes = true
    else if (c === delim) {
      out.push(cur)
      cur = ""
    } else cur += c
  }
  out.push(cur)
  return out.map((s) => s.trim())
}

function detectDelim(headerLine: string): string {
  const candidates = [",", ";", "\t", "|"]
  let best = ","
  let bestCount = -1
  for (const d of candidates) {
    const n = headerLine.split(d).length
    if (n > bestCount) {
      bestCount = n
      best = d
    }
  }
  return best
}

function matchType(raw: string): { value: string | null; issue: string | null } {
  const v = raw.trim()
  if (!v) return { value: null, issue: null }
  const hit = BUILDING_TYPES.find((t) => t.toLowerCase() === v.toLowerCase())
  return hit
    ? { value: hit, issue: null }
    : { value: null, issue: `unknown type "${v}" — left blank` }
}

function matchEpc(raw: string): { value: string | null; issue: string | null } {
  const v = raw.trim().toUpperCase()
  if (!v) return { value: null, issue: null }
  return (EPC_CLASSES as readonly string[]).includes(v)
    ? { value: v, issue: null }
    : { value: null, issue: `EPC "${raw.trim()}" not A–G — left blank` }
}

function num(raw: string): number | null {
  let t = (raw ?? "").replace(/[^\d.,-]/g, "")
  if (!t || !/\d/.test(t)) return null
  if (t.includes(".") && t.includes(",")) {
    t =
      t.lastIndexOf(",") > t.lastIndexOf(".")
        ? t.replace(/\./g, "").replace(",", ".")
        : t.replace(/,/g, "")
  } else if (t.includes(",")) t = t.replace(",", ".")
  const n = parseFloat(t)
  return Number.isFinite(n) ? n : null
}

/** Parse a CSV string into normalized, preview-ready building rows. */
export function parseBuildingsCsv(text: string): ParseResult {
  const clean = text.replace(/^﻿/, "")
  const lines = clean.split(/\r\n|\n|\r/).filter((l) => l.trim() !== "")
  if (lines.length === 0) return { rows: [], headerError: "The file is empty." }

  const delim = detectDelim(lines[0])
  const rawHeaders = splitLine(lines[0], delim)
  const colMap: (keyof BulkBuildingRow | null)[] = rawHeaders.map(
    (h) => HEADER_ALIASES[norm(h)] ?? null
  )
  if (!colMap.includes("name")) {
    return {
      rows: [],
      headerError:
        'No "name" column found. The first row must be a header — include at least a "name" column.',
    }
  }

  const rows: ParsedRow[] = []
  for (let i = 1; i < lines.length; i++) {
    const cells = splitLine(lines[i], delim)
    const rec: BulkBuildingRow = {
      name: "",
      building_type: null,
      city: null,
      country_code: null,
      floor_area_m2: null,
      construction_year: null,
      epc_class: null,
      heating_system: null,
    }
    const issues: string[] = []
    colMap.forEach((field, idx) => {
      if (!field) return
      const raw = (cells[idx] ?? "").trim()
      if (field === "name") rec.name = raw.slice(0, 255)
      else if (field === "city") rec.city = raw ? raw.slice(0, 100) : null
      else if (field === "heating_system") rec.heating_system = raw ? raw.slice(0, 40) : null
      else if (field === "country_code") {
        const cc = raw.toUpperCase().replace(/[^A-Z]/g, "")
        if (raw && cc.length !== 2) issues.push(`country "${raw}" is not a 2-letter code — left blank`)
        rec.country_code = cc.length === 2 ? cc : null
      } else if (field === "building_type") {
        const r = matchType(raw)
        rec.building_type = r.value
        if (r.issue) issues.push(r.issue)
      } else if (field === "epc_class") {
        const r = matchEpc(raw)
        rec.epc_class = r.value
        if (r.issue) issues.push(r.issue)
      } else if (field === "floor_area_m2") {
        rec.floor_area_m2 = num(raw)
      } else if (field === "construction_year") {
        const n = num(raw)
        rec.construction_year = n != null ? Math.round(n) : null
      }
    })
    const valid = rec.name.length > 0
    if (!valid) issues.unshift("missing name — row skipped")
    rows.push({ ...rec, line: i + 1, valid, issues })
  }
  return { rows, headerError: null }
}

/** A small example CSV the user can download as a starting template. */
export function templateCsv(): string {
  return [
    "name,building_type,city,country_code,floor_area_m2,construction_year,epc_class,heating_system",
    "Hauptstraße 12,Residential,Berlin,DE,2400,1998,D,gas_boiler",
    "Büro Mitte,Office,Berlin,DE,5200,2008,C,district_heating",
    "Lager Süd,Logistics,München,DE,8800,2015,B,heat_pump",
  ].join("\n")
}

/** Submit the chosen rows. Only valid rows should be passed in. */
export async function importBuildings(
  rows: BulkBuildingRow[]
): Promise<Result<BulkImportResponse>> {
  try {
    const res = await fetch("/api/buildings/bulk", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ rows }),
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) {
      const detail =
        data && typeof data === "object" && "detail" in data
          ? String((data as { detail: unknown }).detail)
          : `Request failed (${res.status})`
      return { ok: false, error: detail }
    }
    return { ok: true, data: data as BulkImportResponse }
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) }
  }
}
