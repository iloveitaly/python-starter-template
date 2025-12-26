import { useEffect } from "react"
import { Outlet } from "react-router"

import { usePostHog } from "posthog-js/react"

import AdminBar from "~/components/AdminBar"

import {
  RedirectToSignIn,
  SignedIn,
  SignedOut,
  useAuth,
  useUser,
} from "@clerk/clerk-react"

// This layout assumes the user is authenticated. Any clientLoaders making authenticated
// requests will run an additional check and redirect the user to the login page if it fails.
// Additionally, all authenticated routes will 400 if not auth'd propely.

// TODO it seems as though we don't need to manually trigger a pageview event, that's already done for us
// you must use the same identity key in the backend and frontend so users will be automatically merged
// https://clerk.com/blog/how-to-use-clerk-with-posthog-identify-in-nextjs
function PosthogIdentity() {
  const posthog = usePostHog()
  const { user } = useUser()
  const { isSignedIn, userId } = useAuth()

  useEffect(() => {
    if (isSignedIn && userId && user && !posthog._isIdentified()) {
      posthog.identify(userId, {
        email: user.primaryEmailAddress?.emailAddress,
      })
    }

    if (!isSignedIn && posthog._isIdentified()) {
      posthog.reset()
    }
  }, [posthog, user, isSignedIn, userId])

  return null
}

export default function AuthenticatedLayout() {
  return (
    <>
      <SignedIn>
        <PosthogIdentity />
        <AdminBar />
        <Outlet />
      </SignedIn>
      <SignedOut>
        <RedirectToSignIn />
      </SignedOut>
    </>
  )
}
