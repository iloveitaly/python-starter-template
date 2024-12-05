/*
Weird import structure is in place because of the following error. Most likely it's a RR7 issue that will be resolved:

- https://github.com/PostHog/posthog-js/pull/1293
- https://github.com/PostHog/posthog.com/pull/9830

---

x Build failed in 457ms
[react-router] Named export 'PostHogProvider' not found. The requested module 'posthog-js/react/dist/esm/index.js' is a CommonJS module, which may not support all module.exports as named exports.
CommonJS modules can always be imported via the default export, for example using:

import pkg from 'posthog-js/react/dist/esm/index.js';
const { PostHogProvider } = pkg;

file:///Users/mike/Projects/python/python-starter-template/web/build/server/index.js:20
import { PostHogProvider } from "posthog-js/react/dist/esm/index.js";
         ^^^^^^^^^^^^^^^
SyntaxError: Named export 'PostHogProvider' not found. The requested module 'posthog-js/react/dist/esm/index.js' is a CommonJS module, which may not support all module.exports as named exports.
CommonJS modules can always be imported via the default export, for example using:

import pkg from 'posthog-js/react/dist/esm/index.js';
const { PostHogProvider } = pkg;
*/
import { posthog } from "posthog-js"
import pkg from "posthog-js/react/dist/umd/index.js"

import { isProduction, requireEnv } from "~/utils/environment"

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
