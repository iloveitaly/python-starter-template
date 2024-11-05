import { posthog } from "posthog-js"
import pkg from "posthog-js/react/dist/umd/index.js"

import { isProduction, requireEnv } from "utils/environment"

const { PostHogProvider } = pkg

if (isProduction()) {
  posthog.init(requireEnv("VITE_POSTHOG_KEY"), {
    api_host: requireEnv("VITE_POSTHOG_HOST"),
    person_profiles: "identified_only",

    // required for react-router
    capture_pageview: false,
  })
}

export default function withPostHogProvider(Component: React.ComponentType) {
  return function WithPostHogProviderWrapper(props: any) {
    return (
      <PostHogProvider client={posthog}>
        <Component {...props} />
      </PostHogProvider>
    )
  }
}
