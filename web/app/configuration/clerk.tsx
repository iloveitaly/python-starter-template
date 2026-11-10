import { requireEnv } from "~/utils/environment"

import { Clerk } from "@clerk/clerk-js"
import { ClerkProvider } from "@clerk/react"
import type { ClerkOptions } from "@clerk/shared/types"
import { ui } from "@clerk/ui"
import { invariant } from "@epic-web/invariant"

const CLERK_PUBLIC_KEY = requireEnv("VITE_CLERK_PUBLIC_KEY")

/*
clientLoaders run before ClerkProvider, so both must share an instance
the provider skips load() for an already-loaded instance, so our load() must
include UI and redirect options as well
https://github.com/clerk/javascript/issues/8569
*/

const clerkOptions = {
  ui,
  signInFallbackRedirectUrl: "/",
  signUpFallbackRedirectUrl: "/",
  afterSignOutUrl: "/login",
} satisfies ClerkOptions

// react router prerenders the root in node even with ssr disabled
const clerk =
  typeof document === "undefined" ? undefined : new Clerk(CLERK_PUBLIC_KEY)

let loadPromise: Promise<void> | undefined

async function getClerk() {
  invariant(clerk, "clerk is only available in the browser")

  if (!clerk.loaded) {
    // https://clerk.com/docs/js-frontend/reference/objects/clerk#load
    loadPromise ??= clerk.load(clerkOptions)
    await loadPromise
  }

  return clerk
}

/**
 * Clerk client for authenticated requests; redirects unless `requireLoggedIn: false` is passed
 *
 * Assumed to be called in a clientLoader, or automatically called by HeyAPI.
 */
export async function getClient({ requireLoggedIn = true } = {}) {
  const clerk = await getClerk()

  // protect users from hitting the internal API if they aren't authenticated
  if (requireLoggedIn && !clerk.user) {
    await clerk.redirectToSignIn()

    // redirectToSignIn only queues the navigation, so this page keeps running until the new
    // document commits. never settling parks callers for that window rather than letting them
    // run on with no session and flash an error page just before the redirect lands.
    return new Promise<never>(() => {})
  }

  return clerk
}

export default function withClerkProvider<Props extends object>(
  Component: React.ComponentType<Props>,
) {
  return (props: Props) => (
    <ClerkProvider
      // hand the already-loaded instance to the provider so IsomorphicClerk reuses it
      // instead of hotloading clerk-js again and re-calling `.load()` (extra API call)
      // https://github.com/clerk/javascript/issues/8569
      Clerk={clerk}
      publishableKey={CLERK_PUBLIC_KEY}
      {...clerkOptions}
    >
      <Component {...props} />
    </ClerkProvider>
  )
}
