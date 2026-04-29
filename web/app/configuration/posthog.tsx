/*
 * The posthog JS library is a mess. This latest iteration is the recommended solution and seems to work, but I would
 * expect issues with this library and don't assume it's well designed.
 *
 * - https://github.com/PostHog/posthog-js/pull/1293
 * - https://github.com/PostHog/posthog.com/pull/9830
 * - https://github.com/PostHog/posthog-js/issues/908
 * - https://github.com/PostHog/posthog-js/tree/main/packages/browser/playground/react-router
 */
import React from "react"

import posthog from "posthog-js"

import { isProduction, requireEnv } from "~/utils/environment"

import { isDebugEnabled } from "./logging"
import { PostHogProvider } from "@posthog/react"

const POSTHOG_KEY = requireEnv("VITE_POSTHOG_KEY")

// since this is a SPA that *could* be server side rendered, and posthog is browser-only, we need to browser check here
// https://posthog.com/tutorials/single-page-app-pageviews
// it's important that this is run first since clientLoader assumes posthog is initialized (for distinct ID and session IDs)
if (typeof window !== "undefined") {
  posthog.init(POSTHOG_KEY, {
    api_host:
      import.meta.env["VITE_POSTHOG_HOST"] ?? "https://us.i.posthog.com",
    defaults: "2026-01-30",
    debug: isDebugEnabled(),
    // or 'always' to create profiles for anonymous users as well
    person_profiles: "identified_only",
    // this controls both autocapture of exceptions *and* clicks
    // you can disable exception autocapture in your settings
    autocapture: true,
    // by default, posthog will *not* capture all query string params
    custom_campaign_params: [
      // Rewardful referral code params
      "via",
      // TODO pretty sure this was just a generic param I added that we should probably remove
      "referral",
    ],
    // copied from the react router example, unsure if these are the best settings
    capture_pageview: "history_change",
    capture_pageleave: true,
    // https://posthog.com/tutorials/multiple-environments#opt-out-of-capturing-on-initialization
    loaded: function (ph) {
      if (!isProduction()) {
        ph.opt_out_capturing()
        ph.set_config({ disable_session_recording: true })
      }
    },
  })
}

export default function withPostHogProvider(Component: React.ComponentType) {
  // we intentionally do NOT disable this functionality in specific environments
  // instead, we just disable capturing and session recording in non-production environments. This allows us to test that the provider is working and that events are being sent without polluting our production data with test events.
  return function WithPostHogProviderWrapper(
    props: React.ComponentProps<typeof Component>,
  ) {
    return (
      <PostHogProvider client={posthog}>
        <Component {...props} />
      </PostHogProvider>
    )
  }
}
