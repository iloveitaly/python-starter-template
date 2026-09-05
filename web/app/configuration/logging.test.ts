import { LogLevel } from "tslog"
import { afterEach, describe, expect, it } from "vitest"

import { isDebugEnabled, log } from "./logging"

describe("logging", () => {
  const originalMinLevel = log.settings.minLevel

  afterEach(() => {
    log.setMinLevel(originalMinLevel)
  })

  it("uses tslog LogLevel values for the default min level", () => {
    expect(originalMinLevel).toBe(LogLevel.INFO)
    expect(isDebugEnabled()).toBe(false)
  })

  it("enables debug when minLevel is DEBUG or below", () => {
    log.setMinLevel(LogLevel.DEBUG)
    expect(isDebugEnabled()).toBe(true)

    log.setMinLevel(LogLevel.TRACE)
    expect(isDebugEnabled()).toBe(true)

    log.setMinLevel(LogLevel.WARN)
    expect(isDebugEnabled()).toBe(false)
  })

  it("accepts level names through tslog instead of a local map", () => {
    log.setMinLevel("DEBUG")
    expect(log.settings.minLevel).toBe(LogLevel.DEBUG)
    expect(isDebugEnabled()).toBe(true)
  })

  it("keeps the pretty template on the v5 settings group", () => {
    expect(log.settings.pretty.template).toBe(
      "[{{hh}}:{{MM}}:{{ss}}] {{logLevelName}}: ",
    )
  })
})
