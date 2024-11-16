import * as Sentry from "@sentry/react"
import {
  environmentName,
  isDevelopment,
  isProduction,
  isTesting,
  requireEnv,
} from "utils/environment"

// TODO fix up react router when rr7 is supported https://docs.sentry.io/platforms/javascript/guides/react/features/react-router/

if (isProduction()) {
  Sentry.init({
    dsn: requireEnv("VITE_SENTRY_DSN"),

    environment: environmentName(),
    // TODO this may not be needed if we integrate sentry release, unsure
    release: requireEnv("VITE_BUILD_COMMIT"),

    integrations: [
      Sentry.browserTracingIntegration(),
      // TODO(mbianco) we should add react-router 7 integration when it's available
      // Replay is only available in the client
      Sentry.replayIntegration(),
    ],

    // Set tracesSampleRate to 1.0 to capture 100%
    // of transactions for performance monitoring.
    // We recommend adjusting this value in production
    tracesSampleRate: 1.0,

    // TODO(mbianco) pull domain from ENV
    // TODO(mbianco) should pull localias as well
    // Set `tracePropagationTargets` to control for which URLs distributed tracing should be enabled
    tracePropagationTargets: ["localhost", /^https:\/\/yourserver\.io\/api/],

    // Capture Replay for 10% of all sessions,
    // plus for 100% of sessions with an error
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,
  })
}

export default function withSentryProvider(Component: React.ComponentType) {
  // if this is enabled in testing, it impacts the resulting debugging output provided
  // https://discord.com/channels/621778831602221064/1307425055667519578
  if (isDevelopment() || isTesting()) {
    return Component
  }

  return Sentry.withErrorBoundary(Component, {
    // TODO implement custom fallback for a nicer experience
    showDialog: true,
  })
}
