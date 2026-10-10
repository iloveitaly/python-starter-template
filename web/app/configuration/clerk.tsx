import { requireEnv } from "~/utils/environment"

import { Clerk } from "@clerk/clerk-js"
import { ClerkProvider } from "@clerk/react"
import type {
  ClerkOptions,
  SignedInSessionResource,
  UserResource,
} from "@clerk/shared/types"
import { ui } from "@clerk/ui"
import { invariant } from "@epic-web/invariant"

const CLERK_PUBLIC_KEY = requireEnv("VITE_CLERK_PUBLIC_KEY")

/*
`clientLoader`s run before the react render cycle, so they can't get a session token from
ClerkProvider. We own the clerk instance instead and hand it to the provider, which keeps
both paths on a single instance rather than each hitting the Clerk API separately.

Two things about that handoff are easy to get wrong:

- ClerkProvider only attaches the prebuilt UI inside its own `.load()` call, which it skips
  entirely for an already-loaded instance. So `ui` has to be passed to *our* `load()`, or
  <SignIn>/<UserButton> throw "Clerk was not loaded with Ui components".
  https://github.com/clerk/javascript/issues/8569

- For the same reason, `ClerkOptions` set as ClerkProvider props are dropped. Anything that
  belongs in `load()` goes in `clerkOptions` below so both callers stay in sync.
*/

const clerkOptions = {
  signInFallbackRedirectUrl: "/",
  signUpFallbackRedirectUrl: "/",
} satisfies ClerkOptions

// react-router builds with `ssr: false`, but it still renders the root route in node to
// emit index.html, and clerk-js reaches for browser globals as soon as it's constructed
const clerk =
  typeof document === "undefined" ? undefined : new Clerk(CLERK_PUBLIC_KEY)

let loadPromise: Promise<void> | undefined

function getClerk() {
  invariant(clerk, "clerk is only available in the browser")

  loadPromise ??= clerk.load({ ...clerkOptions, ui })

  return loadPromise.then(() => clerk)
}

type AuthenticatedClerk = Clerk & {
  user: UserResource
  session: SignedInSessionResource
}

function isAuthenticated(clerk: Clerk): clerk is AuthenticatedClerk {
  return Boolean(clerk.user && clerk.session)
}

/**
 * Clerk client for authenticated requests, guaranteed to have a user and session.
 *
 * Assumed to be called in a clientLoader, or automatically called by HeyAPI.
 */
export async function getClient(): Promise<AuthenticatedClerk> {
  const clerk = await getClerk()

  // protect users from hitting the internal API if they aren't authenticated
  if (!isAuthenticated(clerk)) {
    await clerk.redirectToSignIn()

    // redirectToSignIn only queues the navigation, so this page keeps running until the new
    // document commits. never settling parks callers for that window rather than letting them
    // run on with no session and flash an error page just before the redirect lands.
    return new Promise<never>(() => {})
  }

  return clerk
}

export default function withClerkProvider(Component: React.ComponentType) {
  return (props: React.ComponentProps<typeof Component>) => (
    <ClerkProvider
      // without this the provider hotloads its own clerk-js from the CDN and builds a
      // second, unrelated instances
      Clerk={clerk}
      ui={ui}
      publishableKey={CLERK_PUBLIC_KEY}
      {...clerkOptions}
    >
      <Component {...props} />
    </ClerkProvider>
  )
}
