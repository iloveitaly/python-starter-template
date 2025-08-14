/**
 * This file cannot use the logger on initialization (which is console.debug is used here) to avoid pulling environment
 * variables on execution. This is because environment detection is used within vite, which does not run in the same
 * environment as the rest of the application.
 *
 * TODO we should consider duplicating the environment code in the vite setup instead of worrying about this here
 */
import { invariant } from "@epic-web/invariant"

export function environmentName() {
  return import.meta.env.MODE.toLowerCase()
}

export function isDevelopment() {
  return environmentName() === "development"
}

export function isProduction() {
  return environmentName() === "production"
}

export function isStaging() {
  return environmentName() === "staging"
}

export function isTesting() {
  return environmentName() === "test"
}

// TODO(mbianco) can we get the type assertion to flow out?
// https://vite.dev/guide/env-and-mode
// NOTE must use 'within' react, otherwise you'll get this error:
// > [module runner] Dynamic access of "import.meta.env" is not supported. Please, use "import.meta.env.MODE" instead.
export function requireEnv(name: string) {
  if (!name.startsWith("VITE_")) {
    console.warn("environment variable name does not start with VITE_", {
      name,
    })
  }

  const value = import.meta.env[name]
  invariant(
    value,
    `Missing environment variable: ${name}. Does it start with VITE_?`,
  )
  return value
}

console.debug("environment status", {
  env: environmentName(),
})
