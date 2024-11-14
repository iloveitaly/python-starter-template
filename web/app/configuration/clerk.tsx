import * as clerkPkg from "@clerk/clerk-js"
import { ClerkProvider, Protect } from "@clerk/clerk-react"
import { invariant } from "@epic-web/invariant"

// required in prod and dev
const CLERK_PUBLIC_KEY = import.meta.env.VITE_CLERK_PUBLIC_KEY
invariant(CLERK_PUBLIC_KEY, "Missing Clerk Key")

export async function getClient() {
  // TODO what's terrible about this is I believe the ClerkProvider will hit the clerk API yet again
  const clerk = new clerkPkg.Clerk(import.meta.env.VITE_CLERK_PUBLIC_KEY)
  await clerk.load()
  return clerk
}

export default function withClerkProvider(Component: React.ComponentType) {
  return (props: React.ComponentProps<typeof Component>) => (
    <ClerkProvider
      publishableKey={CLERK_PUBLIC_KEY}
      signInFallbackRedirectUrl="/"
      signUpFallbackRedirectUrl="/"
    >
      <Component {...props} />
    </ClerkProvider>
  )
}
