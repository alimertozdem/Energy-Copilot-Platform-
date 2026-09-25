"use client"

import Link from "next/link"
import { ChevronDown, Download, FileEdit, FileText, Sparkles } from "lucide-react"
import { useEffect, useRef, useState, type ReactNode } from "react"
import { cn } from "@/lib/utils"

type Variant = { label: string; href: string; download?: boolean }
type Report = { label: string; href: string; badge?: string; featured?: boolean; variants?: Variant[] }

export function ComplianceReportMenu({ reportQuery }: { reportQuery: string }) {
  const q = reportQuery
  const reports: Report[] = [
    {
      label: "Executive Decarbonisation & Capex",
      href: `/compliance/report${q}`,
      badge: "3-Page PDF",
      featured: true,
    },
    {
      label: "CRREM Stranding & 1.5°C Trajectory",
      href: `/compliance/crrem-report${q}`,
    },
    {
      label: "Off-Hours & Quick-Wins Audit",
      href: `/compliance/report${q}#quick-wins`,
      badge: "Zero Capex",
    },
    {
      label: "ESRS E-1 Climate (CSRD)",
      href: `/compliance/esrs-report${q}`,
      variants: [{ label: "Word", href: `/compliance/esrs-report/docx${q}`, download: true }],
    },
    {
      label: "GHG Protocol Scope 1 & 2 Inventory",
      href: `/compliance/ghg-report${q}`,
    },
    {
      label: "EnEfG Energy Efficiency Plan",
      href: `/compliance/enefg-report${q}`,
    },
    {
      label: "VSME ESG Disclosure",
      href: `/compliance/vsme-report${q}`,
      variants: [
        { label: "Word", href: `/compliance/vsme-report/docx${q}`, download: true },
        { label: "Comprehensive", href: `/compliance/vsme-report?level=comprehensive` },
      ],
    },
  ]

  return (
    <div className="flex items-center gap-2.5">
      <Dropdown label="Edit" icon={<FileEdit size={14} aria-hidden />}>
        <MenuLink href="/compliance/esrs-editor">Edit ESRS narrative</MenuLink>
        <MenuLink href="/compliance/vsme-editor">Edit VSME narrative</MenuLink>
      </Dropdown>

      <Dropdown label="All Reports" icon={<FileText size={14} aria-hidden />} width="w-72">
        {reports.map((r) => (
          <div key={r.label} className="px-1.5 py-0.5">
            <Link
              href={r.href}
              target="_blank"
              rel="noopener noreferrer"
              className={cn(
                "group flex items-center justify-between gap-2 rounded-lg px-2.5 py-2 text-xs font-medium transition-all duration-150",
                r.featured
                  ? "bg-brand-emerald/10 text-brand-emerald hover:bg-brand-emerald/20 border border-brand-emerald/30 shadow-[0_0_12px_rgba(16,185,129,0.1)]"
                  : "text-text-muted hover:bg-white/[0.04] hover:text-text-primary"
              )}
            >
              <div className="flex items-center gap-2 truncate">
                {r.featured && <Sparkles size={13} className="text-brand-emerald shrink-0" />}
                <span className="truncate">{r.label}</span>
              </div>
              <div className="flex items-center gap-1.5 shrink-0">
                {r.badge && (
                  <span className="rounded bg-brand-emerald/15 px-1.5 py-0.5 text-[9px] font-semibold text-brand-emerald uppercase tracking-wider">
                    {r.badge}
                  </span>
                )}
                <Download size={13} aria-hidden className="opacity-40 group-hover:opacity-100 transition-opacity" />
              </div>
            </Link>
            {r.variants && (
              <div className="mb-1 mt-1 flex flex-wrap gap-1.5 pl-3">
                {r.variants.map((v) => (
                  <a
                    key={v.label}
                    href={v.href}
                    target={v.download ? undefined : "_blank"}
                    rel="noopener noreferrer"
                    className="rounded border border-border-subtle bg-bg-surface/50 px-2 py-0.5 text-[10px] font-medium text-text-muted transition-colors hover:border-brand-emerald/50 hover:text-brand-emerald"
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
        href={`/compliance/report${q}`}
        target="_blank"
        rel="noopener noreferrer"
        title="Print or save the 3-Page Executive Decarbonisation & Capex Report"
        className="inline-flex items-center gap-2 rounded-lg border border-brand-emerald/50 bg-gradient-to-r from-brand-emerald/20 to-teal-500/20 px-3.5 py-1.5 text-xs font-semibold text-brand-emerald shadow-[0_0_15px_rgba(16,185,129,0.15)] transition-all hover:bg-brand-emerald/25 hover:border-brand-emerald hover:shadow-[0_0_20px_rgba(16,185,129,0.25)] active:scale-[0.98]"
      >
        <Download size={14} aria-hidden />
        <span>Executive Report (PDF)</span>
      </Link>
    </div>
  )
}

function Dropdown({
  label,
  icon,
  width = "w-56",
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
        className="inline-flex items-center gap-2 rounded-lg border border-border-subtle bg-bg-surface/40 px-3 py-1.5 text-xs font-medium text-text-muted shadow-sm backdrop-blur-sm transition-all hover:border-brand-emerald/40 hover:text-text-primary hover:bg-white/[0.03]"
      >
        {icon}
        <span>{label}</span>
        <ChevronDown size={13} aria-hidden className={cn("transition-transform duration-200", open && "rotate-180")} />
      </button>
      {open && (
        <div
          role="menu"
          onClick={() => setOpen(false)}
          className={cn(
            "absolute right-0 z-50 mt-1.5 rounded-xl border border-border-subtle/80 bg-[#0d151d]/95 p-1.5 shadow-[0_12px_36px_rgba(0,0,0,0.55)] backdrop-blur-md animate-in fade-in-50 zoom-in-95 duration-100",
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
      className="block rounded-lg px-3 py-2 text-xs font-medium text-text-muted transition-colors hover:bg-white/[0.04] hover:text-brand-emerald"
    >
      {children}
    </Link>
  )
}
