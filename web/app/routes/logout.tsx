/**
 * A dedicated route for users to easily logout of the application.
 *
 * - the default fallback URL is configured in ClerkProvider in clerk.tsx and cannot be overridden through this route
 * - <PosthogIdentity /> handles posthog state syncing based on the login state
 * - logout does not accept a redirect URL; query parameters cannot change the destination
 * - use Clerk's <SignOutButton redirectUrl="/destination"> when you need to redirect after logout
 * - You can use `signOut` anywhere else in the application, no need to use this route for logout
 */
import type { Route } from "./+types/logout"

import { getClient } from "~/configuration/clerk"

export async function clientLoader(_loaderArgs: Route.ClientLoaderArgs) {
  // logout must also work when the session has already expired
  const clerk = await getClient({ requireLoggedIn: false })
  await clerk.signOut()

  return null
}

export default function LogoutPage() {
  // Clerk redirects after sign-out; the authenticated layout shows sign-in if already logged out
  return null
}
