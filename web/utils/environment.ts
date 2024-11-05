import { log } from "~/configuration/logging"

import { invariant } from "@epic-web/invariant"

export function isDevelopment() {
  return process.env.NODE_ENV?.toLowerCase() === "development"
}

export function isProduction() {
  return process.env.NODE_ENV?.toLowerCase() === "production"
}

export function isTest() {
  return process.env.NODE_ENV?.toLowerCase() === "test"
}

// TODO(mbianco) can we get the type assertion to flow out?
export function requireEnv(name: string) {
  const value = import.meta.env[name]
  invariant(value, `Missing environment variable: ${name}`)
  return value
}

log.debug("environment status", {
  env: process.env.NODE_ENV,
})
