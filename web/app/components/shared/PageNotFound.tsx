function PageNotFoundIcon() {
  return (
    <svg
      className="mx-auto h-16 w-16 text-blue-500"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
      />
    </svg>
  )
}

export default function PageNotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-blue-50 to-blue-100 px-4">
      <div className="text-center">
        <h1 className="text-9xl font-bold text-blue-600">404</h1>
        <div className="mt-4 animate-bounce">
          <PageNotFoundIcon />
        </div>
        <h2 className="mt-6 text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl">
          Page not found
        </h2>
        <p className="mt-4 text-lg text-gray-600">
          Sorry, we couldn't find the page you're looking for.
        </p>
      </div>
    </div>
  )
}
