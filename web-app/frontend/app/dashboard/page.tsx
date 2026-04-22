"use client"
import { useSession, signOut } from "next-auth/react"
import { useRouter } from "next/navigation"
import { useEffect } from "react"
import Image from "next/image"

export default function Dashboard() {
  const { data: session, status } = useSession()
  const router = useRouter()

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/")
    }
  }, [status, router])

  if (status === "loading") {
    return (
      <main className="min-h-screen bg-gray-950 flex items-center justify-center">
        <p className="text-white">Loading...</p>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-gray-950 text-white">
      <nav className="bg-gray-900 border-b border-gray-800 px-6 py-4 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <Image src="/logo.svg" alt="EnergyLens" width={36} height={36} />
          <div className="text-left leading-none">
            <span className="text-gray-500 text-xs tracking-widest uppercase">energy</span>
            <div className="text-lg font-bold text-white">Lens</div>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-gray-400 text-sm">{session?.user?.email}</span>
          <button
            onClick={() => signOut({ callbackUrl: "/" })}
            className="bg-gray-700 hover:bg-gray-600 text-white text-sm px-4 py-2 rounded-lg"
          >
            Sign Out
          </button>
        </div>
      </nav>
      <div className="p-8">
        <h2 className="text-2xl font-bold mb-2">Welcome, {session?.user?.name}</h2>
        <p className="text-gray-400">Dashboard coming soon...</p>
      </div>
    </main>
  )
}