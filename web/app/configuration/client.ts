// the autogen'd client from the python's openapi.json is configured here
import posthog from "posthog-js"

import { isDevelopment, requireEnv } from "~/utils/environment"

import * as Sentry from "@sentry/react"
import { getClient } from "./clerk"
import { invariant } from "@epic-web/invariant"
import { createClient } from "client/client"
import { client } from "client/client.gen"

// goal here is to avoid having any application code rely on this directly
// so we only have a single file to change if the API changes on us
export * from "client/sdk.gen"
export type * from "client/types.gen"
export * from "client/@tanstack/react-query.gen"
export * from "client/zod.gen"

const VITE_PYTHON_URL = requireEnv("VITE_PYTHON_URL")

// without this, you'll get a CORS error. Easy for this to happen during development.
if (
  !VITE_PYTHON_URL.startsWith("http://") &&
  !VITE_PYTHON_URL.startsWith("https://") &&
  VITE_PYTHON_URL != "/"
) {
  throw new Error("VITE_PYTHON_URL must start with http:// or https://")
}

// TODO I don't know if the auth function will be rerun multiple times...
client.setConfig({
  // TODO we want to have better support for ngrok in the future, which means we need to support two distinct domains
  //      maybe we can dynamically determine which to use
  baseUrl: VITE_PYTHON_URL,
  // same-origin is default, this is required in development since different API & FE server domains are used
  // https://github.com/hey-api/openapi-ts/issues/769#issuecomment-2222735798
  credentials: isDevelopment() ? "include" : "same-origin",
  // automatically set bearer auth when requested
  auth: async () => {
    const client = await getClient()
    invariant(client && client.session, "Clerk client and session should exist")

    const token = await client.session.getToken()
    invariant(token, "token should exist")

    // at this point, some sort of authenticated route is being called, so there is user information
    // it is possible for other actions to occur before this, but they should be inconsequential and
    // it would be challenging to inject `getClient` at just the right point, this is a natural place
    // to set the user context. However, this is not a perfect solution, as it uses the frontend user
    // authentication which can be different in the case of an admin who is logged in as a particular user.
    Sentry.setUser({ id: client.user.id })

    return token
  },
})

/**
 * Public client for use in public routes
 *
 * Usage: `await endpointName({ client: publicClient })`
 */
export const publicClient = createClient({
  baseUrl: VITE_PYTHON_URL,

  // explicitly excluding any authentication configuration
})

// this loader checks the response codes and throws specific type of errors that will render different error pages
// this should be used in any clientLoaders
export const publicClientLoader = createClient({
  baseUrl: VITE_PYTHON_URL,
  // explicitly exclude any authentication configuration
})

/**
 * Raise an exception on HTTP error code.
 *
 * Helpful when running a API request within a `clientLoader` that is expected to succeed, and if it doesn't, you want
 * to render an error page. This enables you to avoid adding try/catch a million times and instead define a global
 * error boundary for your route.
 *
 * https://heyapi.dev/openapi-ts/clients/fetch#interceptors
 * https://github.com/sparkplug/momoapi-node/blob/a547cac2fd4ad52e06e56b9b318714498d6aa80c/src/client.ts#L40
 *
 * TODO need to understand if it's better to map `error`
 */
publicClientLoader.interceptors.response.use((response) => {
  if (response.status === 404) {
    throw new Response("Not Found", { status: 404 })
  } else if (response.status >= 400 && response.status < 500) {
    throw new Response("Client Error", { status: response.status })
  } else if (response.status >= 500) {
    throw new Response("Server Error", { status: response.status })
  }

  return response
})

/**
 * Add the posthog distinct and session IDs to the request headers.
 *
 * This is helpful for linking frontend events to backend events. This could fail
 * if adblockers are in place or if these are used before `init` is called.
 */
function addPosthogHeaders(request: Request): Request {
  const newHeaders = new Headers(request.headers)

  const distinctId = posthog.get_distinct_id()
  if (distinctId) {
    newHeaders.set("X-Posthog-Distinct-Id", distinctId)
  }

  const sessionId = posthog.get_session_id()
  if (sessionId) {
    newHeaders.set("X-Posthog-Session-Id", sessionId)
  }

  return new Request(request, { headers: newHeaders })
}
publicClientLoader.interceptors.request.use(addPosthogHeaders)
publicClient.interceptors.request.use(addPosthogHeaders)
client.interceptors.request.use(addPosthogHeaders)

// TODO implement dynamic base URL interceptor for development, helpful for ngrok and friends
// function dynamicBaseInterceptor(request: Request): Request {
//   const origin = window.location.origin;
//   const newBase = origin === 'https://example.com' ? 'https://api.example.com' : 'https://staging.api.example.com';
//   const newUrl = request.url.replace(OpenAPI.BASE, newBase);
//   return new Request(newUrl, request);
// }

// OpenAPI.interceptors.request.use(dynamicBaseInterceptor);
