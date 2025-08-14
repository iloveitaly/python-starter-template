/**
 * Utilities to build URLs in the frontend application
 */
import { href } from "react-router"

import { BASE_URL } from "./constants"

export function absHref(...args: Parameters<typeof href>): string {
  return new URL(href(...args), BASE_URL).href
}
