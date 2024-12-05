import { log } from "~/configuration/logging"

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
export function requireEnv(name: string) {
    if (!name.startsWith("VITE_")) {
        log.warn("environment variable name does not start with VITE_", {
            name,
        })
    }

    const value = import.meta.env[name]
    invariant(value, `Missing environment variable: ${name}`)
    return value
}

log.debug("environment status", {
    env: environmentName(),
})
