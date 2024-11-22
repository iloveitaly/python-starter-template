// the autogen'd client from the python's openapi.json is configured here
import { client } from "client/sdk.gen"
import { requireEnv } from "utils/environment"

// goal here is to avoid having any application code rely on this directly
// so we only have a single file to change if the API changes on us
export * from "client/sdk.gen"

client.setConfig({
  baseUrl: requireEnv("VITE_PYTHON_URL"),
})
