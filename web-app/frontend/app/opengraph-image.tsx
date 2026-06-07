import { ImageResponse } from "next/og"

/**
 * Site-wide Open Graph image (App Router file convention).
 *
 * Renders a branded 1200x630 card at request time via next/og (Satori) — no
 * binary asset checked into the repo. Applies to every route that does not
 * define its own opengraph-image, so `/` and `/demo` share this card when a
 * link is pasted into LinkedIn, email, Slack, or a grant portal.
 *
 * Satori notes: every multi-child element sets display:flex; colours come from
 * the EnergyLens palette (navy #0A1628 base, emerald #1D9E75); default font is
 * used (Latin only) so no runtime font fetch is required.
 */
export const alt = "EnergyLens — Smart energy for smart buildings"
export const size = { width: 1200, height: 630 }
export const contentType = "image/png"

// Skyline silhouette heights (brand "building" motif).
const BARS = [60, 112, 84, 150, 96, 132, 72, 120, 54, 142, 88, 106]

export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: "72px 80px",
          backgroundColor: "#0A1628",
          backgroundImage:
            "radial-gradient(900px circle at 0% 0%, rgba(29,158,117,0.38), rgba(10,22,40,0) 55%), radial-gradient(760px circle at 100% 110%, rgba(6,182,212,0.20), rgba(10,22,40,0) 52%)",
          fontFamily: "sans-serif",
          color: "#E8EEF5",
        }}
      >
        {/* Brand block */}
        <div style={{ display: "flex", flexDirection: "column" }}>
          <div style={{ display: "flex", alignItems: "center", marginBottom: 26 }}>
            <div
              style={{
                display: "flex",
                width: 14,
                height: 14,
                borderRadius: 999,
                backgroundColor: "#1D9E75",
                marginRight: 14,
              }}
            />
            <div
              style={{
                display: "flex",
                fontSize: 22,
                letterSpacing: 5,
                color: "#5DCAA5",
                textTransform: "uppercase",
              }}
            >
              Commercial Building Intelligence
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "baseline" }}>
            <div
              style={{
                display: "flex",
                fontSize: 110,
                fontWeight: 700,
                letterSpacing: -3,
                color: "#FFFFFF",
              }}
            >
              Energy
            </div>
            <div
              style={{
                display: "flex",
                fontSize: 110,
                fontWeight: 700,
                letterSpacing: -3,
                color: "#1D9E75",
              }}
            >
              Lens
            </div>
          </div>

          <div style={{ display: "flex", fontSize: 36, color: "#9FB3C8", marginTop: 16 }}>
            Smart energy for smart buildings
          </div>
        </div>

        {/* Skyline motif */}
        <div style={{ display: "flex", alignItems: "flex-end", height: 152 }}>
          {BARS.map((h, i) => (
            <div
              key={i}
              style={{
                display: "flex",
                width: 56,
                height: h,
                marginRight: i === BARS.length - 1 ? 0 : 14,
                borderRadius: 10,
                backgroundColor:
                  i % 3 === 0
                    ? "rgba(29,158,117,0.55)"
                    : i % 3 === 1
                    ? "rgba(93,202,165,0.42)"
                    : "rgba(6,182,212,0.30)",
              }}
            />
          ))}
        </div>

        {/* Footer: stack tags + domain */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ display: "flex", alignItems: "center", fontSize: 22, color: "#7C93AC" }}>
            <div style={{ display: "flex" }}>Microsoft Fabric</div>
            <div style={{ display: "flex", margin: "0 14px" }}>·</div>
            <div style={{ display: "flex" }}>BACnet / Modbus / MQTT</div>
            <div style={{ display: "flex", margin: "0 14px" }}>·</div>
            <div style={{ display: "flex" }}>EU 2023/1542</div>
          </div>
          <div style={{ display: "flex", fontSize: 26, fontWeight: 600, color: "#1D9E75" }}>
            energylens.eu
          </div>
        </div>
      </div>
    ),
    { ...size }
  )
}
