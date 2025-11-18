// mainly just to demonstrate what an unauthenticated route could look like
export default function LoginPage() {
  return (
    <div className="flex items-center justify-center px-4">
      <div className="bg-card w-full max-w-md rounded-lg border p-6 shadow-sm">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold">Welcome Back</h1>
          <p className="text-muted-foreground text-sm">
            Sign in to your account to continue
          </p>
        </div>
        <div>
          <button className="bg-primary text-primary-foreground hover:bg-primary/90 w-full rounded-md px-4 py-2 text-lg">
            Sign In
          </button>
        </div>
      </div>
    </div>
  )
}
