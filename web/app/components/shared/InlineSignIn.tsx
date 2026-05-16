/**
 * For layouts that assume the user is authenticated, drop this in and avoid a redirect to login. *
 */
import { SignIn } from "@clerk/react"

function InlineSignIn() {
  return (
    <div className="relative min-h-screen">
      {/* Background Image with Gradient Overlay */}
      <div className="absolute inset-0 bg-cover bg-center">
        <div className="absolute inset-0 bg-gradient-to-t from-black via-black/40 to-transparent" />
      </div>

      {/* Content */}
      <div className="relative flex min-h-screen justify-center pt-20">
        <div>
          <SignIn
            appearance={{
              elements: {
                formButtonPrimary: "bg-blue-600 hover:bg-blue-700",
                card: "shadow-xl",
                headerTitle: "Welcome to Our App",
                headerSubtitle: "Sign in to access your account.",
              },
            }}
          />
        </div>
      </div>
    </div>
  )
}
