"use client"

/**
 * AccountMenu — the right-side "my account" dropdown.
 *
 * Collapses the email + Settings + Glossary + Sign-out cluster into one avatar
 * button with a dropdown (the conventional SaaS pattern), freeing horizontal room
 * so the primary nav no longer needs a scrollbar. Closes on outside-click / pick.
 */
import { BookOpen, ChevronDown, LogOut, Settings } from "lucide-react"
import Link from "next/link"
import { signOut } from "next-auth/react"
import { useEffect, useRef, useState } from "react"

export function AccountMenu({ email }: { email?: string | null }) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const initial = (email?.trim()?.[0] ?? "?").toUpperCase()

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
        className="inline-flex items-center gap-2 rounded-md border border-border-subtle px-2 h-9 text-text-muted transition-colors hover:border-brand-emerald hover:text-text-primary"
      >
        <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-brand-emerald/15 text-xs font-semibold text-brand-emerald">
          {initial}
        </span>
        <span className="hidden max-w-[160px] truncate text-sm md:inline">{email ?? "Account"}</span>
        <ChevronDown size={14} aria-hidden />
      </button>

      {open && (
        <div
          role="menu"
          className="absolute right-0 mt-1 w-56 overflow-hidden rounded-md border border-border-subtle bg-bg-elevated py-1 shadow-[0_8px_24px_rgba(0,0,0,0.45)] z-50"
        >
          {email && (
            <div className="border-b border-border-subtle px-3 py-2">
              <div className="text-[10px] uppercase tracking-wider text-text-faint">Signed in as</div>
              <div className="truncate text-sm text-text-primary">{email}</div>
            </div>
          )}
          <Link
            href="/settings"
            role="menuitem"
            onClick={() => setOpen(false)}
            className="flex items-center gap-2.5 px-3 py-2 text-sm text-text-muted transition-colors hover:bg-white/5 hover:text-text-primary"
          >
            <Settings className="h-4 w-4" aria-hidden /> Account &amp; settings
          </Link>
          <Link
            href="/glossary"
            role="menuitem"
            onClick={() => setOpen(false)}
            className="flex items-center gap-2.5 px-3 py-2 text-sm text-text-muted transition-colors hover:bg-white/5 hover:text-text-primary"
          >
            <BookOpen className="h-4 w-4" aria-hidden /> Glossary
          </Link>
          <button
            type="button"
            role="menuitem"
            onClick={() => {
              setOpen(false)
              signOut({ callbackUrl: "/" })
            }}
            className="flex w-full items-center gap-2.5 border-t border-border-subtle px-3 py-2 text-sm text-text-muted transition-colors hover:bg-white/5 hover:text-accent-red"
          >
            <LogOut className="h-4 w-4" aria-hidden /> Sign out
          </button>
        </div>
      )}
    </div>
  )
}
