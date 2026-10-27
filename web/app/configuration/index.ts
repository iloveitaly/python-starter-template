// should be imported *first* before any other application logic
import withClerkProvider from "./clerk"
import "./client"
import "./logging"
import withPostHogProvider from "./posthog"
import withSentryProvider from "./sentry"
import withTanstackQueryProvider from "./tanstack-query"

export function withProviders<Props extends object>(
  app: React.FunctionComponent<Props>,
): React.FunctionComponent<Props> {
  const withClerk = withClerkProvider(app)
  const withPostHog = withPostHogProvider(withClerk)
  const withSentry = withSentryProvider(withPostHog)

  return withTanstackQueryProvider(withSentry)
}
