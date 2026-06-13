/**
 * wordDoc — render a report document component to a Word-openable .doc download.
 *
 * The report documents are pure, inline-styled, server-renderable components (the same
 * ones the print/PDF routes use). We render one to static HTML and return it with the
 * Word content-type, so the browser downloads a .doc that Microsoft Word opens and the
 * user can edit / Save As .docx. This reuses the exact report components — no separate
 * Word layout to maintain, and no extra dependency (the `docx` npm package is blocked in
 * this environment, so a native-.docx build would need a python-docx backend instead).
 *
 * Fidelity note: Word renders inline-styled tables and text well; CSS flexbox rows (the
 * StatCard strips) may stack rather than sit side-by-side. Content is faithful; if the
 * card layout matters we can convert those strips to tables.
 */
import { renderToStaticMarkup } from "react-dom/server"
import type { ReactElement } from "react"

function esc(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
}

export function wordResponse(
  filename: string,
  title: string,
  subtitle: string | null,
  body: ReactElement
): Response {
  const inner = renderToStaticMarkup(body)
  const html =
    `<html xmlns:o="urn:schemas-microsoft-com:office:office" ` +
    `xmlns:w="urn:schemas-microsoft-com:office:word" xmlns="http://www.w3.org/TR/REC-html40">` +
    `<head><meta charset="utf-8"><title>${esc(title)}</title>` +
    `<!--[if gte mso 9]><xml><w:WordDocument><w:View>Print</w:View>` +
    `<w:Zoom>100</w:Zoom></w:WordDocument></xml><![endif]-->` +
    `<style>@page{size:A4 landscape;margin:1.4cm}` +
    `body{font-family:Arial,Helvetica,sans-serif;color:#1e293b;font-size:11pt}` +
    `table{border-collapse:collapse;width:100%}` +
    `td,th{border:1px solid #e2e8f0;padding:4px 6px;vertical-align:top}` +
    `h1,h2,h3{color:#0F6E56}</style></head><body>` +
    `<h2 style="color:#0F6E56;margin:0 0 2px">${esc(title)}</h2>` +
    (subtitle ? `<p style="color:#64748b;margin:0 0 12px;font-size:10pt">${esc(subtitle)}</p>` : "") +
    `${inner}</body></html>`
  return new Response("﻿" + html, {
    headers: {
      "Content-Type": "application/msword; charset=utf-8",
      "Content-Disposition": `attachment; filename="${filename}.doc"`,
    },
  })
}
