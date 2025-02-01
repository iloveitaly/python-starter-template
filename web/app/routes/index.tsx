import { Navigate } from "react-router"
import { $path } from "safe-routes"

import { SignIn, SignedIn, SignedOut } from "@clerk/clerk-react"

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
