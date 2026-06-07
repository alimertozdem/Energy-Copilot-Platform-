/**
 * NextAuth configuration -- single source of truth for providers + callbacks.
 *
 * Exported separately from the route handler so server components can call
 * getServerSession(authOptions) without dragging the handler import path.
 *
 * Behavior is identical to the previous inline config in route.ts:
 *   * 3 providers: AzureAD (Microsoft), Google, Credentials (Email)
 *   * signIn callback: POSTs to backend /auth/sync, mutates user.accessToken
 *   * jwt callback:    carries user.accessToken into the NextAuth JWT
 *   * session callback: exposes token.accessToken on session for server fetches
 */
import type { NextAuthOptions } from "next-auth"
import AzureADProvider from "next-auth/providers/azure-ad"
import GoogleProvider from "next-auth/providers/google"
import CredentialsProvider from "next-auth/providers/credentials"

import { syncUserToBackend } from "@/lib/auth/syncUser"
import { loginWithCredentials } from "@/lib/auth/loginWithCredentials"

export const authOptions: NextAuthOptions = {
  providers: [
    AzureADProvider({
      clientId: process.env.AZURE_AD_CLIENT_ID!,
      clientSecret: process.env.AZURE_AD_CLIENT_SECRET!,
      tenantId: process.env.AZURE_AD_TENANT_ID!,
    }),
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
    CredentialsProvider({
      name: "Email",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null
        }
        const result = await loginWithCredentials({
          email: credentials.email,
          password: credentials.password,
        })
        if (!result.ok) {
          // Wrong creds, network error, etc. -- NextAuth rejects login.
          return null
        }
        // Returned object becomes the NextAuth `user` in subsequent callbacks.
        // accessToken is carried via the jwt callback into the session.
        return {
          id: result.data.user_id,
          email: result.data.email,
          name: result.data.display_name,
          image: result.data.avatar_url,
          accessToken: result.data.access_token,
        }
      },
    }),
  ],
  pages: {
    signIn: "/",
  },
  callbacks: {
    async signIn({ user, account, profile }) {
      // Defensive: NextAuth normally guarantees these, but bail clearly if not.
      if (!account || !user?.email) {
        console.error("[signIn] Missing account or user.email — rejecting")
        return false
      }

      // Map NextAuth provider id → backend provider enum.
      const providerMap: Record<string, "microsoft" | "google" | "email"> = {
        "azure-ad": "microsoft",
        google: "google",
        credentials: "email",
      }
      const backendProvider = providerMap[account.provider]
      if (!backendProvider) {
        console.error(`[signIn] Unknown provider: ${account.provider}`)
        return false
      }

      // Google gives us email_verified in profile; Azure AD doesn't,
      // but tenant-authenticated AAD emails are treated as verified.
      // Credentials: not verified in V1 (no email verification flow yet).
      const emailVerified =
        backendProvider === "google"
          ? Boolean((profile as { email_verified?: boolean })?.email_verified)
          : backendProvider === "microsoft"
            ? true
            : false

      // For OAuth providers, provider_user_id is the external account id.
      // For Credentials (email), provider_user_id is the user's email itself
      // (matches the backend's UserAuthProvider row created at signup).
      const providerUserId =
        backendProvider === "email" ? user.email : account.providerAccountId

      const result = await syncUserToBackend({
        email: user.email,
        display_name: user.name ?? null,
        avatar_url: user.image ?? null,
        provider: backendProvider,
        provider_user_id: providerUserId,
        email_verified: emailVerified,
      })

      if (!result.ok) {
        console.error(`[signIn] Sync failed: ${result.error} — rejecting login`)
        return false
      }

      // Mutate the user object so the jwt callback can pick up the access token.
      // NextAuth runs jwt() after signIn() and receives the same user reference
      // on first login -- this is the official channel for carrying provider
      // tokens across callbacks.
      user.accessToken = result.data.access_token

      return true
    },
    async jwt({ token, user }) {
      // On first login, `user` is populated -- carry accessToken into the JWT.
      // On subsequent calls (token refresh), only `token` is present.
      if (user?.accessToken) {
        token.accessToken = user.accessToken
      }
      return token
    },
    async session({ session, token }) {
      // Expose accessToken on the session for server-side fetch helpers.
      // Server-only -- the token never leaves the HTTP-only NextAuth cookie.
      if (token.accessToken) {
        session.accessToken = token.accessToken
      }
      return session
    },
  },
}
