"use client"

/**
 * AgentPanel — the "Edge agent" section of /connections.
 *
 * Issue / list / revoke building-scoped agent tokens, and show the one-line
 * command to run the edge gateway. The plaintext token is shown ONCE on issue
 * (the backend only stores a hash) — the user copies it into the agent's env.
 * The gateway then pulls THIS building's device map from /agent/config and
 * pushes live readings to Event Hub.
 */
import { useCallback, useEffect, useState } from "react"
import { Check, Copy, KeyRound, Plus, Trash2 } from "lucide-react"

import {
  type AgentToken,
  type IssuedToken,
  fetchAgentTokens,
  issueAgentToken,
  revokeAgentToken,
} from "@/lib/api/agentTokens"

function CopyButton({ text, label = "Copy" }: { text: string; label?: string }) {
  const [done, setDone] = useState(false)
  return (
    <button
      type="button"
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(text)
          setDone(true)
          setTimeout(() => setDone(false), 1500)
        } catch {
          /* clipboard blocked — ignore */
        }
      }}
      className="inline-flex items-center gap-1 rounded border border-border-subtle px-2 py-1 text-[11px] text-text-muted transition-colors hover:border-brand-emerald/60 hover:text-brand-emerald"
    >
      {done ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
      {done ? "Copied" : label}
    </button>
  )
}

export function AgentPanel({ buildingId }: { buildingId: string }) {
  const [tokens, setTokens] = useState<AgentToken[]>([])
  const [issued, setIssued] = useState<IssuedToken | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const reload = useCallback(async () => {
    if (!buildingId) return
    const r = await fetchAgentTokens(buildingId)
    if (r.ok) setTokens(r.data.tokens)
  }, [buildingId])

  useEffect(() => {
    setIssued(null)
    void reload()
  }, [reload])

  async function issue() {
    setBusy(true)
    setError(null)
    const r = await issueAgentToken(buildingId)
    setBusy(false)
    if (r.ok) {
      setIssued(r.data)
      void reload()
    } else {
      setError(r.error)
    }
  }

  async function revoke(id: string) {
    if (!confirm("Revoke this token? The agent using it loses access immediately.")) return
    const r = await revokeAgentToken(buildingId, id)
    if (r.ok) void reload()
  }

  const active = tokens.filter((t) => t.is_active)
  const tokenForSnippet = issued?.token ?? "$AGENT_TOKEN"
  const snippet =
    `docker run --rm -e AGENT_TOKEN="${tokenForSnippet}" \\\n` +
    `  --entrypoint python energylens-gateway run_agent.py \\\n` +
    `  --platform https://<your-energylens-api> \\\n` +
    `  --sink http --seconds 0`

  return (
    <div className="rounded-xl border border-border-subtle bg-bg-elevated/30 p-4">
      <div className="mb-3 flex items-center gap-2.5">
        <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-brand-emerald/15 ring-1 ring-brand-emerald/30">
          <KeyRound className="h-4 w-4 text-brand-emerald" aria-hidden />
        </span>
        <div>
          <h2 className="font-display text-sm font-semibold text-text-primary">Edge agent</h2>
          <p className="text-[11px] text-text-muted">
            Run an on-site gateway that pulls this building&rsquo;s device map and streams live data.
          </p>
        </div>
      </div>

      {issued && (
        <div className="mb-3 rounded-lg border border-amber-400/30 bg-amber-400/5 p-3">
          <div className="mb-1 text-xs font-medium text-amber-200">
            Copy this token now — it won&rsquo;t be shown again.
          </div>
          <div className="flex items-center gap-2">
            <code className="min-w-0 flex-1 truncate rounded bg-black/30 px-2 py-1 text-[11px] text-text-primary">
              {issued.token}
            </code>
            <CopyButton text={issued.token} />
          </div>
        </div>
      )}

      {active.length > 0 ? (
        <div className="mb-3 space-y-1.5">
          {active.map((t) => (
            <div
              key={t.id}
              className="flex items-center gap-2 rounded-md border border-border-subtle/60 bg-white/[0.02] px-2.5 py-1.5 text-xs"
            >
              <code className="rounded bg-white/5 px-1.5 py-0.5 text-[11px] text-text-primary">
                {t.token_prefix}…
              </code>
              <span className="truncate text-text-muted">{t.name}</span>
              <span className="ml-auto text-[10px] text-text-faint">
                {t.last_used_at ? `last used ${new Date(t.last_used_at).toLocaleDateString()}` : "never used"}
              </span>
              <button
                type="button"
                onClick={() => void revoke(t.id)}
                aria-label="Revoke token"
                className="rounded p-1 text-text-faint transition-colors hover:text-red-300"
              >
                <Trash2 className="h-3 w-3" />
              </button>
            </div>
          ))}
        </div>
      ) : (
        <p className="mb-3 text-xs text-text-faint">No active agent tokens for this building yet.</p>
      )}

      {error && <div className="mb-3 text-xs text-red-300">{error}</div>}

      <button
        type="button"
        onClick={() => void issue()}
        disabled={busy}
        className="inline-flex items-center gap-1.5 rounded-md border border-brand-emerald/40 px-3 py-1.5 text-sm text-brand-emerald transition-colors hover:bg-brand-emerald/10 disabled:opacity-50"
      >
        <Plus className="h-3.5 w-3.5" />
        {busy ? "Issuing…" : "Issue agent token"}
      </button>

      <div className="mt-4">
        <div className="mb-1 flex items-center justify-between">
          <span className="text-[11px] uppercase tracking-wide text-text-faint">Run the gateway</span>
          <CopyButton text={snippet} label="Copy command" />
        </div>
        <pre className="overflow-x-auto rounded-lg border border-border-subtle bg-black/30 p-3 text-[11px] leading-relaxed text-text-muted">
          <code>{snippet}</code>
        </pre>
        <p className="mt-1.5 text-[10px] leading-relaxed text-text-faint">
          Set <code className="text-text-muted">AGENT_TOKEN</code> to the issued token. The gateway reads
          this building&rsquo;s devices from <code className="text-text-muted">/agent/config</code> and posts
          normalized readings to <code className="text-text-muted">/ingest/telemetry</code> over HTTPS — no
          inbound ports, works from behind the building firewall. Build the image from the repo:{" "}
          <code className="text-text-muted">docker build -f edge-gateway/Dockerfile -t energylens-gateway .</code>{" "}
          High-volume streaming instead? Swap to <code className="text-text-muted">--sink eventhub</code> (Event Hub).
        </p>
      </div>
    </div>
  )
}
