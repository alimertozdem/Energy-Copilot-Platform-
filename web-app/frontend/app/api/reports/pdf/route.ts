/**
 * GET /api/reports/pdf?path=/buildings/<id>/report&filename=Name
 *
 * Server-side, true one-click PDF download for the print/HTML reports.
 *
 * Renders the *existing* gated report page with a headless Chromium and returns
 * page.pdf(). Because the report pages are server-rendered and already ship an
 * A4-landscape print stylesheet (@page in reportKit), the output is vector,
 * text-selectable and pixel-identical to the on-screen report — no rasterising,
 * no broken page breaks. The caller's session cookie is forwarded so the gated
 * page renders with their own data; the target is locked to the app's own
 * origin and to report routes only (no open proxy).
 *
 * Chromium: @sparticuz/chromium + puppeteer-core on Vercel; system Chrome
 * (CHROME_PATH) for local dev. Both are dynamic imports + serverExternalPackages
 * so they never enter the client/edge bundle.
 */
import { NextRequest, NextResponse } from "next/server"

export const runtime = "nodejs"
export const dynamic = "force-dynamic"
export const maxDuration = 60

/** Only allow internal report routes (every one ends in ".../report" or "...-report"). */
function isAllowedReportPath(path: string): boolean {
  if (!path.startsWith("/") || path.startsWith("//")) return false
  if (path.includes("..") || path.includes("://")) return false
  const pathname = path.split("?")[0].replace(/\/+$/, "")
  return /(^|\/)([a-z0-9]+-)?report$/i.test(pathname)
}

function sanitizeFilename(raw: string): string {
  const base = (raw || "EnergyLens-Report").replace(/[^a-zA-Z0-9 _.-]/g, "").trim() || "EnergyLens-Report"
  return base.toLowerCase().endsWith(".pdf") ? base : `${base}.pdf`
}

async function launchBrowser() {
  // Serverless Linux (Vercel / Lambda) → bundled headless Chromium.
  if (process.env.VERCEL || process.env.AWS_LAMBDA_FUNCTION_NAME) {
    const chromiumMod: any = await import("@sparticuz/chromium")
    const chromium = chromiumMod.default ?? chromiumMod
    const puppeteer: any = await import("puppeteer-core")
    return puppeteer.launch({
      args: chromium.args,
      defaultViewport: { width: 1280, height: 1696 },
      executablePath: await chromium.executablePath(),
      headless: true,
    })
  }
  // Local dev → system Chrome. Override with CHROME_PATH if not the default.
  const puppeteer: any = await import("puppeteer-core")
  const executablePath =
    process.env.CHROME_PATH || "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
  return puppeteer.launch({
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
    executablePath,
    headless: true,
  })
}

export async function GET(request: NextRequest) {
  const path = request.nextUrl.searchParams.get("path") || ""
  const filename = sanitizeFilename(request.nextUrl.searchParams.get("filename") || "")

  if (!isAllowedReportPath(path)) {
    return NextResponse.json({ error: "invalid_path" }, { status: 400 })
  }

  // Forward the caller's auth so the gated report renders with their data.
  const cookie = request.headers.get("cookie") || ""
  if (!cookie) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 })
  }

  // Same-origin only — cookies stay valid, never a cross-origin proxy.
  const targetUrl = request.nextUrl.origin + path

  let browser: any
  try {
    browser = await launchBrowser()
    const page = await browser.newPage()
    await page.setExtraHTTPHeaders({ cookie })
    await page.goto(targetUrl, { waitUntil: "networkidle0", timeout: 45000 })
    // Report pages are SSR; give any late client paint a beat to settle.
    await new Promise((r) => setTimeout(r, 400))
    const pdf: Uint8Array = await page.pdf({
      printBackground: true,
      preferCSSPageSize: true, // honour @page { size: A4 landscape; margin: 10mm }
      landscape: true,
      format: "A4",
    })
    await browser.close()
    browser = undefined

    return new NextResponse(Buffer.from(pdf), {
      status: 200,
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": `attachment; filename="${filename}"`,
        "Cache-Control": "no-store",
      },
    })
  } catch (err) {
    if (browser) {
      try {
        await browser.close()
      } catch {
        /* ignore */
      }
    }
    console.error("[reports/pdf] render failed:", err)
    return NextResponse.json({ error: "render_failed" }, { status: 500 })
  }
}
