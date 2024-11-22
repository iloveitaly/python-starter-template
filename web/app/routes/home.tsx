// TODO why do I need ../? I couldn't get .react-router to play well
// import * as Route from "/.react-router/types/app/+types.root"
import { type MetaFunction } from "react-router"

import { getClient } from "~/configuration/clerk"
import { readRootInternalV1Get } from "~/configuration/client"

import type { Route } from "./+types.home"

export const meta: MetaFunction = () => {
  return [
    { title: "Starter Application Template" },
    { name: "description", content: "Welcome to Starter Application Template" },
  ]
}

export async function clientLoader(_loader_args: Route.ClientLoaderArgs) {
  // TODO what's terrible about this is I believe the ClerkProvider will hit the clerk API yet again
  // https://discord.com/channels/856971667393609759/1306770317624086649
  const clerkClient = await getClient()

  // only goal here is protecting this page from hitting the internal API
  if (!clerkClient.user) {
    await clerkClient.redirectToSignIn()
    return
  }

  // this route is authenticated
  const { data } = await readRootInternalV1Get()

  // TODO need idiomatic error handling here
  if (data === undefined) {
    throw new Error("Failed to load data")
  }

  return data
}

export default function Home({ loaderData }: Route.ComponentProps) {
  return (
    <div className="flex h-screen items-center justify-center">
      <div className="flex flex-col items-center gap-16">
        <header className="flex flex-col items-center gap-9">
          <h1 className="leading text-2xl font-bold text-gray-800 dark:text-gray-100">
            {loaderData && loaderData.message}
            <span className="sr-only">React Router</span>
          </h1>
          <div className="w-[500px] max-w-[100vw] p-4">
            <img
              src="/logo-light.svg"
              alt="React Router"
              className="block w-full dark:hidden"
            />
            <img
              src="/logo-dark.svg"
              alt="React Router"
              className="hidden w-full dark:block"
            />
          </div>
        </header>
      </div>
    </div>
  )
}
