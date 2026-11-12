/**
 * Utilities to build URLs in the frontend application
 */
import { href } from "react-router"

import { BASE_URL } from "./constants"

export function absHref<Path extends Parameters<typeof href>[0]>(
  ...[path, ...params]: Parameters<typeof href<Path>>
): string {
  return new URL(href<Path>(path, ...params), BASE_URL).href
}
