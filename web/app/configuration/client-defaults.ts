// loaded by the generated client via runtimeConfigPath in web/openapi-ts.config.ts
import { isDevelopment, requireEnv } from "~/utils/environment"

import * as Sentry from "@sentry/react"
import { getClient } from "./clerk"
import { invariant } from "@epic-web/invariant"
import type { Config } from "client/client"

export const API_CLIENT_BASE_URL = requireEnv("VITE_PYTHON_URL")

// without this, you'll get a CORS error. Easy for this to happen during development.
if (
  !API_CLIENT_BASE_URL.startsWith("http://") &&
  !API_CLIENT_BASE_URL.startsWith("https://") &&
  API_CLIENT_BASE_URL != "/"
) {
  throw new Error("VITE_PYTHON_URL must start with http:// or https://")
}

// initialize the generated client with application defaults
export function createClientConfig(config?: Config): Config {
  // TODO I don't know if the auth function will be rerun multiple times...
  return {
    ...config,
    // TODO we want to have better support for ngrok in the future, which means we need to support two distinct domains
    //      maybe we can dynamically determine which to use
    baseUrl: API_CLIENT_BASE_URL,
    // same-origin is default, this is required in development since different API & FE server domains are used
    // https://github.com/hey-api/openapi-ts/issues/769#issuecomment-2222735798
    credentials: isDevelopment() ? "include" : "same-origin",
    // automatically set bearer auth when requested
    auth: async () => {
      const client = await getClient()
      invariant(
        client && client.session && client.user,
        "Clerk client, session, and user should exist when attempting an authenticated API call",
      )

      const token = await client.session.getToken()
      invariant(token, "token should exist if a session exists")

      // at this point, some sort of authenticated route is being called, so there is user information
      // it is possible for other actions to occur before this, but they should be inconsequential and
      // it would be challenging to inject `getClient` at just the right point, this is a natural place
      // to set the user context. However, this is not a perfect solution, as it uses the frontend user
      // authentication which can be different in the case of an admin who is logged in as a particular user.
      Sentry.setUser({ id: client.user.id })

      return token
    },
  }
}
