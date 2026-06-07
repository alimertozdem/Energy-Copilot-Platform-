import type { MetadataRoute } from "next"

/**
 * robots.txt (served at /robots.txt). Allow the public marketing surfaces
 * (/ and /demo); disallow the auth-walled app + API so crawlers don't hit
 * login-gated pages. References the sitemap for discovery.
 */
const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://energylens.eu"

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: ["/", "/demo"],
        disallow: [
          "/api/",
          "/portfolio",
          "/buildings",
          "/actions",
          "/alerts",
          "/solar",
          "/copilot",
          "/settings",
          "/admin",
          "/onboarding",
          "/dashboard",
          "/login",
          "/signup",
          "/forgot-password",
          "/invite",
        ],
      },
    ],
    sitemap: `${SITE_URL}/sitemap.xml`,
    host: SITE_URL,
  }
}
