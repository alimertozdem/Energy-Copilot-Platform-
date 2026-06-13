/**
 * Next.js instrumentation — runs once at server boot, before any request.
 *
 * Why: Node 18+ resolves DNS in "verbatim" order, which often returns IPv6
 * (AAAA) first. When the machine's IPv6 path to Google is broken (common after
 * sleep/wake, a network switch, or VPN toggling), the Next.js server hangs for
 * ~tens of seconds trying to reach Google's OAuth token/JWKS endpoints during
 * the NextAuth callback, then fails with `error=OAuthCallback`. The browser and
 * curl don't hit this because they fall back to IPv4 cleanly; Node doesn't by
 * default.
 *
 * Fix: force IPv4-first DNS resolution for the whole server process. This is the
 * in-code equivalent of launching Node with `--dns-result-order=ipv4first`, but
 * it always applies regardless of how the dev/prod server is started (no reliance
 * on a NODE_OPTIONS env var being set in the right shell).
 *
 * Scope: affects all outbound lookups (Google OAuth, JWKS, and the local backend
 * — which already uses 127.0.0.1, so unaffected). IPv4-first still allows IPv6
 * when IPv4 is unavailable, so it's safe on IPv6-only networks too.
 */
export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    const { setDefaultResultOrder } = await import("node:dns")
    setDefaultResultOrder("ipv4first")
  }
}
