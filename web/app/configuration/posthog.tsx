/*
 * The posthog JS library is a mess. This latest iteration is the recommended solution and seems to work, but I would
 * expect issues with this library and don't assume it's well designed.
 *
 * - https://github.com/PostHog/posthog-js/pull/1293
 * - https://github.com/PostHog/posthog.com/pull/9830
 * - https://github.com/PostHog/posthog-js/issues/908
 */
import React from "react"
import { useEffect, useState } from "react"

import posthog from "posthog-js"
import { PostHogProvider } from "posthog-js/react"

import { isDevelopment, isTesting, requireEnv } from "~/utils/environment"

export function PHProvider({ children }: { children: React.ReactNode }) {
  const [hydrated, setHydrated] = useState(false)

  useEffect(() => {
    posthog.init(requireEnv("VITE_POSTHOG_KEY"), {
      api_host:
        import.meta.env["VITE_POSTHOG_HOST"] ?? "https://us.i.posthog.com",
      defaults: "2025-05-24",
      // or 'always' to create profiles for anonymous users as well
      person_profiles: "identified_only",
    })

    setHydrated(true)
  }, [])

  if (!hydrated) return <>{children}</>
  return <PostHogProvider client={posthog}>{children}</PostHogProvider>
}

export default function withPostHogProvider(Component: React.ComponentType) {
  if (isDevelopment() || isTesting()) {
    return Component
  }

  return function WithPostHogProviderWrapper(
    props: React.ComponentProps<typeof Component>,
  ) {
    return (
      <PHProvider>
        <Component {...props} />
      </PHProvider>
    )
  }
}
