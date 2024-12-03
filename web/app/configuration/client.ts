// the autogen'd client from the python's openapi.json is configured here
import { requireEnv } from "~/utils/environment"

import { Clerk } from "@clerk/clerk-js"
import { client } from "client/sdk.gen"

// goal here is to avoid having any application code rely on this directly
// so we only have a single file to change if the API changes on us
export * from "client/sdk.gen"

client.setConfig({
  baseUrl: requireEnv("VITE_PYTHON_URL"),
})

export async function setToken(clerkClient: Clerk) {
  const bearerToken = await clerkClient.session?.getToken()

  client.setConfig({
    baseUrl: requireEnv("VITE_PYTHON_URL"),
    headers: {
      Authorization: `Bearer ${bearerToken}`,
    },
  })

  //   client.interceptors.request.use((request, options) => {
  //     request.headers.set("Authorization", `Bearer ${bearerToken}`)
  //     return request
  //   })
}
