import { defineConfig } from "@hey-api/openapi-ts"

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
    path: "client",
    // TODO https://github.com/ferdikoomen/openapi-typescript-codegen/issues/1252#issuecomment-2593462128
    // converts all openapi snake case attributes to camelCase, but does not translate the api request
    // case: "camelCase",
    postProcess: ["prettier"],
  },
  plugins: [
    {
      name: "@hey-api/client-fetch",
      runtimeConfigPath: "./app/configuration/client-defaults",
    },
    "@hey-api/sdk",
    // https://github.com/hey-api/openapi-ts/issues/1571
    {
      name: "@hey-api/typescript",
      definitions: {
        case: "preserve",
      },
    },
    {
      name: "@tanstack/react-query",
      useQuery: true,
      useMutation: true,
      getQueryData: true,
      setQueryData: true,
      mutationKeys: true,
    },
    {
      name: "zod",
      types: {
        input: true,
        output: true,
      },
    },
  ],
})
