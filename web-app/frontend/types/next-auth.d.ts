/**
 * NextAuth interface augmentation.
 *
 * Adds `accessToken` to User, JWT, and Session so the backend JWT can flow
 * through the NextAuth callbacks in a type-safe way:
 *
 *   signIn callback:   sets `user.accessToken` from /auth/sync response
 *   jwt callback:      copies `user.accessToken` -> `token.accessToken`
 *   session callback:  copies `token.accessToken` -> `session.accessToken`
 *
 * Server-side fetch helpers (lib/api/*.ts) call `getServerSession()` and read
 * `session.accessToken` to forward as Authorization: Bearer <jwt>.
 */
import "next-auth"
import "next-auth/jwt"

declare module "next-auth" {
  interface User {
    accessToken?: string
  }

  interface Session {
    accessToken?: string
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    accessToken?: string
  }
}
