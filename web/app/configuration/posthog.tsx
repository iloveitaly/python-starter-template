/*
Weird import structure is in place because of the following error. Most likely it's a RR7 issue that will be resolved:

- https://github.com/PostHog/posthog-js/pull/1293
- https://github.com/PostHog/posthog.com/pull/9830
- https://github.com/PostHog/posthog-js/issues/908

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
import React, { createContext, useContext, useRef } from "react"

import { posthog } from "posthog-js"

import { isDevelopment, isTesting, requireEnv } from "~/utils/environment"

type PosthogType = typeof posthog | undefined

const PosthogContext = createContext<PosthogType>(undefined)

interface PosthogProviderProps {
  children: React.ReactNode
}

export function PostHogProvider({ children }: PosthogProviderProps) {
  const posthogInstanceRef = useRef<PosthogType>(undefined)

  // https://react.dev/reference/react/useRef#avoiding-recreating-the-ref-contents
  // Note that in StrictMode, this will run twice.
  function getPosthogInstance() {
    if (posthogInstanceRef.current) return posthogInstanceRef.current

    posthogInstanceRef.current = posthog.init(requireEnv("VITE_POSTHOG_KEY"), {
      api_host: requireEnv("VITE_POSTHOG_HOST"),
      person_profiles: "identified_only",

      // required for react-router
      capture_pageview: false,
    })

    return posthogInstanceRef.current
  }

  return (
    <PosthogContext.Provider value={getPosthogInstance()}>
      {children}
    </PosthogContext.Provider>
  )
}

export const usePosthog = () => useContext(PosthogContext)

export default function withPostHogProvider(Component: React.ComponentType) {
  if (isDevelopment() || isTesting()) {
    return Component
  }

  return function WithPostHogProviderWrapper(
    props: React.ComponentProps<typeof Component>,
  ) {
    return (
      <PostHogProvider>
        <Component {...props} />
      </PostHogProvider>
    )
  }
}
