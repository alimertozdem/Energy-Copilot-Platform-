import type { MetadataRoute } from "next"

/**
 * Sitemap (served at /sitemap.xml). Only the public surfaces are listed — the
 * rest of the app is auth-walled and intentionally excluded (see robots.ts).
 * URLs are absolute via NEXT_PUBLIC_SITE_URL (defaults to the bought domain).
 */
const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://energylens.eu"

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date()
  return [
    {
      url: SITE_URL,
      lastModified: now,
      changeFrequency: "weekly",
      priority: 1,
    },
    {
      url: `${SITE_URL}/demo`,
      lastModified: now,
      changeFrequency: "weekly",
      priority: 0.8,
    },
    {
      url: `${SITE_URL}/pricing`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.7,
    },
  ]
}
