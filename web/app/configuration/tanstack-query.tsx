import { isDevelopment } from "~/utils/environment"

import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { ReactQueryDevtools } from "@tanstack/react-query-devtools"

declare global {
  interface Window {
    __queryClient?: QueryClient
  }
}

// client must be set globally to avoid this error
// https://stackoverflow.com/questions/65590195/error-no-queryclient-set-use-queryclientprovider-to-set-one
const queryClient = new QueryClient()

// expose queryClient for playwright readiness checks in wait_for_loading
if (typeof window !== "undefined") {
  window.__queryClient = queryClient
}

export default function withTanstackQueryProvider<Props extends object>(
  Component: React.ComponentType<Props>,
) {
  return (props: Props) => (
    <QueryClientProvider client={queryClient}>
      <Component {...props} />
      {isDevelopment() && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  )
}
