import { Component } from "react"

import { isDevelopment } from "~/utils/environment"

import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { ReactQueryDevtools } from "@tanstack/react-query-devtools"

// client must be set globally to avoid this error
// https://stackoverflow.com/questions/65590195/error-no-queryclient-set-use-queryclientprovider-to-set-one
const queryClient = new QueryClient()

export default function withTanstackQueryProvider(
  Component: React.ComponentType,
) {
  return (props: React.ComponentProps<typeof Component>) => (
    <QueryClientProvider client={queryClient}>
      <Component {...props} />
      {isDevelopment() && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  )
}
