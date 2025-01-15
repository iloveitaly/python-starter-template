import { defaultPlugins, defineConfig } from "@hey-api/openapi-ts"

const { OPENAPI_JSON_PATH, TEST_RESULTS_DIRECTORY } = process.env

if (!OPENAPI_JSON_PATH) {
  throw new Error("OPENAPI_JSON_PATH is not defined")
}

if (!TEST_RESULTS_DIRECTORY) {
  throw new Error("TEST_RESULTS_DIRECTORY is not defined")
}

// originally lifted from: https://github.com/sagardwivedi/YumBook/blob/7ec69b9ce51dfb20826f80a2769ff6bc056e72e1/frontend/openapi-ts.config.ts#L9
export default defineConfig({
  input: OPENAPI_JSON_PATH,
  logs: {
    path: TEST_RESULTS_DIRECTORY,
  },
  output: {
    // TODO determine where these magic config options are defined...
    // lint: "biome",
    // format: "biome",
    path: "client",
    // TODO https://github.com/ferdikoomen/openapi-typescript-codegen/issues/1252#issuecomment-2593462128
    // converts all openapi snake case attributes to camelCase, but does not translate the api request
    // case: "camelCase",
  },
  client: "@hey-api/client-fetch",
  experimentalParser: true,
  plugins: [...defaultPlugins],
})
