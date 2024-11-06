import { ClerkProvider } from "@clerk/clerk-react"
import { invariant } from "@epic-web/invariant"

// required in prod and dev
const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY
invariant(PUBLISHABLE_KEY, "Missing Clerk Key")

export default function withClerkProvider(Component: React.ComponentType) {
  return (props: React.ComponentProps<typeof Component>) => (
    <ClerkProvider publishableKey={PUBLISHABLE_KEY} afterSignOutUrl="/">
      <Component {...props} />
    </ClerkProvider>
  )
}
