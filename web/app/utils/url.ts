/**
 * A type-safe absolute URL builder for react-router.
 */
import { href } from "react-router"

import { requireEnv } from "./environment"

const BASE_URL = requireEnv("VITE_APP_BASE_URL")

export function absHref(...args: Parameters<typeof href>): string {
  return new URL(href(...args), BASE_URL).href
}
