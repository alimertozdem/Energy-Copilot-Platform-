import { test, expect } from "@playwright/test"

/**
 * Authenticated render checks — run only under the "authed" project, which
 * injects a logged-in storageState (see playwright.config.ts + auth.setup.ts).
 *
 * Intent: catch the auth wiring silently breaking. A logged-in user must reach
 * the protected app shell, not bounce to the public landing. Assertions target
 * the authenticated chrome (Sign Out, nav, top-bar links), not Fabric data — so
 * they stay green when the portfolio is empty or Fabric is temporarily
 * unavailable (the pages degrade gracefully).
 */
const LANDING_CTA = /Explore the Live Dashboard/i

// AppChrome-wrapped routes that don't persona-redirect when visited directly.
const SHELL_ROUTES = ["/actions", "/alerts", "/settings", "/copilot"]

test.describe("authenticated app shell", () => {
  for (const path of SHELL_ROUTES) {
    test(`${path} renders the authed shell (no guard bounce)`, async ({ page }) => {
      await page.goto(path)
      // Not bounced to the public landing => the session is valid.
      await expect(page.getByRole("link", { name: LANDING_CTA })).toHaveCount(0)
      await expect(page).not.toHaveURL(/\/login(\?|$)/)
      // AppChrome renders on every authenticated route.
      await expect(page.getByRole("button", { name: /Sign Out/i })).toBeVisible()
    })
  }

  test("/portfolio is reachable under a session", async ({ page }) => {
    await page.goto("/portfolio")
    await expect(page.getByRole("link", { name: LANDING_CTA })).toHaveCount(0)
    // Portfolio itself, or onboarding/buildings for accounts without data yet.
    await expect(page).toHaveURL(/\/(portfolio|onboarding|buildings)/)
  })

  test("top-bar Glossary link opens /glossary", async ({ page }) => {
    await page.goto("/settings")
    await page.getByRole("link", { name: "Glossary" }).click()
    await expect(page).toHaveURL(/\/glossary/)
    await expect(page.getByRole("heading", { name: "Glossary" })).toBeVisible()
  })
})
