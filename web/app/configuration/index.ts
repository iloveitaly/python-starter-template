// should be imported *first* before any other application logic
import withClerkProvider from "./clerk"
import "./client"
import "./logging"
import withPostHogProvider from "./posthog"
import withSentryProvider from "./sentry"
import withTanstackQueryProvider from "./tanstack-query"

const PROVIDERS = [
  withClerkProvider,
  withPostHogProvider,
  withSentryProvider,
  withTanstackQueryProvider,
]

export function withProviders<Props extends object>(
  Component: React.FC<Props>,
) {
  return PROVIDERS.reduce((acc, provider) => provider(acc), Component)
}
