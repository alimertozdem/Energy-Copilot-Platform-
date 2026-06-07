import { test, expect } from "@playwright/test"

/** SEO route handlers (Next app/robots.ts + app/sitemap.ts). */
test.describe("SEO endpoints", () => {
  test("robots.txt allows crawl + references the sitemap", async ({ request }) => {
    const res = await request.get("/robots.txt")
    expect(res.ok()).toBeTruthy()
    const body = await res.text()
    expect(body).toContain("Sitemap:")
    expect(body.toLowerCase()).toContain("disallow")
  })

  test("sitemap.xml lists the public routes", async ({ request }) => {
    const res = await request.get("/sitemap.xml")
    expect(res.ok()).toBeTruthy()
    const body = await res.text()
    expect(body).toContain("<urlset")
    expect(body).toContain("/demo")
    expect(body).toContain("/pricing")
  })
})
