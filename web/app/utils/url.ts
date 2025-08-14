/**
 * A type-safe absolute URL builder for react-router.
 */
import { href } from "react-router"

import { requireEnv } from "./environment"
import { invariant } from "@epic-web/invariant"

// TODO in this application, we really need to acquire the base URL dynamically...
const BASE_URL = requireEnv("VITE_APP_BASE_URL")

invariant(
  BASE_URL &&
    (BASE_URL.startsWith("http") || BASE_URL.startsWith("https")) &&
    BASE_URL.endsWith("/"),
  "VITE_APP_BASE_URL must be a valid URL starting with http(s)://",
)

export function absHref(...args: Parameters<typeof href>): string {
  return new URL(href(...args), BASE_URL).href
}
