import { Navigate, href } from "react-router"

import { SignIn, SignedIn, SignedOut } from "~/configuration/clerk"

// redirect users to the correct page based on their authentication status
export default function LoginRedirect() {
  return (
    <div className="mt-[10%] flex min-h-screen justify-center">
      Hello World
     {/*<SignedIn>
        <Navigate to={href("/home")} />
      </SignedIn>
      <SignedOut>
        <SignIn />
      </SignedOut>*/}
    </div>
  )
}
