import { test as setup, expect } from "@playwright/test"
import fs from "node:fs"

/**
 * Authenticated-session setup.
 *
 * Runs only under the "setup" project, which is registered only when
 * E2E_EMAIL + E2E_PASSWORD are present (see playwright.config.ts). It logs in
 * through the real NextAuth Credentials flow and saves the resulting session to
 * e2e/.auth/user.json, which the "authed" project reuses as storageState — so
 * the login happens once, not per test.
 *
 * Requires (Mert runs these):
 *   - The Next.js dev server (started by the webServer config) AND the FastAPI
 *     backend running, so the Credentials provider can validate against the DB.
 *   - A real account: point E2E_EMAIL / E2E_PASSWORD at an existing user
 *     (create one via /signup once, or use a dedicated e2e account).
 *
 *   E2E_EMAIL=e2e@energylens.eu E2E_PASSWORD=... npx playwright test
 */
const AUTH_FILE = "e2e/.auth/user.json"

setup("authenticate", async ({ page }) => {
  const email = process.env.E2E_EMAIL
  const password = process.env.E2E_PASSWORD
  // Belt-and-suspenders: the project is already gated on these in the config.
  setup.skip(!email || !password, "Set E2E_EMAIL and E2E_PASSWORD")

  await page.goto("/login")
  await page.fill("#email", email!)
  await page.fill("#password", password!)
  await page.getByRole("button", { name: /^Sign in$/ }).click()

  // Credentials sign-in is client-side (redirect:false) then router.push().
  // A successful login leaves /login; a failure stays put and shows an error,
  // so this wait fails loudly on bad credentials / missing user / backend down.
  await page.waitForURL((url) => !url.pathname.startsWith("/login"), {
    timeout: 30_000,
  })

  // Prove the session passes the server-side guard (guarded routes bounce
  // unauthenticated visitors to the public landing).
  await page.goto("/settings")
  await expect(
    page.getByRole("link", { name: /Explore the Live Dashboard/i })
  ).toHaveCount(0)
  await expect(page.getByRole("button", { name: /Sign Out/i })).toBeVisible()

  fs.mkdirSync("e2e/.auth", { recursive: true })
  await page.context().storageState({ path: AUTH_FILE })
})
