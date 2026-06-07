import { test, expect } from "@playwright/test"

/**
 * Auth-walled routes server-redirect to the landing ("/") when there is no
 * session, and an unknown route renders the branded 404. We assert the landing
 * is reached by looking for its demo CTA after navigation.
 */
const GUARDED = ["/portfolio", "/settings", "/actions", "/alerts"]

test.describe("auth guards + 404", () => {
  for (const path of GUARDED) {
    test(`${path} redirects to landing when unauthenticated`, async ({ page }) => {
      await page.goto(path)
      await expect(
        page.getByRole("link", { name: /Explore the Live Dashboard/i })
      ).toBeVisible()
    })
  }

  test("unknown route shows the branded 404", async ({ page }) => {
    await page.goto("/this-route-does-not-exist-xyz")
    await expect(page.getByText(/Page not found/i)).toBeVisible()
  })
})
