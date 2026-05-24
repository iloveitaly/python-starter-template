// should be imported *first* before any other application logic
import "./client"
import "./logging"
import withClerkProvider from "./clerk"
import withPostHogProvider from "./posthog"
import withSentryProvider from "./sentry"
import withTanstackQueryProvider from "./tanstack-query"

const PROVIDERS: ((app: React.ComponentType) => JSX.Element)[] = [
  withClerkProvider,
  withPostHogProvider,
  withSentryProvider,
  withTanstackQueryProvider,
]

// TODO(mbianco) figure out type issue here + move to config index
export function withProviders(app: () => React.ComponentType) {
  return PROVIDERS.reduce((acc, provider) => provider(acc), app)
}
