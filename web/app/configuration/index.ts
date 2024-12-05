// should be imported *first* before any other application logic
import withClerkProvider from "./clerk"
import "./client"
import "./logging"
import withPostHogProvider from "./posthog"
import withSentryProvider from "./sentry"

const PROVIDERS: ((app: React.ComponentType) => JSX.Element)[] = [
    withPostHogProvider,
    withClerkProvider,
    withSentryProvider,
]

// TODO(mbianco) figure out type issue here + move to config index
export function withProviders(app: () => React.ComponentType) {
    return PROVIDERS.reduce((acc, provider) => provider(acc), app)
}
