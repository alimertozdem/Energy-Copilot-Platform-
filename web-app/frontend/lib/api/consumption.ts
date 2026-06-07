/**
 * Consumption baseline (CSV / bill upload) — client helpers.
 *
 * The CSV is parsed in the browser into normalized monthly rows, then POSTed as
 * JSON to /api/buildings/{building_id}/consumption (a Next proxy that forwards
 * the session token). building_id is the Postgres UUID, so this works for
 * buildings still pending a Fabric bridge (fabric_building_id NULL).
 *
 * The parser is deliberately tolerant of messy real-world exports: it strips a
 * BOM, auto-detects the delimiter (, ; tab |), respects quoted fields, reads
 * EU (1.234,56) and US (1,234.56) numbers, and recognises EN/DE/TR month names
 * — so a German "Januar 2024;1.234,5" or a Turkish "Şubat 2024" both parse.
 */
export type ConsumptionSummary = {
  months: number
  period_start: string | null
  period_end: string | null
  total_kwh: number
  total_cost_eur: number | null
  avg_monthly_kwh: number | null
}

export type ConsumptionRow = {
  period: string // YYYY-MM
  energy_kwh: number
  cost_eur?: number | null
}

type Result<T> = { ok: true; data: T } | { ok: false; error: string }

// Month name -> month number (EN / DE / TR). Used for "Januar 2024" / "Şubat 2024".
const MONTHS: Record<string, number> = {
  january: 1, januar: 1, ocak: 1,
  february: 2, februar: 2, "şubat": 2, subat: 2,
  march: 3, "märz": 3, marz: 3, mart: 3,
  april: 4, nisan: 4,
  may: 5, mai: 5, "mayıs": 5, mayis: 5,
  june: 6, juni: 6, haziran: 6,
  july: 7, juli: 7, temmuz: 7,
  august: 8, "ağustos": 8, agustos: 8,
  september: 9, "eylül": 9, eylul: 9, sept: 9,
  october: 10, oktober: 10, ekim: 10, okt: 10,
  november: 11, "kasım": 11, kasim: 11,
  december: 12, dezember: 12, "aralık": 12, aralik: 12, dez: 12,
  jan: 1, feb: 2, mar: 3, apr: 4, jun: 6, jul: 7, aug: 8, sep: 9, oct: 10, nov: 11, dec: 12,
}

