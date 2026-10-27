// should be imported *first* before any other application logic
import { createElement } from "react"

import withClerkProvider from "./clerk"
import "./client"
import "./logging"
import withPostHogProvider from "./posthog"
import withSentryProvider from "./sentry"
import withTanstackQueryProvider from "./tanstack-query"

// each provider wraps a component and returns the wrapped component
const PROVIDERS: ((app: React.ComponentType) => React.ComponentType)[] = [
  withClerkProvider,
  withPostHogProvider,
  withSentryProvider,
  withTanstackQueryProvider,
]

export function withProviders(app: React.ComponentType) {
  const WrappedApp = PROVIDERS.reduce((acc, provider) => provider(acc), app)

  // react router requires a route module's default export to be a function component
  return function WithProviders() {
    return createElement(WrappedApp)
  }
}
