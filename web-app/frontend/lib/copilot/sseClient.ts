/**
 * Browser-side SSE consumer for /api/copilot/conversations/{id}/messages.
 *
 * EventSource doesn't support POST + JSON body, so we use fetch + ReadableStream
 * and parse the wire format ourselves. The wire format is the standard SSE
 * "event: name\ndata: json\n\n" framing emitted by the backend orchestrator.
 *
 * Usage:
 *   const cancel = streamCopilotMessage({
 *     conversationId,
 *     content: "B001 nasıl gidiyor?",
 *     onEvent: (ev) => updateUi(ev),
 *     onError: (err) => showToast(err),
 *     onClose: () => setSending(false),
 *   })
 *
 *   // Later, to cancel mid-stream (component unmount, user clicks Stop):
 *   cancel()
 */
import type { SSEEvent } from "@/lib/api/copilot"

type StreamCopilotMessageArgs = {
  conversationId: string
  content: string
  onEvent: (event: SSEEvent) => void
  onError?: (err: Error) => void
  onClose?: () => void
}

/**
 * Open a streaming POST to the proxy route. Returns a cancel() function
 * that aborts the underlying fetch + closes the stream.
 */
export function streamCopilotMessage(args: StreamCopilotMessageArgs): () => void {
  const { conversationId, content, onEvent, onError, onClose } = args
  const controller = new AbortController()

  void (async () => {
    let response: Response
    try {
      response = await fetch(
        `/api/copilot/conversations/${encodeURIComponent(conversationId)}/messages`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "text/event-stream",
          },
          body: JSON.stringify({ content }),
          signal: controller.signal,
        }
      )
    } catch (err) {
      if ((err as Error).name === "AbortError") {
        onClose?.()
        return
      }
      onError?.(err as Error)
      onClose?.()
      return
    }

    if (!response.ok || !response.body) {
      let detail = `HTTP ${response.status}`
      try {
        const body = await response.json()
        if (body?.detail) detail = String(body.detail)
      } catch {
        // ignore
      }
      onError?.(new Error(detail))
      onClose?.()
      return
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder("utf-8")
    let buffer = ""

    try {
      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        // SSE events are separated by a blank line ("\n\n").
        let sep = buffer.indexOf("\n\n")
        while (sep !== -1) {
          const raw = buffer.slice(0, sep)
          buffer = buffer.slice(sep + 2)
          const parsed = parseSSEChunk(raw)
          if (parsed) onEvent(parsed)
          sep = buffer.indexOf("\n\n")
        }
      }

      // Flush any final partial chunk (rare — server should always end with \n\n).
      if (buffer.trim()) {
        const parsed = parseSSEChunk(buffer)
        if (parsed) onEvent(parsed)
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        onError?.(err as Error)
      }
    } finally {
      onClose?.()
    }
  })()

  return () => controller.abort()
}

/**
 * Parse one SSE chunk (already separated from the next by the caller).
 * Expected shape:
 *     event: <name>
 *     data: <json>
 *
 * Lines beginning with ':' are SSE comments — ignored.
 */
function parseSSEChunk(raw: string): SSEEvent | null {
  let eventName: string | null = null
  let dataLine: string | null = null

  for (const line of raw.split("\n")) {
    if (!line || line.startsWith(":")) continue
    if (line.startsWith("event: ")) {
      eventName = line.slice("event: ".length).trim()
    } else if (line.startsWith("data: ")) {
      // SSE allows multiple data: lines per event; concatenate.
      const piece = line.slice("data: ".length)
      dataLine = dataLine === null ? piece : `${dataLine}\n${piece}`
    }
  }

  if (!eventName || dataLine === null) {
    return null
  }

  let parsedData: unknown
  try {
    parsedData = JSON.parse(dataLine)
  } catch {
    parsedData = { _raw: dataLine }
  }

  // The union narrows naturally — backend guarantees one of the known
  // event names. Unknown names still pass through with an `unknown` payload.
  return { type: eventName as SSEEvent["type"], data: parsedData as never }
}
