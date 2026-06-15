/**
 * Logo — the EnergyLens mark + wordmark (design language, 2026-06-15).
 *
 * The approved "Living Grid" direction, simplified to read at small sizes:
 * rising green building-bars, a lime→gold energy line sweeping up into a leaf,
 * and a small sun. Replaces the heavy white LogoCard box in the app shell.
 */

export function LogoMark({ size = 36, className }: { size?: number; className?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      aria-hidden
      className={className}
    >
      <defs>
        <linearGradient id="elTower" x1="0" y1="1" x2="1" y2="0">
          <stop offset="0%" stopColor="#0F6E56" />
          <stop offset="55%" stopColor="#1D9E75" />
          <stop offset="100%" stopColor="#2DD4BF" />
        </linearGradient>
        <linearGradient id="elRise" x1="0" y1="1" x2="1" y2="0">
          <stop offset="0%" stopColor="#5DCAA5" />
          <stop offset="52%" stopColor="#C8E66B" />
          <stop offset="100%" stopColor="#F5D061" />
        </linearGradient>
      </defs>
      <rect x="9" y="36" width="9" height="18" rx="2.5" fill="url(#elTower)" />
      <rect x="21" y="28" width="9" height="26" rx="2.5" fill="url(#elTower)" />
      <rect x="33" y="18" width="9" height="36" rx="2.5" fill="url(#elTower)" />
      <rect x="45" y="31" width="9" height="23" rx="2.5" fill="url(#elTower)" />
      <path d="M8 52 C 22 42 32 28 45 19" stroke="url(#elRise)" strokeWidth="4.5" fill="none" strokeLinecap="round" />
      <path d="M45 19 C 51 11 60 12 62 5 C 55 7 48 12 45 19 Z" fill="#7FD9A6" />
      <circle cx="55" cy="11" r="4.6" fill="#F5C94B" />
    </svg>
  )
}

export function Logo({
  size = 36,
  withWordmark = true,
  className,
}: {
  size?: number
  withWordmark?: boolean
  className?: string
}) {
  return (
    <span className={`inline-flex items-center gap-2.5 ${className ?? ""}`}>
      <LogoMark size={size} className="shrink-0" />
      {withWordmark && (
        <span className="font-display text-lg font-semibold leading-none tracking-tight text-text-primary">
          Energy<span className="text-brand-mint">Lens</span>
        </span>
      )}
    </span>
  )
}
