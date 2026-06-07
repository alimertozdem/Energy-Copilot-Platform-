# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: public.spec.ts >> public pages >> demo shell renders without signup
- Location: e2e\public.spec.ts:26:7

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: page.goto: net::ERR_ABORTED; maybe frame was detached?
Call log:
  - navigating to "http://localhost:3000/demo", waiting until "load"

```

# Test source

```ts
  1  | import { test, expect } from "@playwright/test"
  2  | 
  3  | /** Public marketing/auth surfaces render without a session. */
  4  | test.describe("public pages", () => {
  5  |   test("landing shows the demo + sign-in CTAs", async ({ page }) => {
  6  |     await page.goto("/")
  7  |     await expect(
  8  |       page.getByRole("link", { name: /Explore the Live Dashboard/i })
  9  |     ).toBeVisible()
  10 |     await expect(
  11 |       page.getByRole("button", { name: /Sign in with Microsoft/i })
  12 |     ).toBeVisible()
  13 |   })
  14 | 
  15 |   test("pricing page shows all four tiers", async ({ page }) => {
  16 |     await page.goto("/pricing")
  17 |     await expect(page.getByRole("heading", { name: /Plans.*pricing/i })).toBeVisible()
  18 |     for (const tier of ["Free", "Basic", "Monitor", "Enterprise"]) {
  19 |       await expect(
  20 |         page.getByRole("heading", { name: tier, exact: true })
  21 |       ).toBeVisible()
  22 |     }
  23 |     await expect(page.getByText("Most popular")).toBeVisible()
  24 |   })
  25 | 
  26 |   test("demo shell renders without signup", async ({ page }) => {
> 27 |     await page.goto("/demo")
     |                ^ Error: page.goto: net::ERR_ABORTED; maybe frame was detached?
  28 |     await expect(page.getByText("Sample Buildings")).toBeVisible()
  29 |     await expect(
  30 |       page.getByText(/Commercial-building energy intelligence/i)
  31 |     ).toBeVisible()
  32 |   })
  33 | 
  34 |   test("login and signup pages load a form", async ({ page }) => {
  35 |     await page.goto("/login")
  36 |     await expect(page.locator("input").first()).toBeVisible()
  37 |     await page.goto("/signup")
  38 |     await expect(page.locator("input").first()).toBeVisible()
  39 |   })
  40 | })
  41 | 
```