/** Normalize a free-form date/period cell to "YYYY-MM", or null if unparseable. */
function normalizePeriod(s: string): string | null {
  const v = (s ?? "").trim()
  if (!v) return null
  let m = v.match(/(20\d{2}|19\d{2})[-/.](\d{1,2})\b/) // 2024-03 / 2024/3
  if (m && +m[2] >= 1 && +m[2] <= 12) return `${m[1]}-${m[2].padStart(2, "0")}`
  m = v.match(/\b(\d{1,2})[-/.](20\d{2}|19\d{2})\b/) // 03/2024
  if (m && +m[1] >= 1 && +m[1] <= 12) return `${m[2]}-${m[1].padStart(2, "0")}`
  // Month name (EN/DE/TR) + a 4-digit year, in any order. Token-based so the
  // Turkish/German accented names match (JS \b is unreliable around ş/ä/ı).
  const low = v.toLowerCase()
  const ym = low.match(/(?:19|20)\d{2}/)
  if (ym) {
    for (const tok of low.split(/[^\p{L}\p{N}]+/u)) {
      if (MONTHS[tok] != null) return `${ym[0]}-${String(MONTHS[tok]).padStart(2, "0")}`
    }
  }
  const d = new Date(v)
  if (!Number.isNaN(d.getTime())) {
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`
  }
  return null
}

/** Parse a number from a cell, handling EU (1.234,56) and US (1,234.56). */
function num(s: string): number {
  let t = (s ?? "").replace(/[^\d.,-]/g, "")
  if (!t || !/\d/.test(t)) return NaN
  if (t.includes(".") && t.includes(",")) {
    t =
      t.lastIndexOf(",") > t.lastIndexOf(".")
        ? t.replace(/\./g, "").replace(",", ".") // 1.234,56 -> 1234.56
        : t.replace(/,/g, "") // 1,234.56 -> 1234.56
  } else if (t.includes(",")) {
    t = t.split(",").length > 2 || /^\d{1,3}(,\d{3})+$/.test(t) ? t.replace(/,/g, "") : t.replace(",", ".")
  } else if (t.includes(".")) {
    if (t.split(".").length > 2 || /^\d{1,3}(\.\d{3})+$/.test(t) || /^\d+\.\d{3}$/.test(t)) {
      t = t.replace(/\./g, "") // 1.234 (EU thousands) -> 1234
    }
  }
  return parseFloat(t)
}

/** Pick the delimiter that splits the header into the most fields. */
function detectDelim(line: string): string {
  let best = ","
  let bestN = -1
  for (const d of [";", ",", "\t", "|"]) {
    const n = line.split(d).length - 1
    if (n > bestN) {
      bestN = n
      best = d
    }
  }
  return best
}

/** Split a CSV line on the delimiter, respecting double-quoted fields. */
function splitCsvLine(line: string, delim: string): string[] {
  const out: string[] = []
  let cur = ""
  let inQ = false
  for (let i = 0; i < line.length; i++) {
    const ch = line[i]
    if (ch === '"') {
      if (inQ && line[i + 1] === '"') {
        cur += '"'
        i++
      } else {
        inQ = !inQ
      }
    } else if (ch === delim && !inQ) {
      out.push(cur)
      cur = ""
    } else {
      cur += ch
    }
  }
  out.push(cur)
  return out.map((c) => c.trim().replace(/^"|"$/g, ""))
}

/**
 * Pick the column holding the kWh *value* by scoring, not first-match — so a
 * categorical header like "energy_type" never beats "consumption_kwh".
 */
function pickKwhColumn(header: string[]): number {
  let best = -1
  let bestScore = 0
  header.forEach((h, i) => {
    let score = 0
    if (/kwh/.test(h)) score = 4
    else if (/consumption|verbrauch|menge|t[üu]ketim/.test(h)) score = 3
    else if (/energy|enerji/.test(h)) score = 2
    // Penalise obviously-categorical columns ("energy_type", "meter_id", …).
    if (score > 0 && /type|id|name|source|status|unit|meter/.test(h)) score -= 2
    if (score > bestScore) {
      bestScore = score
      best = i
    }
  })
  return best
}

/**
 * Parse a consumption CSV into monthly rows. Tolerant: BOM, delimiter, quotes,
 * EU/US numbers, EN/DE/TR month names. Detects a date/period column and a kWh
 * column (plus optional cost) by header keywords; skips rows it can't read.
 */
export function parseConsumptionCsv(text: string): {
  rows: ConsumptionRow[]
  errors: string[]
} {
  const clean = (text ?? "").replace(/^﻿/, "")
  const lines = clean.split(/\r?\n/).map((l) => l.trim()).filter(Boolean)
  if (lines.length < 2) {
    return { rows: [], errors: ["Need a header row and at least one data row."] }
  }
  const delim = detectDelim(lines[0])
  const header = splitCsvLine(lines[0], delim).map((h) => h.toLowerCase())
  const periodIdx = header.findIndex((h) =>
    /period|month|date|ay|tarih|dönem|donem|monat|datum|abrechnung/.test(h)
  )
  const kwhIdx = pickKwhColumn(header)
  const costIdx = header.findIndex((h) =>
    /cost|eur|price|tutar|fiyat|€|betrag|kosten|ücret|ucret/.test(h)
  )
  if (periodIdx < 0 || kwhIdx < 0) {
    return {
      rows: [],
      errors: [
        `Couldn't find a date/period column and a kWh column. Detected columns: ${header.join(", ") || "(none)"}.`,
      ],
    }
  }

  const rows: ConsumptionRow[] = []
  const errors: string[] = []
  for (let i = 1; i < lines.length; i++) {
    const cells = splitCsvLine(lines[i], delim)
    const period = normalizePeriod(cells[periodIdx] ?? "")
    const kwh = num(cells[kwhIdx] ?? "")
    if (!period || !Number.isFinite(kwh)) {
      errors.push(`Row ${i + 1}: skipped (couldn't read the date or kWh).`)
      continue
    }
    let cost: number | null = null
    if (costIdx >= 0) {
      const c = num(cells[costIdx] ?? "")
      if (Number.isFinite(c)) cost = c
    }
    rows.push({ period, energy_kwh: Math.round(kwh * 100) / 100, cost_eur: cost })
  }

  // Aggregate by month: a file split by energy type or meter (e.g. district
  // heat + electricity rows for the same month) sums into one monthly total —
  // the building's total monthly energy, which is what the baseline expects.
  const byPeriod = new Map<string, { energy: number; cost: number; hasCost: boolean }>()
  for (const r of rows) {
    const cur = byPeriod.get(r.period) ?? { energy: 0, cost: 0, hasCost: false }
    cur.energy += r.energy_kwh
    if (r.cost_eur != null) {
      cur.cost += r.cost_eur
      cur.hasCost = true
    }
    byPeriod.set(r.period, cur)
  }
  const merged: ConsumptionRow[] = [...byPeriod.entries()]
    .map(([period, v]) => ({
      period,
      energy_kwh: Math.round(v.energy * 100) / 100,
      cost_eur: v.hasCost ? Math.round(v.cost * 100) / 100 : null,
    }))
    .sort((a, b) => a.period.localeCompare(b.period))
  return { rows: merged, errors }
}

export async function uploadConsumption(
  buildingId: string,
  rows: ConsumptionRow[],
  source = "csv"
): Promise<Result<ConsumptionSummary>> {
  try {
    const res = await fetch(
      `/api/buildings/${encodeURIComponent(buildingId)}/consumption`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rows, source }),
      }
    )
    if (!res.ok) {
      const text = await res.text().catch(() => "")
      return { ok: false, error: `Upload failed (${res.status}): ${text.slice(0, 160)}` }
    }
    return { ok: true, data: (await res.json()) as ConsumptionSummary }
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) }
  }
}

/** A bill parsed server-side from a PDF — candidate rows + provenance + warnings. */
export type ParsedBill = {
  rows: ConsumptionRow[]
  source: string // "table" | "text" | "none"
  warnings: string[]
}

/**
 * Send a base64 PDF bill to the backend for best-effort extraction of monthly
 * rows. The result is shown for review; nothing is saved until the user uploads.
 */
export async function parseBillPdf(
  buildingId: string,
  pdfBase64: string
): Promise<Result<ParsedBill>> {
  try {
    const res = await fetch(
      `/api/buildings/${encodeURIComponent(buildingId)}/consumption/parse-pdf`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pdf_base64: pdfBase64 }),
      }
    )
    if (!res.ok) {
      const text = await res.text().catch(() => "")
      return { ok: false, error: `PDF parse failed (${res.status}): ${text.slice(0, 160)}` }
    }
    return { ok: true, data: (await res.json()) as ParsedBill }
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) }
  }
}
