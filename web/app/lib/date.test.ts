import timezoneMock from "timezone-mock"
import { afterEach, beforeEach, describe, expect, it } from "vitest"

import {
  formatDateWithOrdinal,
  formatTimeWithoutMinutes,
  parseISOWithOptions,
  secondsToMinutes,
  standardDateFormat,
  standardDateTimeFormat,
  standardTimeFormat,
} from "./date"

const UTC_INPUT = "2025-09-13T13:00:00Z"

describe("Date Formatting Helpers", () => {
  describe("parseISOWithOptions", () => {
    it("parses as UTC by default", () => {
      const date = parseISOWithOptions(UTC_INPUT)
      expect(date.toISOString()).toBe("2025-09-13T13:00:00.000Z")
    })

    it("ignores timezone when flag is true", () => {
      const date = parseISOWithOptions(UTC_INPUT, true)
      expect(date.getFullYear()).toBe(2025)
      expect(date.getMonth()).toBe(8) // September
      expect(date.getDate()).toBe(13)
      expect(date.getHours()).toBe(13)
      expect(date.getMinutes()).toBe(0)
    })
  })

  describe("Formatting Functions in UTC System TZ", () => {
    beforeEach(() => {
      timezoneMock.register("UTC")
    })

    afterEach(() => {
      timezoneMock.unregister()
    })

    it("standardDateTimeFormat without ignore", () => {
      expect(standardDateTimeFormat(UTC_INPUT)).toBe("9/13/2025, 1:00 PM")
    })

    it("standardDateTimeFormat with ignore", () => {
      expect(standardDateTimeFormat(UTC_INPUT, true)).toBe("9/13/2025, 1:00 PM")
    })

    it("standardDateFormat without ignore", () => {
      expect(standardDateFormat(UTC_INPUT)).toBe("9/13/2025")
    })

    it("standardTimeFormat without ignore", () => {
      expect(standardTimeFormat(UTC_INPUT)).toBe("1:00 PM")
    })

    it("formatDateWithOrdinal without ignore", () => {
      expect(formatDateWithOrdinal(UTC_INPUT)).toBe("September 13th, 2025")
    })

    it("formatTimeWithoutMinutes without ignore", () => {
      expect(formatTimeWithoutMinutes(UTC_INPUT)).toBe("1PM")
    })
  })

  describe("Formatting Functions in Etc/GMT+6 (UTC-6, equivalent to MDT without DST)", () => {
    beforeEach(() => {
      timezoneMock.register("Etc/GMT+6")
    })

    afterEach(() => {
      timezoneMock.unregister()
    })

    it("standardDateTimeFormat without ignore (shifts to local)", () => {
      expect(standardDateTimeFormat(UTC_INPUT)).toBe("9/13/2025, 7:00 AM")
    })

    it("standardDateTimeFormat with ignore (treats as local)", () => {
      expect(standardDateTimeFormat(UTC_INPUT, true)).toBe("9/13/2025, 1:00 PM")
    })

    it("standardDateFormat without ignore (date shifts if crosses day)", () => {
      expect(standardDateFormat(UTC_INPUT)).toBe("9/13/2025") // No shift, same day
    })

    it("standardDateFormat with ignore (treats as local)", () => {
      expect(standardDateFormat(UTC_INPUT, true)).toBe("9/13/2025")
    })

    it("standardTimeFormat without ignore (shifts to local)", () => {
      expect(standardTimeFormat(UTC_INPUT)).toBe("7:00 AM")
    })

    it("standardTimeFormat with ignore (treats as local)", () => {
      expect(standardTimeFormat(UTC_INPUT, true)).toBe("1:00 PM")
    })

    it("formatDateWithOrdinal without ignore (shifts to local)", () => {
      expect(formatDateWithOrdinal(UTC_INPUT)).toBe("September 13th, 2025")
    })

    it("formatDateWithOrdinal with ignore (treats as local)", () => {
      expect(formatDateWithOrdinal(UTC_INPUT, true)).toBe(
        "September 13th, 2025",
      )
    })

    it("formatTimeWithoutMinutes without ignore (shifts to local)", () => {
      expect(formatTimeWithoutMinutes(UTC_INPUT)).toBe("7AM")
    })

    it("formatTimeWithoutMinutes with ignore (treats as local)", () => {
      expect(formatTimeWithoutMinutes(UTC_INPUT, true)).toBe("1PM")
    })
  })

  // Additional test for secondsToMinutes (no TZ involvement)
  it("secondsToMinutes", () => {
    expect(secondsToMinutes(120)).toBe("2 minutes")
    expect(secondsToMinutes(0)).toBe("0 minutes")
    expect(secondsToMinutes(undefined)).toBe("0 minutes")
  })
})
