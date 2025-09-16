/**
 * Helpers for date & time formatting.
 *
 * `ignoreTimezone` is helpful if you store a datetime in a DB assuming that the person
 * looking at the date will never need it time shifted. i.e. it should always display in
 * their local time. This method ignores the timezone and ensures the formatted date/time
 * is not shifted to the local timezone.
 */
import { format, formatDuration, intervalToDuration, parseISO } from "date-fns"

export function parseISOWithOptions(
  dateStr: string,
  ignoreTimezone: boolean = false,
): Date {
  const date = parseISO(dateStr)
  if (ignoreTimezone) {
    return new Date(
      date.getUTCFullYear(),
      date.getUTCMonth(),
      date.getUTCDate(),
      date.getUTCHours(),
      date.getUTCMinutes(),
      date.getUTCSeconds(),
      date.getUTCMilliseconds(),
    )
  }
  return date
}

export function secondsToMinutes(seconds?: number | undefined) {
  if (!seconds) return "0 minutes"

  return formatDuration(intervalToDuration({ start: 0, end: seconds * 1000 }), {
    format: ["minutes"],
  })
}

export function standardDateTimeFormat(
  dateStr: string,
  ignoreTimezone: boolean = false,
) {
  const date = parseISOWithOptions(dateStr, ignoreTimezone)
  return format(date, "M/d/yyyy, h:mm a")
}

export function standardDateFormat(
  dateStr: string,
  ignoreTimezone: boolean = false,
) {
  const date = parseISOWithOptions(dateStr, ignoreTimezone)
  return format(date, "M/d/yyyy")
}

export function standardTimeFormat(
  dateStr: string,
  ignoreTimezone: boolean = false,
) {
  const date = parseISOWithOptions(dateStr, ignoreTimezone)
  return format(date, "h:mm a")
}

// Formats dates like "January 20th, 2025" with appropriate ordinal suffix (st, nd, rd, th).
export function formatDateWithOrdinal(
  dateStr: string,
  ignoreTimezone: boolean = false,
): string {
  const date = parseISOWithOptions(dateStr, ignoreTimezone)
  return format(date, "MMMM do, yyyy")
}

// Formats time like "7pm", "4pm", etc. without minutes
export function formatTimeWithoutMinutes(
  dateStr: string,
  ignoreTimezone: boolean = false,
): string {
  const date = parseISOWithOptions(dateStr, ignoreTimezone)
  return format(date, "ha")
}
