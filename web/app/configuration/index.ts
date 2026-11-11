// should be imported *first* before any other application logic
import withClerkProvider from "./clerk"
import "./client"
import "./logging"
import withPostHogProvider from "./posthog"
import withSentryProvider from "./sentry"
import withTanstackQueryProvider from "./tanstack-query"

// each provider wraps a component and returns the wrapped component
const PROVIDERS = [
  withClerkProvider,
  withPostHogProvider,
  withSentryProvider,
  withTanstackQueryProvider,
]

// react router requires a route module's default export to be a function component, so class components can't be accepted here
export function withProviders<Props extends object>(
  Component: React.FC<Props>,
) {
  return PROVIDERS.reduce((acc, provider) => provider(acc), Component)
}
