import { Navigate } from "react-router"

import { SignIn, SignedIn, SignedOut } from "@clerk/clerk-react"

// redirect users to the correct page based on their authentication status
export default function LoginRedirect() {
  return (
    <>
      <SignedIn>
        {/* TODO used typed routes */}
        <Navigate to="/notes" />
      </SignedIn>
      <SignedOut>
        <SignIn />
      </SignedOut>
    </>
  )
}
