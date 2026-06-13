"use client"

/**
 * NarrativeEditor — reusable form to write a standard's qualitative disclosures.
 *
 * One card per narrative datapoint ({ code, title, asks, boilerplate }). Each textarea
 * is pre-filled with the org's saved text, falling back to the guided boilerplate. Save
 * goes through the shared /api/esrs-narrative proxy (token added server-side); the same
 * org-scoped narrative table backs every standard, keyed by datapoint_key (E1-*, B*, …).
 * Used by the ESRS E-1 editor and the VSME editor.
 */
import Link from "next/link"
import { useState } from "react"

import { saveEsrsNarrative } from "@/lib/api/esrsNarrative"

type Disclosure = { code: string; title: string; asks: string; boilerplate: string }
type Status = "idle" | "saving" | "saved" | "error"

export function NarrativeEditor({
  disclosures,
  saved,
  loadError,
  heading,
  intro,
  asksLabel,
  reportHref,
  reportLabel,
}: {
  disclosures: Disclosure[]
  saved: Record<string, string>
  loadError: string | null
  heading: string
  intro: string
  asksLabel: string
  reportHref: string
  reportLabel: string
}) {
  const [content, setContent] = useState<Record<string, string>>(() => {
    const init: Record<string, string> = {}
    for (const d of disclosures) init[d.code] = saved[d.code] ?? d.boilerplate
    return init
  })
  const [status, setStatus] = useState<Record<string, Status>>({})
  const [errors, setErrors] = useState<Record<string, string>>({})

  async function save(code: string) {
    setStatus((s) => ({ ...s, [code]: "saving" }))
    const res = await saveEsrsNarrative(code, content[code] ?? "")
    if (res.ok) {
      setStatus((s) => ({ ...s, [code]: "saved" }))
    } else {
      setStatus((s) => ({ ...s, [code]: "error" }))
      setErrors((e) => ({ ...e, [code]: res.error }))
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-5 py-8">
      <div className="mb-2 flex items-center justify-between gap-3">
        <Link href="/compliance" className="text-sm text-text-muted hover:text-text-primary">
          ← Compliance
        </Link>
        <Link
          href={reportHref}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm font-medium text-brand-emerald hover:underline"
        >
          {reportLabel}
        </Link>
      </div>

      <h1 className="text-xl font-semibold text-text-primary">{heading}</h1>
      <p className="mt-1 text-sm text-text-muted">{intro}</p>

      {loadError && (
        <div className="mt-4 rounded-md border border-amber-400/40 bg-amber-400/10 px-3 py-2 text-sm text-amber-300">
          Couldn&apos;t load saved narrative ({loadError}) — starting from the drafts below.
        </div>
      )}

      <div className="mt-6 space-y-6">
        {disclosures.map((d) => {
          const st = status[d.code] ?? "idle"
          const isBoilerplate = (content[d.code] ?? "") === d.boilerplate
          return (
            <section
              key={d.code}
              className="rounded-lg border border-border-subtle bg-bg-elevated/40 p-4"
            >
              <div className="flex items-baseline gap-2">
                <span className="text-sm font-bold text-text-primary">{d.code}</span>
                <span className="text-sm font-semibold text-text-primary">{d.title}</span>
                {!isBoilerplate && saved[d.code] && (
                  <span className="rounded-full border border-brand-emerald/50 px-2 py-0.5 text-[10px] font-semibold text-brand-emerald">
                    saved
                  </span>
                )}
              </div>
              <p className="mt-1 text-xs text-text-faint">
                {asksLabel}: {d.asks}
              </p>
              <textarea
                value={content[d.code] ?? ""}
                onChange={(e) => {
                  const v = e.target.value
                  setContent((c) => ({ ...c, [d.code]: v }))
                  setStatus((s) => ({ ...s, [d.code]: "idle" }))
                }}
                rows={5}
                className="mt-2 w-full resize-y rounded-md border border-border-subtle bg-bg-base px-3 py-2 text-sm text-text-primary outline-none focus-visible:border-brand-emerald"
              />
              <div className="mt-2 flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => save(d.code)}
                  disabled={st === "saving"}
                  className="rounded-md border border-brand-emerald/40 bg-brand-emerald/10 px-3 py-1.5 text-sm font-medium text-brand-emerald transition-colors hover:border-brand-emerald hover:bg-brand-emerald/20 disabled:opacity-50"
                >
                  {st === "saving" ? "Saving…" : "Save"}
                </button>
                {st === "saved" && <span className="text-xs text-brand-emerald">Saved ✓</span>}
                {st === "error" && (
                  <span className="text-xs text-red-400">{errors[d.code] ?? "Failed"}</span>
                )}
                <button
                  type="button"
                  onClick={() => {
                    setContent((c) => ({ ...c, [d.code]: d.boilerplate }))
                    setStatus((s) => ({ ...s, [d.code]: "idle" }))
                  }}
                  className="text-xs text-text-faint hover:text-text-muted"
                >
                  Reset to draft
                </button>
              </div>
            </section>
          )
        })}
      </div>

      <p className="mt-6 text-xs text-text-faint">
        Reporting support — the narrative is your disclosure to complete and approve; it is
        not auto-generated or audited. Quantitative figures come from your metered data.
      </p>
    </div>
  )
}
