import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Headless-Chromium PDF route: keep native binaries out of the bundle.
  serverExternalPackages: ["@sparticuz/chromium", "puppeteer-core"],
};

export default nextConfig;
