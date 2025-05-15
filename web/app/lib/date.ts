// helpers for date & time formatting
import { formatDuration, intervalToDuration } from "date-fns"

export function secondsToMinutes(seconds?: number | undefined) {
  if (!seconds) return "0 minutes"

  return formatDuration(intervalToDuration({ start: 0, end: seconds * 1000 }), {
    format: ["minutes"],
  })
}

export function standardDateTimeFormat(date: string) {
  return new Date(date).toLocaleString("en-US", {
    dateStyle: "short",
    timeStyle: "short",
  })
}

export function standardDateFormat(date: string) {
  return new Date(date).toLocaleString("en-US", {
    dateStyle: "short",
  })
}
