// the autogen'd client from the python's openapi.json is configured here
import { isDevelopment, requireEnv } from "~/utils/environment"

import * as Sentry from "@sentry/react"
import { getClient } from "./clerk"
import { invariant } from "@epic-web/invariant"
import { client } from "client/client.gen"

// goal here is to avoid having any application code rely on this directly
// so we only have a single file to change if the API changes on us
export * from "client/sdk.gen"
export type * from "client/types.gen"

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
  baseUrl: VITE_PYTHON_URL,
  // same-origin is default, this is required in development since different API & FE server domains are used
  // https://github.com/hey-api/openapi-ts/issues/769#issuecomment-2222735798
  credentials: isDevelopment() ? "include" : "same-origin",
  // automatically set bearer auth when requested
  auth: async () => {
    const client = await getClient()
    invariant(client && client.session, "client and session should exist")

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
