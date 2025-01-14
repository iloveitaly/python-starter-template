import { setToken } from "~/configuration/client"

import { ClerkProvider } from "@clerk/clerk-react"
import { loadClerkJsScript } from "@clerk/shared/loadClerkJsScript"
import { invariant } from "@epic-web/invariant"

// required in prod and dev
const CLERK_PUBLIC_KEY = import.meta.env.VITE_CLERK_PUBLIC_KEY
invariant(CLERK_PUBLIC_KEY, "Missing Clerk Key")

/*
This whole situation isn't great. Here's what is happening:

- The ClerkProvider is a React component that wraps the entire app. It looks like it hits the Clerk API
  but should also set window.Clerk. However, the clientLoaders seem to be loaded before the providers
  (at least sometimes) so we need to load the clerk client in a way that will play well with the provider
  to avoid additional API calls to Clerk.

- There's not an easy way to do this. This insane `loadClerkJsScript` function is the only way I've found.
  `IsomorphicClerk.getOrCreateInstance(options)` is what react uses, but that is not exposed to us.

- The clerk-js package is not bundled in a way that can be split, so it greatly increases bundle size when
  used directly.

- This method is assumed to be called in a clientLoader.
*/

export async function getClient() {
  if (!window.Clerk) {
    // recommended officially here:
    // https://clerk.com/docs/references/sdk/frontend-only#call-window-clerk-load
    await loadClerkJsScript({
      publishableKey: CLERK_PUBLIC_KEY,
    })
  }

  invariant(window.Clerk, "Clerk should be defined")

  const clerk = window.Clerk

  if (!clerk.loaded) {
    await clerk.load()
  }

  // protect users from hitting the internal API if they aren't authenticated
  if (!clerk.user) {
    await clerk.redirectToSignIn()
    return
  }

  // IMPORTANT: this sets the bearer token for all requests to the internal backend API
  await setToken(clerk)

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
