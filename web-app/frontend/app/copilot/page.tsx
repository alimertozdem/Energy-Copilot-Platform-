/**
 * /copilot — AI chat over the user's portfolio.
 *
 * Server Component: pulls the initial conversation list, then hands off to
 * CopilotShell (client) for all interactive state — message streaming,
 * tool-call rendering, conversation switching.
 *
 * Auth:
 *   Same NextAuth JWT pattern as /portfolio and /buildings. No session →
 *   redirect to "/". The accessToken is forwarded by the proxy routes at
 *   /api/copilot/* and never reaches the browser.
 *
 * Data path:
 *   browser → /api/copilot/* (Next.js proxy with session token)
 *           → backend FastAPI /copilot/* (orchestrator + LLMProvider)
 *           → Anthropic API + Fabric SQL + Postgres
 */
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { AppChrome } from "@/components/AppChrome"
import { CopilotShell } from "@/components/copilot/CopilotShell"
import { CopilotMotif } from "@/components/motifs/CopilotMotif"
import { authOptions } from "@/lib/auth/options"
import { fetchConversations } from "@/lib/api/copilot"

// Accent reserved for the Copilot section — violet, distinct from
// emerald (portfolio) and the cartographic atlas accents on /buildings/*.
const COPILOT_ACCENT = "#7B5BD6"

type PageProps = {
  searchParams: Promise<{ building_id?: string }>
}

export default async function CopilotPage({ searchParams }: PageProps) {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }

  const { building_id } = await searchParams
  const focusBuildingId =
    typeof building_id === "string" && building_id.length > 0 ? building_id : null

  const result = await fetchConversations(session.accessToken)
  const initialConversations = result.ok ? result.data.conversations : []
  const loadError = result.ok ? null : result.error

  return (
    <AppChrome
      breadcrumb={[{ label: "Copilot" }]}
      pageTitle="Copilot"
      subtitle="AI assistant for your portfolio"
      accentColor={COPILOT_ACCENT}
    >
      <CopilotMotif />
      <div className="px-6 py-6">
        {loadError && (
          <div className="max-w-6xl mx-auto mb-4 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-200">
            Could not load conversations: {loadError}
          </div>
        )}
        <CopilotShell
          initialConversations={initialConversations}
          accent={COPILOT_ACCENT}
          focusBuildingId={focusBuildingId}
        />
      </div>
    </AppChrome>
  )
}
