/**
 * /dashboard -- legacy route, redirects to the new /buildings entry point.
 *
 * The original V1 dashboard rendered a single full-screen Power BI embed.
 * Day 13-14 replaced that with /buildings (grid list) + /buildings/[id]
 * (per-building embed with AppChrome). Keeping this redirect avoids breaking
 * any bookmarks, README links, or old screenshots that point at /dashboard.
 *
 * Server-side redirect happens before render -> no flicker.
 */
import { redirect } from "next/navigation"

export default function DashboardRedirect() {
  redirect("/buildings")
}
