import { defineConfig, devices } from "@playwright/test"

/**
 * Playwright suite for the EnergyLens web app.
 *
 * Public suite (always): public render (/, /pricing, /demo, /login, /signup),
 * SEO endpoints, auth-guard redirects, branded 404. Needs only `npm run dev`.
 *
 * Authenticated suite (opt-in): runs only when E2E_EMAIL + E2E_PASSWORD are set.
 * The "setup" project logs in once (auth.setup.ts) and saves a session that the
 * "authed" project reuses. Needs the dev server AND the FastAPI backend up, and
 * a real account in those env vars.
 *
 * Run:  npm run dev   (+ backend for the authed suite)
 *       npx playwright test
 *       E2E_EMAIL=e2e@energylens.eu E2E_PASSWORD=... npx playwright test
 * Override target: E2E_BASE_URL=https://staging.energylens.eu npx playwright test
 */
const hasAuthCreds = !!(process.env.E2E_EMAIL && process.env.E2E_PASSWORD)
const AUTH_FILE = "e2e/.auth/user.json"

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: "list",
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
      // Public/SEO/guard specs — no session. Exclude the authed setup + specs.
      testIgnore: [/auth\.setup\.ts/, /authed\.spec\.ts/],
    },
    // The authenticated suite only registers when credentials are provided, so
    // a plain `npx playwright test` (no creds) runs just the public suite and
    // never trips over a missing storageState file.
    ...(hasAuthCreds
      ? [
          {
            name: "setup",
            use: { ...devices["Desktop Chrome"] },
            testMatch: /auth\.setup\.ts/,
          },
          {
            name: "authed",
            use: { ...devices["Desktop Chrome"], storageState: AUTH_FILE },
            testMatch: /authed\.spec\.ts/,
            dependencies: ["setup"],
          },
        ]
      : []),
  ],
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
})
