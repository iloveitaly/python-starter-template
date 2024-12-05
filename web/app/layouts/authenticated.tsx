import { Outlet } from "react-router"

import { RedirectToSignIn, SignedIn, SignedOut } from "@clerk/clerk-react"

export default function AuthenticatedLayout() {
    // https://clerk.com/docs/components/control/redirect-to-signin
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
