import { test, expect } from "@playwright/test"

/** Public marketing/auth surfaces render without a session. */
test.describe("public pages", () => {
  test("landing shows the demo + sign-in CTAs", async ({ page }) => {
    await page.goto("/")
    await expect(
      page.getByRole("link", { name: /Explore the Live Dashboard/i })
    ).toBeVisible()
    await expect(
      page.getByRole("button", { name: /Sign in with Microsoft/i })
    ).toBeVisible()
  })

  test("pricing page shows all four tiers", async ({ page }) => {
    await page.goto("/pricing")
    await expect(page.getByRole("heading", { name: /Plans.*pricing/i })).toBeVisible()
    for (const tier of ["Free", "Basic", "Monitor", "Enterprise"]) {
      await expect(
        page.getByRole("heading", { name: tier, exact: true })
      ).toBeVisible()
    }
    await expect(page.getByText("Most popular")).toBeVisible()
  })

  test("demo shell renders without signup", async ({ page }) => {
    await page.goto("/demo")
    await expect(page.getByText("Sample Buildings")).toBeVisible()
    await expect(
      page.getByText(/Commercial-building energy intelligence/i)
    ).toBeVisible()
  })

  test("login and signup pages load a form", async ({ page }) => {
    await page.goto("/login")
    await expect(page.locator("input").first()).toBeVisible()
    await page.goto("/signup")
    await expect(page.locator("input").first()).toBeVisible()
  })
})
