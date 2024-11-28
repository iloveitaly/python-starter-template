import { setToken } from "~/configuration/client"

import * as clerkPkg from "@clerk/clerk-js"
import { ClerkProvider } from "@clerk/clerk-react"
import { invariant } from "@epic-web/invariant"

// required in prod and dev
const CLERK_PUBLIC_KEY = import.meta.env.VITE_CLERK_PUBLIC_KEY
invariant(CLERK_PUBLIC_KEY, "Missing Clerk Key")

// TODO what's terrible about this is I believe the ClerkProvider will hit the clerk API yet again
// https://discord.com/channels/856971667393609759/1306770317624086649
export async function getClient() {
  // TODO what's terrible about this is I believe the ClerkProvider will hit the clerk API yet again
  const clerk = new clerkPkg.Clerk(import.meta.env.VITE_CLERK_PUBLIC_KEY)
  await clerk.load()

  // protect users from hitting the internal API if they aren't authenticated
  if (!clerk.user) {
    await clerk.redirectToSignIn()
    return
  }

  await setToken(clerk)

  return clerk
}

export default function withClerkProvider(Component: React.ComponentType) {
  return (props: React.ComponentProps<typeof Component>) => (
    <ClerkProvider
      publishableKey={CLERK_PUBLIC_KEY}
      signInFallbackRedirectUrl="/home"
      signUpFallbackRedirectUrl="/home"
    >
      <Component {...props} />
    </ClerkProvider>
  )
}
