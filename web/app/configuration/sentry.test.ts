import { describe, expect, it } from "vitest"

import { SENTRY_IGNORE_ERRORS } from "./sentry"

function isIgnored(message: string) {
  return SENTRY_IGNORE_ERRORS.some((pattern) => pattern.test(message))
}

describe("SENTRY_IGNORE_ERRORS", () => {
  it("drops Stripe.js script-load failures (MOVIE-TICKET-FRONTEND-M3)", () => {
    expect(isIgnored("Failed to load Stripe.js")).toBe(true)
    expect(isIgnored("Error: Failed to load Stripe.js")).toBe(true)
  })

  it("drops module script import failures (MOVIE-TICKET-FRONTEND-2H)", () => {
    expect(isIgnored("Importing a module script failed.")).toBe(true)
    expect(isIgnored("TypeError: Importing a module script failed.")).toBe(
      true,
    )
  })

  it("does not drop first-party fetch failures that share common wording", () => {
    expect(isIgnored("Failed to fetch")).toBe(false)
    expect(isIgnored("Load failed")).toBe(false)
    expect(
      isIgnored("TypeError: Load failed (screening.triumphoftheheart.com)"),
    ).toBe(false)
  })
})
