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

  it("includes file and line on pretty logs outside production", () => {
    expect(log.settings.pretty.template).toContain("{{filePathWithLine}}")
    expect(log.settings.pretty.errorStackTemplate).toContain(
      "{{filePathWithLine}}",
    )
  })

  it("routes warn and error through the matching console methods", () => {
    expect(log.settings.pretty.levelMethod.WARN).toBeTypeOf("function")
    expect(log.settings.pretty.levelMethod.ERROR).toBeTypeOf("function")
    expect(log.settings.pretty.levelMethod.FATAL).toBeTypeOf("function")
  })

  it("masks common secret keys", () => {
    expect(log.settings.mask.keys).toEqual(
      expect.arrayContaining(["password", "token", "secret", "apiKey"]),
    )
    expect(log.settings.mask.caseInsensitive).toBe(true)
  })
})
