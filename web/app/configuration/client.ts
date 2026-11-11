// the autogen'd client from the python's openapi.json is configured here
import posthog from "posthog-js"

import { API_CLIENT_BASE_URL } from "./client-defaults"
import { createClient } from "client/client"
import { client } from "client/client.gen"

// goal here is to avoid having any application code rely on this directly
// so we only have a single file to change if the API changes on us
export * from "client/sdk.gen"
export type * from "client/types.gen"
export * from "client/@tanstack/react-query.gen"
export * from "client/zod.gen"

/**
 * API client for use in public (unauthenticated) routes.
 *
 * Designed for use *outside* of a clientLoader (within a component's body), since it does not throw on HTTP errors.
 *
 * Usage: `await generatedEndpointName({ client: publicClient })`
 */
export const publicClient = createClient({
  baseUrl: API_CLIENT_BASE_URL,

  // explicitly excluding any authentication configuration
})

/**
 * API client for use in authenticated routes within a clientLoader
 *
 * this loader checks the response codes and throws specific type of errors that will render different error pages.
 * this should be used in any clientLoaders
 *
 * Usage: `await generatedEndpointName({ client: publicClientLoader })`
 */
export const publicClientLoader = createClient({
  baseUrl: API_CLIENT_BASE_URL,
  // otherwise interceptor errors are returned instead of reaching loader error handlers
  throwOnError: true,

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
