import { Link } from "react-router"

import {
    SignIn,
    SignOutButton,
    SignedIn,
    SignedOut,
    UserButton,
} from "@clerk/clerk-react"

export default function Index() {
    return (
        <div className="flex h-screen w-full items-center justify-center px-4">
            <SignedIn>
                {/* <Navigate to="/home" /> https://discord.com/channels/856971667393609759/1311386772520960182 */}
                <p>
                    <Link to="/home">Go Home</Link>
                </p>
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
