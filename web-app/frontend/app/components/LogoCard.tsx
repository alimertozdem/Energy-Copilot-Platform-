import Image from "next/image"
import { cn } from "@/lib/utils"

type LogoCardProps = {
  className?: string
  /** Rendered height in pixels. Width auto-scales (asset is 230×68, ratio ~3.38:1). */
  iconSize?: number
}

/**
 * EnergyLens logo.
 *
 * The source PNG already contains its own card/background, so this wrapper
 * stays transparent -- just a thin emerald glow border + the image.
 * Asset: public/logo-pbi.png == report-design/.../energylens_logo_card_230x68.png
 */
export function LogoCard({ className, iconSize = 52 }: LogoCardProps) {
  const height = iconSize
  const width = Math.round(iconSize * (230 / 68))

  return (
    <div
      className={cn(
        "inline-flex items-center rounded-lg overflow-hidden",
        "shadow-[0_0_20px_rgba(29,158,117,0.25)] ring-1 ring-brand-emerald/20",
        className
      )}
    >
      <Image
        src="/logo-pbi.png"
        alt="EnergyLens — Smart energy for smart buildings"
        width={width}
        height={height}
        priority
        unoptimized
        className="block"
        style={{ height, width: "auto" }}
      />
    </div>
  )
}
