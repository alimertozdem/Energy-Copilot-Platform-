# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: auth-guard.spec.ts >> auth guards + 404 >> /alerts redirects to landing when unauthenticated
- Location: e2e\auth-guard.spec.ts:12:9

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: page.goto: Test timeout of 30000ms exceeded.
Call log:
  - navigating to "http://localhost:3000/alerts", waiting until "load"

```

# Page snapshot

```yaml
- generic [ref=e13]: Loading alerts…
```

# Test source

```ts
  1  | import { test, expect } from "@playwright/test"
  2  | 
  3  | /**
  4  |  * Auth-walled routes server-redirect to the landing ("/") when there is no
  5  |  * session, and an unknown route renders the branded 404. We assert the landing
  6  |  * is reached by looking for its demo CTA after navigation.
  7  |  */
  8  | const GUARDED = ["/portfolio", "/settings", "/actions", "/alerts"]
  9  | 
  10 | test.describe("auth guards + 404", () => {
  11 |   for (const path of GUARDED) {
  12 |     test(`${path} redirects to landing when unauthenticated`, async ({ page }) => {
> 13 |       await page.goto(path)
     |                  ^ Error: page.goto: Test timeout of 30000ms exceeded.
  14 |       await expect(
  15 |         page.getByRole("link", { name: /Explore the Live Dashboard/i })
  16 |       ).toBeVisible()
  17 |     })
  18 |   }
  19 | 
  20 |   test("unknown route shows the branded 404", async ({ page }) => {
  21 |     await page.goto("/this-route-does-not-exist-xyz")
  22 |     await expect(page.getByText(/Page not found/i)).toBeVisible()
  23 |   })
  24 | })
  25 | 
```