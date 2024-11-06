// should be imported *first* before any other application logic
import * as _client from "./client"
import * as _logging from "./logging"
import withChakraProvider from "./chakra"
import withClerkProvider from "./clerk"
import withPostHogProvider from "./posthog"
import withSentryProvider from "./sentry"

const PROVIDERS: ((app: React.ComponentType) => JSX.Element)[] = [
  withChakraProvider,
  withPostHogProvider,
  // withClerkProvider,
  withSentryProvider,
]

// TODO(mbianco) figure out type issue here + move to config index
export function withProviders(app: () => React.ComponentType) {
  return PROVIDERS.reduce((acc, provider) => provider(acc), app)
}
