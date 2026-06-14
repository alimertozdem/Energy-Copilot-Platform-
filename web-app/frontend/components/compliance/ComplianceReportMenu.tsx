"use client"

/**
 * ComplianceReportMenu — declutters the compliance hub's export row (design audit P1-5/P2, 2026-06-15).
 *
 * Was: ~12 equal-weight buttons crammed in one line (incl. two ambiguous "Word" links).
 * Now: [Edit ▾] [Reports ▾] [Export PDF] — three controls; each report's PDF + Word +
 * Comprehensive variants nest under the report. Same routes, same new-tab/download
 * behaviour — pure presentation grouping.
 */

import Link from "next/link"
import { ChevronDown, Download, FileEdit, FileText } from "lucide-react"
import { useEffect, useRef, useState, type ReactNode } from "react"

import { cn } from "@/lib/utils"

type Variant = { label: string; href: string; download?: boolean }
type Report = { label: string; href: string; variants?: Variant[] }

export function ComplianceReportMenu({ reportQuery }: { reportQuery: string }) {
  const q = reportQuery
  const reports: Report[] = [
    {
      label: "ESRS E-1 (Climate)",
      href: `/compliance/esrs-report${q}`,
      variants: [{ label: "Word", href: `/compliance/esrs-report/docx${q}`, download: true }],
    },
    { label: "EnEfG plan", href: `/compliance/enefg-report${q}` },
    { label: "GHG Inventory", href: `/compliance/ghg-report${q}` },
    {
      label: "VSME report",
      href: `/compliance/vsme-report${q}`,
      variants: [
        { label: "Word", href: `/compliance/vsme-report/docx${q}`, download: true },
        { label: "Comprehensive", href: `/compliance/vsme-report?level=comprehensive` },
      ],
    },
    { label: "CRREM stranding", href: `/compliance/crrem-report${q}` },
    { label: "GRESB readiness", href: `/compliance/gresb-report${q}` },
  ]

  return (
    <div className="flex items-center gap-2">
      <Dropdown label="Edit" icon={<FileEdit size={14} aria-hidden />}>
        <MenuLink href="/compliance/esrs-editor">Edit ESRS narrative</MenuLink>
        <MenuLink href="/compliance/vsme-editor">Edit VSME narrative</MenuLink>
      </Dropdown>

      <Dropdown label="Reports" icon={<FileText size={14} aria-hidden />} width="w-64">
        {reports.map((r) => (
          <div key={r.label} className="px-1 py-0.5">
            <Link
              href={r.href}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between gap-2 rounded-md px-2 py-1.5 text-sm text-text-muted transition-colors hover:bg-white/5 hover:text-brand-emerald"
            >
              <span>{r.label}</span>
              <Download size={13} aria-hidden className="opacity-60" />
            </Link>
            {r.variants && (
              <div className="mb-1 mt-0.5 flex flex-wrap gap-1 pl-2">
                {r.variants.map((v) => (
                  <a
                    key={v.label}
                    href={v.href}
                    target={v.download ? undefined : "_blank"}
                    rel="noopener noreferrer"
                    className="rounded border border-border-faint px-1.5 py-0.5 text-[10px] font-medium text-text-faint transition-colors hover:border-brand-emerald/40 hover:text-brand-emerald"
                  >
                    {v.label}
                  </a>
                ))}
              </div>
            )}
          </div>
        ))}
      </Dropdown>

      <Link
        href="/compliance/report"
        target="_blank"
        rel="noopener noreferrer"
        title="Print-ready PDF: MEPS, CRREM, EU Taxonomy and ESRS-E1"
        className="inline-flex items-center gap-1.5 rounded-md border border-brand-emerald/40 bg-brand-emerald/10 px-3 py-1.5 text-sm font-semibold text-brand-emerald transition-colors hover:bg-brand-emerald/15"
      >
        <Download size={14} aria-hidden />
        Export PDF
      </Link>
    </div>
  )
}

function Dropdown({
  label,
  icon,
  width = "w-52",
  children,
}: {
  label: string
  icon: ReactNode
  width?: string
  children: ReactNode
}) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    function onDoc(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener("mousedown", onDoc)
    return () => document.removeEventListener("mousedown", onDoc)
  }, [open])

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="menu"
        aria-expanded={open}
        className="inline-flex items-center gap-1.5 rounded-md border border-border-subtle px-3 py-1.5 text-sm font-medium text-text-muted transition-colors hover:border-brand-emerald hover:text-brand-emerald"
      >
        {icon}
        {label}
        <ChevronDown size={13} aria-hidden className={cn("transition-transform", open && "rotate-180")} />
      </button>
      {open && (
        <div
          role="menu"
          onClick={() => setOpen(false)}
          className={cn(
            "absolute right-0 z-50 mt-1 rounded-md border border-border-subtle bg-bg-elevated py-1 shadow-[0_8px_24px_rgba(0,0,0,0.4)]",
            width
          )}
        >
          {children}
        </div>
      )}
    </div>
  )
}

function MenuLink({ href, children }: { href: string; children: ReactNode }) {
  return (
    <Link
      href={href}
      role="menuitem"
      className="block px-3 py-2 text-sm text-text-muted transition-colors hover:bg-white/5 hover:text-brand-emerald"
    >
      {children}
    </Link>
  )
}
