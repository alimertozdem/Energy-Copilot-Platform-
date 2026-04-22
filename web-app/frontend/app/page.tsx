"use client"
import { signIn } from "next-auth/react"
import Image from "next/image"

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-950 flex items-center justify-center">
      <div className="text-center">
        <div className="flex items-center justify-center gap-3 mb-4">
          <Image src="/logo.svg" alt="EnergyLens Logo" width={56} height={56} />
          <div className="text-left">
            <span className="text-gray-400 text-sm font-light tracking-widest uppercase">energy</span>
            <div className="text-3xl font-bold text-white leading-none">Lens</div>
          </div>
        </div>
        <p className="text-gray-500 mb-8 text-sm tracking-wide">
          Commercial Building Intelligence Platform
        </p>
        <button
        onClick={() => signIn("azure-ad", { callbackUrl: "/dashboard" })}
className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-8 py-3 rounded-lg"
>
  Sign in with Microsoft
          
        </button>
      </div>
    </main>
  )
}