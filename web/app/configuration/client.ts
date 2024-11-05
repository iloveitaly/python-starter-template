// the autogen'd client from the python's openapi.json is configured here
import { client } from "client/services.gen"
import { requireEnv } from "utils/environment"

client.setConfig({
  baseUrl: requireEnv("VITE_PYTHON_URL"),
})
