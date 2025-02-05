// the autogen'd client from the python's openapi.json is configured here
import { requireEnv } from "~/utils/environment"

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
  // automatically set bearer auth when requested
  auth: async () => {
    const client = await getClient()
    invariant(client && client.session, "client and session should exist")

    const token = await client.session.getToken()
    invariant(token, "token should exist")

    return token
  },
})
