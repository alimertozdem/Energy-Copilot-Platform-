/**
 * /residence/enter?token=… — magic-link landing.
 *
 * PUBLIC server component (no NextAuth). Reads the token from the URL and hands
 * it to a tiny client component that exchanges it for the resident session
 * cookie (via /api/residence/session) and redirects to /residence.
 */
import { ResidenceEnterClient } from "./ResidenceEnterClient"

export const dynamic = "force-dynamic"

export default async function ResidenceEnterPage({
  searchParams,
}: {
  searchParams: Promise<{ token?: string }>
}) {
  const { token } = await searchParams
  return <ResidenceEnterClient token={token?.trim() || null} />
}
