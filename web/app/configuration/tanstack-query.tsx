import { Component } from "react"

import { isDevelopment } from "~/utils/environment"

import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { ReactQueryDevtools } from "@tanstack/react-query-devtools"

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
