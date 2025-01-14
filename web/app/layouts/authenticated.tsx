import { Outlet } from "react-router"

import { RedirectToSignIn, SignedIn, SignedOut } from "@clerk/clerk-react"

// This layout assumes the user is authenticated. Any clientLoaders making authenticated
// requests will run an additional check and redirect the user to the login page if it fails.
// Additionally, all authenticated routes will 400 if not auth'd propely.

export default function AuthenticatedLayout() {
  return (
    <>
      <SignedIn>
        <Outlet />
      </SignedIn>
      <SignedOut>
        <RedirectToSignIn />
      </SignedOut>
    </>
  )
}
