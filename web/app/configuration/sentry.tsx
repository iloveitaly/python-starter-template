import * as Sentry from "@sentry/react"
import { invariant } from "@epic-web/invariant"
import { isProduction } from "utils/environment"

if (isProduction()) {
  const SENTRY_DSN = import.meta.env.VITE_SENTRY_DSN
  invariant(SENTRY_DSN, "Missing Sentry Key")

  Sentry.init({
    dsn: SENTRY_DSN,
    integrations: [
      // TODO(mbianco) we should add react-router 7 integration when it's available
      // Replay is only available in the client
      Sentry.replayIntegration(),
    ],

    // Set tracesSampleRate to 1.0 to capture 100%
    // of transactions for performance monitoring.
    // We recommend adjusting this value in production
    tracesSampleRate: 1.0,

    // TODO(mbianco) pull domain from ENV
    // Set `tracePropagationTargets` to control for which URLs distributed tracing should be enabled
    tracePropagationTargets: ["localhost", /^https:\/\/yourserver\.io\/api/],

    // Capture Replay for 10% of all sessions,
    // plus for 100% of sessions with an error
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,
  })
}

export default function withSentryProvider(Component: React.ComponentType) {
  return (props: React.ComponentProps<typeof Component>) => (
    <Sentry.ErrorBoundary>
      <Component {...props} />
    </Sentry.ErrorBoundary>
  )
}
