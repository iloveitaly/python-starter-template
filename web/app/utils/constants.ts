/**
 * Project-specific constants.
 */
import { requireEnv } from "~/utils/environment"

import { invariant } from "@epic-web/invariant"

// TODO we should figure out an option to acquire the base url dynamically from the request using a middleware
export const BASE_URL = requireEnv("VITE_APP_BASE_URL")

invariant(
  BASE_URL && BASE_URL.startsWith("http") && BASE_URL.endsWith("/"),
  "VITE_APP_BASE_URL must be a valid URL starting with http(s)://",
)

// Define the constant, checking for window availability
export const IN_IFRAME =
  typeof window !== "undefined"
    ? (() => {
        try {
          return window !== window.top
        } catch (_e) {
          return true // Assume iframe if access is restricted
        }
      })()
    : false // Default to false on server

// 1p and others can improperly detect and autofill form fields, use `{...NO_AUTOFILL_PROPS}` to prevent this
export const NO_AUTOFILL_PROPS = {
  autoComplete: "off",
  "data-1p-ignore": true,
  "data-op-ignore": true,
  "data-bwignore": true,
  "data-lpignore": "true",
  "data-form-type": "other",
}
