import { useEffect } from "react"
import { Navigate, href } from "react-router"

import posthog from "posthog-js"

import { useClerk } from "~/configuration/clerk"

export default function LogoutRedirect() {
  const { signOut } = useClerk()

  useEffect(() => {
    posthog.reset()
    signOut({ redirectUrl: href("/login") })
  }, [signOut])

  return <Navigate to={href("/login")} />
}
