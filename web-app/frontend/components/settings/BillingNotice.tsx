"use client"

/**
 * BillingNotice — confirmation banner after returning from Stripe Checkout.
 *
 * Stripe redirects to /settings?billing=success | cancel. This shows a calm,
 * dismissible acknowledgement (the actual tier change arrives via webhook and
 * is reflected by the SubscriptionCard below). Dismissing drops the ?billing
 * query param so a refresh doesn't re-show it.
 */
import { useState } from "react"
import { CheckCircle2, Info, X } from "lucide-react"

export function BillingNotice({ status }: { status?: string }) {
  const [dismissed, setDismissed] = useState(false)

  if (dismissed || (status !== "success" && status !== "cancel")) {
    return null
  }

  const success = status === "success"

  function dismiss() {
    setDismissed(true)
    if (typeof window !== "undefined") {
      const url = new URL(window.location.href)
      url.searchParams.delete("billing")
      window.history.replaceState({}, "", url.toString())
    }
  }

  return (
    <div
      className={
        success
          ? "mb-4 flex items-start gap-2 rounded-lg border border-brand-emerald/30 bg-brand-emerald/5 px-4 py-3"
          : "mb-4 flex items-start gap-2 rounded-lg border border-border-subtle bg-white/[0.03] px-4 py-3"
      }
    >
      {success ? (
        <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-brand-emerald" aria-hidden />
      ) : (
        <Info className="mt-0.5 h-4 w-4 shrink-0 text-text-muted" aria-hidden />
      )}
      <div className="flex-1 text-sm text-text-primary">
        {success ? (
          <>
            <span className="font-medium">Subscription updated.</span>{" "}
            <span className="text-text-muted">
              Your new plan is active — it may take a moment to reflect below.
            </span>
          </>
        ) : (
          <>
            <span className="font-medium">Checkout canceled.</span>{" "}
            <span className="text-text-muted">No changes were made to your plan.</span>
          </>
        )}
      </div>
      <button
        type="button"
        onClick={dismiss}
        aria-label="Dismiss"
        className="shrink-0 text-text-faint hover:text-text-primary transition-colors"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  )
}
