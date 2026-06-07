/**
 * Billing client helpers (browser-side).
 *
 * Go through our Next.js proxy routes (/api/billing/*), which attach the
 * NextAuth session JWT as Bearer to FastAPI. Each call returns a Stripe-hosted
 * URL; the caller redirects the browser there (window.location.href = url).
 */

export type BillingTier = "basic" | "monitor"

export type BillingResult = { ok: true; url: string } | { ok: false; error: string }

async function postForUrl(path: string, body?: unknown): Promise<BillingResult> {
  try {
    const res = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    })
    const data = (await res.json().catch(() => ({}))) as { url?: string; detail?: string }
    if (!res.ok) {
      return { ok: false, error: data?.detail || `Request failed (${res.status})` }
    }
    if (!data?.url) {
      return { ok: false, error: "No checkout URL returned" }
    }
    return { ok: true, url: data.url }
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) }
  }
}

/** Begin a Stripe Checkout session for a self-serve tier. */
export function startCheckout(tier: BillingTier): Promise<BillingResult> {
  return postForUrl("/api/billing/checkout", { tier })
}

/** Open the Stripe Customer Portal (manage / cancel the subscription). */
export function openPortal(): Promise<BillingResult> {
  return postForUrl("/api/billing/portal")
}
