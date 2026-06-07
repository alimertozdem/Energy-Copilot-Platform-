import type { Metadata, Viewport } from "next";
import { Inter, Space_Grotesk } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { cn } from "@/lib/utils";

const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin"],
});

const spaceGrotesk = Space_Grotesk({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["500", "700"],
});

// Public origin the OG + canonical URLs resolve against. Defaults to the bought
// domain; override per-environment with NEXT_PUBLIC_SITE_URL (Vercel preview,
// local tunnel) so shared links and the OG image resolve to absolute URLs.
const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://energylens.eu";

const TITLE_DEFAULT = "EnergyLens — Commercial Building Intelligence";
const DESCRIPTION =
  "Turn commercial-building energy data into decisions: portfolio KPIs, anomaly alerts, battery & solar ROI, and an AI copilot — built on Microsoft Fabric.";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: TITLE_DEFAULT,
    template: "%s · EnergyLens",
  },
  description: DESCRIPTION,
  applicationName: "EnergyLens",
  keywords: [
    "energy management",
    "commercial buildings",
    "building energy intelligence",
    "Microsoft Fabric",
    "ESG reporting",
    "CRREM pathways",
    "battery storage ROI",
    "solar self-consumption",
    "IoT BACnet Modbus MQTT",
  ],
  authors: [{ name: "EnergyLens" }],
  creator: "EnergyLens",
  alternates: { canonical: "/" },
  openGraph: {
    type: "website",
    siteName: "EnergyLens",
    url: "/",
    title: TITLE_DEFAULT,
    description: DESCRIPTION,
    locale: "en",
  },
  twitter: {
    card: "summary_large_image",
    title: TITLE_DEFAULT,
    description: DESCRIPTION,
  },
  icons: {
    icon: [
      { url: "/icon.svg", type: "image/svg+xml" },
      { url: "/favicon.ico", sizes: "any" },
    ],
  },
  manifest: "/manifest.webmanifest",
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  themeColor: "#1D9E75",
  colorScheme: "dark",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={cn("h-full antialiased", inter.variable, spaceGrotesk.variable)}
    >
      <body className="min-h-full flex flex-col bg-bg-base text-text-primary">
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-brand-emerald focus:px-4 focus:py-2 focus:text-bg-base focus:shadow-lg"
        >
          Skip to content
        </a>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
