import { Navigate } from "react-router"

import { SignIn, SignedIn, SignedOut } from "@clerk/clerk-react"
import { $path } from "safe-routes"

// redirect users to the correct page based on their authentication status
export default function LoginRedirect() {
  return (
    <>
      <SignedIn>
        <Navigate to={$path("/home")} />
      </SignedIn>
      <SignedOut>
        <SignIn />
      </SignedOut>
    </>
  )
}
