import { Navigate, href } from "react-router"

import { SignIn, SignedIn, SignedOut } from "@clerk/clerk-react"

// redirect users to the correct page based on their authentication status
export default function LoginRedirect() {
  return (
    <div className="mt-[10%] flex min-h-screen justify-center">
      <SignedIn>
        <Navigate to={href("/home")} />
      </SignedIn>
      <SignedOut>
        <SignIn />
      </SignedOut>
    </div>
  )
}
