import { Link, Navigate } from "react-router"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  ClerkProvider,
  RedirectToSignIn,
  SignIn,
  SignInButton,
  SignOutButton,
  SignUpButton,
  SignedIn,
  SignedOut,
  UserButton,
} from "@clerk/clerk-react"

export default function Index() {
  return (
    <div className="flex h-screen w-full items-center justify-center px-4">
      <SignedIn>
        <Navigate to="/home" />
        {/* <Link to="/home">Hi</Link> */}
        <p>You are signed in!</p>
        <div>
          <p>View your profile here</p>
          <UserButton />
        </div>
        <div>
          <SignOutButton />
        </div>
      </SignedIn>
      <SignedOut>
        <SignIn />
      </SignedOut>
    </div>
  )
}
