import {
  environmentName,
  isDevelopment,
  isProduction,
  isTesting,
  requireEnv,
} from "~/utils/environment"

import * as Sentry from "@sentry/react"

// TODO fix up react router when rr7 is supported https://docs.sentry.io/platforms/javascript/guides/react/features/react-router/

if (isProduction()) {
  Sentry.init({
    dsn: requireEnv("VITE_SENTRY_DSN"),

    // Adds request headers and IP for users, for more info visit:
    // https://docs.sentry.io/platforms/javascript/guides/react-router/configuration/options/#sendDefaultPii
    sendDefaultPii: true,

    environment: environmentName(),
    // TODO this may not be needed if we integrate sentry release, unsure
    release: requireEnv("VITE_BUILD_COMMIT"),

    integrations: [
      Sentry.browserTracingIntegration(),
      // TODO(mbianco) we should add react-router 7 integration when it's available
      // Replay is only available in the client
      Sentry.replayIntegration(),
      Sentry.feedbackIntegration({
        colorScheme: "system",
        showBranding: false,
      }),
    ],

    // assume `contains` on all string entries
    denyUrls: ["youtube.com"],

    // 1.0 to capture 100% of transactions for performance monitoring.
    tracesSampleRate: 0.05,

    // TODO(mbianco) pull domain from ENV
    // TODO(mbianco) should pull localias as well
    // Set `tracePropagationTargets` to control for which URLs distributed tracing should be enabled
    // tracePropagationTargets: ["localhost", /^https:\/\/yourserver\.io\/api/],

    // Capture Replay for 5% of all sessions,
    // plus for 100% of sessions with an error
    replaysSessionSampleRate: 0.05,
    replaysOnErrorSampleRate: 1.0,
  })
}

export default function withSentryProvider(Component: React.ComponentType) {
  // if this is enabled in testing, it impacts the resulting debugging output provided
  // https://discord.com/channels/621778831602221064/1307425055667519578
  // TODO should add env var for testing the sentry error reporting experience
  if (isDevelopment() || isTesting()) {
    return Component
  }

  return Sentry.withErrorBoundary(Component, {
    // TODO implement custom fallback for a nicer experience
    showDialog: true,
  })
}
