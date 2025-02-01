import { defaultPlugins, defineConfig } from "@hey-api/openapi-ts"

const { OPENAPI_JSON_PATH, TEST_RESULTS_DIRECTORY: TMP_DIRECTORY } = process.env

if (!OPENAPI_JSON_PATH) {
  throw new Error("OPENAPI_JSON_PATH is not defined")
}

export default defineConfig({
  input: OPENAPI_JSON_PATH,
  logs: TMP_DIRECTORY
    ? {
        path: TMP_DIRECTORY,
      }
    : {},
  output: {
    format: "prettier",
    lint: "eslint",
    path: "client",
    // TODO https://github.com/ferdikoomen/openapi-typescript-codegen/issues/1252#issuecomment-2593462128
    // converts all openapi snake case attributes to camelCase, but does not translate the api request
    // case: "camelCase",
  },
  experimentalParser: true,
  plugins: [
    "@hey-api/client-fetch",
    ...defaultPlugins,
    // https://github.com/hey-api/openapi-ts/issues/1571
    {
      identifierCase: "preserve",
      name: "@hey-api/typescript",
    },
    "@tanstack/react-query",
  ],
})
