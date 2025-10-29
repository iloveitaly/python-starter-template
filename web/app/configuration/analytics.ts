/**
 * Analytics configuration settings.
 *
 * Most of the time, you should use Google Tag Manager to inject JavaScript into the application. For instance, if you are
 * looking to use a Facebook pixel, Google Ads pixel, or any sort of pixel that doesn't need any tie-in to particular front-end logic,
 * this should be done through Google Tag Manager.
 *
 * However, this doesn't work for everything. For instance:
 *
 * - Rewardful. If you rely on rewardful on `clientLoader` you need the `window.rewardful` object to exist before executing
 *   `clientLoader` code.
 * - Posthog. You'll probably want to more deeply integrate Posthog into your application. So you wouldn't want to use
 *   the analytics plugin here either.
 *
 */
import { Analytics } from "analytics"

import rewardfulPlugin from "~/lib/rewardful"
import { requireEnv } from "~/utils/environment"

import { isDebugEnabled } from "./logging"
// GTM isn't typed and won't be anytime soon
// https://github.com/DavidWells/analytics/issues/99#issuecomment-736153120
import googleTagManager from "@analytics/google-tag-manager"

// this is really important to run as early in the application setup as possible since it injects various scripts that
// other aspects of the application rely on. Specifically, many scripts which are loaded from external domains end up
// injecting an array into the window element to store references/events to fire when it has initialized properly.
//
// `analytics` is designed to be used via node as well, so we don't have to protect against browser-only code.
const analytics = Analytics({
  debug: isDebugEnabled(),
  plugins: [
    // https://github.com/DavidWells/analytics/blob/master/packages/analytics-plugin-google-tag-manager/README.md
    googleTagManager({
      containerId: requireEnv("VITE_GOOGLE_TAG_MANAGER"),
    }),
    rewardfulPlugin({
      apiKey: requireEnv("VITE_REWARDFUL_API_KEY"),
    }),
  ],
})

// we don't need to use hooks, we can simply import this object directly and use it throughout the application
// https://getanalytics.io/utils/react-hooks/#without-hooks
export default analytics
