import { Navigate, href } from "react-router"

import withClerkProvider from "~/configuration/clerk"

import { Show, SignIn } from "@clerk/react"

function LoginRedirectPage() {
  return (
    <div className="mt-[10%] flex min-h-screen justify-center">
      <Show when="signed-in">
        <Navigate to={href("/home")} />
      </Show>
      <Show when="signed-out">
        <SignIn />
      </Show>
    </div>
  )
}

export default withClerkProvider(LoginRedirectPage)
