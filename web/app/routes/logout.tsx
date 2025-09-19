import { useEffect } from "react"
import { Navigate, href } from "react-router"

import { useClerk } from "@clerk/clerk-react"

export default function LogoutRedirect() {
  const { signOut } = useClerk()

  useEffect(() => {
    signOut({ redirectUrl: href("/login") })
  }, [signOut])

  return <Navigate to={href("/login")} />
}
