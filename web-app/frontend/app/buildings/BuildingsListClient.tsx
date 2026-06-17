"use client"

/**
 * BuildingsListClient -- the interactive layer of /buildings.
 *
 * The server component (page.tsx) fetches the building list and hands it
 * down here. This component owns:
 *   * Compare-mode toggle (single-tap-open vs multi-select)
 *   * Selection state (Set of fabric_building_ids), persisted to localStorage
 *     so it survives a refresh (pruned against the current building list)
 *   * Max-5 selection limit (UX clarity guard)
 *   * A sticky footer Compare bar that stays visible while the grid scrolls
 *
 * In default mode, BuildingCards are <Link>s. In compare mode, they're
 * <button>s with a selection checkmark.
 */
import { useEffect, useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import { ArrowRight, GitCompare, Plus, Upload, X } from "lucide-react"

import type { Building } from "@/lib/api/buildings"
import { AddBuildingModal } from "@/components/buildings/AddBuildingModal"
import { ConsumptionUploadModal } from "@/components/buildings/ConsumptionUploadModal"

import { BuildingCard } from "./BuildingCard"

const MAX_SELECTION = 5
const STORAGE_KEY = "el:buildings:compare"

type StoredCompare = { compareMode: boolean; ids: string[] }

type BuildingsListClientProps = {
  buildings: Building[]
}

export function BuildingsListClient({ buildings }: BuildingsListClientProps) {
  const router = useRouter()
  const [compareMode, setCompareMode] = useState(false)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  // Don't persist until the initial restore has run, so the empty default
  // state can't clobber a saved selection on first render.
  const [restored, setRestored] = useState(false)
  const [uploadOpen, setUploadOpen] = useState(false)
  const [addOpen, setAddOpen] = useState(false)

  const validIds = useMemo(
    () =>
      new Set(
        buildings
          .map((b) => b.fabric_building_id)
          .filter((id): id is string => Boolean(id))
      ),
    [buildings]
  )

  // Restore once on mount. localStorage is client-only, so it is read in an
  // effect (not in useState init) to keep SSR + first client render identical
  // and avoid a hydration mismatch. Stale ids are pruned against the current
  // building list.
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (raw) {
        const parsed = JSON.parse(raw) as StoredCompare
        const ids = (parsed.ids ?? [])
          .filter((id) => validIds.has(id))
          .slice(0, MAX_SELECTION)
        if (ids.length > 0) {
          setSelectedIds(new Set(ids))
          setCompareMode(parsed.compareMode ?? true)
        }
      }
    } catch {
      /* storage unavailable / blocked -- ignore */
    }
    setRestored(true)
    // Mount-only: validIds derives from server-provided buildings (stable).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Persist on change (after the initial restore).
  useEffect(() => {
    if (!restored) return
    try {
      const payload: StoredCompare = {
        compareMode,
        ids: Array.from(selectedIds),
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(payload))
    } catch {
      /* ignore */
    }
  }, [restored, compareMode, selectedIds])

  const selectedArray = useMemo(() => Array.from(selectedIds), [selectedIds])

  function toggleCompareMode() {
    const next = !compareMode
    setCompareMode(next)
    if (!next) setSelectedIds(new Set())
  }

  function toggleSelected(fabricId: string) {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(fabricId)) {
        next.delete(fabricId)
      } else if (next.size < MAX_SELECTION) {
        next.add(fabricId)
      }
      return next
    })
  }

  function clearSelection() {
    setSelectedIds(new Set())
  }

  function goToCompare() {
    if (selectedArray.length < 2) return
    const qs = selectedArray.join(",")
    router.push(`/buildings/compare?ids=${encodeURIComponent(qs)}`)
  }

  return (
    <>
      {/* Toolbar row -- compare-mode toggle + selection summary */}
      <div className="flex items-center justify-between mb-5">
        <div className="text-xs text-text-muted">
          {compareMode ? (
            <span>
              <span className="text-text-primary font-medium">
                {selectedIds.size}
              </span>{" "}
              of {MAX_SELECTION} selected
              {selectedIds.size > 0 && (
                <span className="ml-3 text-text-faint">
                  Tap a card to add or remove
                </span>
              )}
            </span>
          ) : (
            <span className="text-text-faint">
              Tap any building to open its report
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => setAddOpen(true)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-brand-emerald text-white text-sm font-medium transition-colors hover:bg-brand-deep"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Add building</span>
        </button>
        <button
          type="button"
          onClick={() => setUploadOpen(true)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-border-subtle text-sm text-text-muted transition-colors hover:border-brand-emerald/60 hover:text-brand-emerald"
        >
          <Upload className="w-3.5 h-3.5" />
          <span>Upload data</span>
        </button>
        <button
          type="button"
          onClick={toggleCompareMode}
          className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md
                      border text-sm transition-colors
                      ${
                        compareMode
                          ? "border-brand-emerald/60 text-brand-emerald bg-brand-emerald/10"
                          : "border-border-subtle text-text-muted hover:border-brand-emerald/60 hover:text-brand-emerald"
                      }`}
        >
          {compareMode ? (
            <>
              <X className="w-3.5 h-3.5" />
              <span>Exit Compare</span>
            </>
          ) : (
            <>
              <GitCompare className="w-3.5 h-3.5" />
              <span>Compare Buildings</span>
            </>
          )}
        </button>
        </div>
      </div>

      {/* The grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {buildings.map((b) => {
          const id = b.fabric_building_id ?? ""
          return (
            <BuildingCard
              key={b.id}
              building={b}
              selectable={compareMode}
              selected={selectedIds.has(id)}
              onToggle={() => id && toggleSelected(id)}
            />
          )
        })}
      </div>

      {/* Sticky compare bar -- keeps the Compare CTA in view while the grid
          scrolls (replaces the old top-toolbar button). */}
      {compareMode && selectedIds.size > 0 && (
        <div className="fixed inset-x-0 bottom-6 z-40 flex justify-center px-4 pointer-events-none">
          <div
            className="pointer-events-auto flex items-center gap-3 rounded-full
                       border border-border-subtle bg-bg-elevated/95 backdrop-blur-md
                       pl-4 pr-2 py-2 shadow-[0_8px_32px_rgba(0,0,0,0.45)]"
          >
            <span className="text-sm text-text-muted">
              <span className="text-text-primary font-medium">
                {selectedIds.size}
              </span>{" "}
              selected
            </span>
            <button
              type="button"
              onClick={clearSelection}
              className="text-xs text-text-faint hover:text-text-muted transition-colors px-2 py-1"
            >
              Clear
            </button>
            <button
              type="button"
              onClick={goToCompare}
              disabled={selectedIds.size < 2}
              className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full
                         bg-brand-emerald text-white text-sm font-medium
                         hover:bg-brand-emerald/90 transition-colors
                         disabled:opacity-40 disabled:cursor-not-allowed
                         shadow-[0_4px_16px_rgba(29,158,117,0.35)]"
            >
              <span>
                {selectedIds.size < 2
                  ? "Select 2+ to compare"
                  : `Compare (${selectedIds.size})`}
              </span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {uploadOpen && (
        <ConsumptionUploadModal buildings={buildings} onClose={() => setUploadOpen(false)} />
      )}

      {addOpen && <AddBuildingModal onClose={() => setAddOpen(false)} />}
    </>
  )
}
