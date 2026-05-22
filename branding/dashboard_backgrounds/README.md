# EnergyLens — Dashboard Backgrounds

Brand-aligned 1920×1080 PNG backgrounds for all 9 Power BI report pages.
Generated 2026-05-11 from the approved Emerald Pulse brand identity.

---

## Files & Page Mapping

| # | File | Power BI page name | Accent color |
|---|---|---|---|
| 1 | `page_01_portfolio_bg.png` | Portfolio Overview | Emerald `#1D9E75` |
| 2 | `page_02_building_bg.png` | Building Detail | Mint `#5DCAA5` |
| 3 | `page_03_anomalies_bg.png` | Anomalies & Alerts | Coral `#D85A30` |
| 4 | `page_04_forecast_bg.png` | Forecast & Recommendations | Blue `#378ADD` |
| 5 | `page_05_occupancy_bg.png` | Occupancy Analysis | Amber `#EF9F27` |
| 6 | `page_06_sustainability_bg.png` | Sustainability & Compliance | Lime `#97C459` |
| 7 | `page_07_hvac_bg.png` | HVAC & Building Envelope | Burnt amber `#BA7517` |
| 8 | `page_08_iot_bg.png` | IoT & Real-Time Monitoring | Mint cyan `#5DCAA5` |
| 9 | `page_09_battery_dispatch_bg.png` | Battery Dispatch & Financial Simulation | Deep blue `#185FA5` |

Each page has the same DNA — graphite-emerald base, EnergyLens logo top-left, stacked page title with vertical accent bar, page number top-right, footer bottom — but its own color ruhu and thematic motif behind the visuals.

---

## How to Apply in Power BI Desktop

For every page in the report:

1. Open the report in **Power BI Desktop**.
2. Select the page tab (bottom).
3. Open the **Format** pane (right side, no visual selected). It will show **Page** settings.
4. Expand **Canvas background**.
5. Set:
   - **Image** → Browse → select the matching PNG from `branding/dashboard_backgrounds/`
   - **Image fit** → `Fit`
   - **Transparency** → `0%`
6. Optional: Under **Canvas settings**, ensure **Type** = `16:9` (or Custom 1280×720 / 1920×1080).

Repeat for all 9 pages. The visuals you already have stay on top — only the canvas changes.

---

## Visual Layout Recommendation

The backgrounds reserve specific areas — move your existing visuals to fit:

- **Top band (y = 0 – 220 px)** → leave clear. This is where the logo, page title, and page badge live.
- **KPI card row (y = 220 – 380 px)** → keep KPI cards compact here. Tighter than before — gives more room to charts.
- **Chart area (y = 380 – 1050 px)** → main visuals. Expand charts to fill this space.
- **Side panel (x = 0 – 280 px, y = 220 – 1050 px)** → slicers, map, side KPIs.
- **Footer (y = 1050 – 1080 px)** → leave clear. Footer text is part of the background.

The subtle motif behind your visuals (skyline, leaves, network, etc.) is at ~5–15% opacity, so it won't compete with chart readability — but it will give each page its own story.

---

## Per-Page Theme & Motif

| # | Theme | Story | Background motif |
|---|---|---|---|
| 1 | Portfolio Overview | "Multi-building intelligence at a glance" | Full skyline silhouette across bottom + window dots |
| 2 | Building Detail | "One building, every signal" | One tall stepped tower right side + measurement grid |
| 3 | Anomalies & Alerts | "Catch what shouldn't be there" | Concentric warning rings + scattered alert dots |
| 4 | Forecast & Recommendations | "See tomorrow, act today" | Sine forecast curve + dashed projection + data nodes |
| 5 | Occupancy Analysis | "Energy meets human rhythm" | Faint 7×22 heatmap grid centered |
| 6 | Sustainability & Compliance | "Decarbonize on schedule" | Rotated leaves + vine curves |
| 7 | HVAC & Building Envelope | "Where heat lives and leaks" | Horizontal thermal waves + radiator fins right |
| 8 | IoT & Real-Time Monitoring | "The building, live" | Sensor node network with connecting lines |
| 9 | Battery Dispatch | "Store, shift, save" | 4×10 battery cell grid + flow arrow |

---

## Regeneration

To rebuild the backgrounds (e.g., palette tweaks, page title changes):

```bash
cd <project root>
python3 outputs/generate_backgrounds.py
# PNGs land in outputs/backgrounds/
# Copy them back over branding/dashboard_backgrounds/
```

The script lives at `outputs/generate_backgrounds.py` (in the working folder) — all tunable parameters (colors, motifs, fonts, layout coordinates) are in the `PAGES` config and individual `motif_*` functions.

---

## Brand DNA Used Here

- **Mark:** simplified Emerald Pulse logo — magnifier lens framing a 4-building skyline with spotlight pulse on the tallest tower
- **Wordmark:** Lato Heavy 52px — "Energy" white, "Lens" in page accent
- **Tagline:** "Smart energy for smart buildings" — Lato Light 17px
- **Title typography:** Lato Heavy 60px (line 1, white) + 38px (line 2, accent)
- **Base color:** deep emerald, slightly different hue per page (graphite-emerald foundation)
- **Accent color:** unique per page — see table above
- **Soft accent:** lighter shade of accent, used for tagline, footer, page badge

Anything off-palette in future visuals (chart fills, KPI card borders, slicer accents) should be picked from this same system so the whole report feels like one product.
