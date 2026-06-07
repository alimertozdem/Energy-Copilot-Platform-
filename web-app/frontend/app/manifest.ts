import type { MetadataRoute } from "next"

/**
 * Web app manifest (served at /manifest.webmanifest). Light PWA polish: a
 * branded install name, dark navy background, emerald theme. Icon is the SVG
 * mark (favicon.ico stays the raster fallback).
 */
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "EnergyLens — Commercial Building Intelligence",
    short_name: "EnergyLens",
    description: "Smart energy for smart buildings",
    start_url: "/",
    display: "standalone",
    background_color: "#0A1628",
    theme_color: "#1D9E75",
    icons: [
      {
        src: "/icon.svg",
        sizes: "any",
        type: "image/svg+xml",
        purpose: "any",
      },
    ],
  }
}
