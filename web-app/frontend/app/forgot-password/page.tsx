import Link from "next/link"
import { LogoCard } from "@/app/components/LogoCard"

export default function ForgotPassword() {
  return (
    <main id="main-content" className="min-h-screen bg-radial-emerald-glow flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-dot-grid opacity-30 pointer-events-none" />

      <Link
        href="/login"
        className="fixed top-6 left-6 z-20 text-text-faint hover:text-text-muted text-sm transition-colors"
      >
        ← Back to sign in
      </Link>

      <div className="relative z-10 w-full max-w-md">
        <div className="flex justify-center mb-8">
          <LogoCard iconSize={56} />
        </div>

        <div className="bg-bg-elevated border border-border-subtle rounded-lg p-8 text-center shadow-[0_8px_32px_rgba(0,0,0,0.4)]">
          <h1 className="text-2xl font-bold text-text-primary mb-3 tracking-tight">
            Forgot your password?
          </h1>
          <p className="text-text-muted text-sm mb-5">
            Self-service password reset is coming soon.
          </p>
          <p className="text-text-primary text-sm mb-6 leading-relaxed">
            In the meantime, please contact{" "}
            <a
              href="mailto:alimert@energylens.eu"
              className="text-brand-mint hover:text-brand-glow font-medium transition-colors"
            >
              alimert@energylens.eu
            </a>{" "}
            and we&apos;ll reset your password manually.
          </p>
          <Link
            href="/login"
            className="inline-block bg-brand-emerald hover:bg-brand-deep text-white font-medium px-5 py-2 rounded-md text-sm transition-colors shadow-[0_0_24px_rgba(29,158,117,0.2)]"
          >
            Back to sign in
          </Link>
        </div>
      </div>
    </main>
  )
}
