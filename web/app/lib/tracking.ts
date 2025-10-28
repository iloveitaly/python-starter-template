/**
 * Centralized utilities for extracting and forwarding advertising/campaign tracking
 * parameters from URLs to backend APIs for attribution and analytics.
 */
import { log } from "~/configuration/logging"

/**
 * List of tracking parameter names recognized by the application.
 * These include advertising click IDs and UTM campaign parameters.
 *
 * - `fbclid`, `fbc`, `fbp` - Facebook click and browser identifiers
 * - `gclid` - Google Ads click identifier
 * - `msclkid` - Microsoft Ads click identifier
 * - `ttclid` - TikTok click identifier
 * - `via` - Rewardful referral code
 * - `utm_*` - Standard UTM campaign tracking parameters
 */
export const TRACKING_PARAM_NAMES = [
  "fbclid",
  "fbc",
  "fbp",
  "gclid",
  "msclkid",
  "ttclid",
  "via",
  "utm_source",
  "utm_medium",
  "utm_campaign",
  "utm_term",
  "utm_content",
] as const

export type TrackingParamName = (typeof TRACKING_PARAM_NAMES)[number]

/**
 * Extracts tracking parameters from URL search params for forwarding to backend APIs.
 * This is helpful for emitting server side events with the tracking parameters and reduces the risk
 * of client-side blockers that prevent the event from being emitted.
 *
 * @param searchParams - URLSearchParams to extract from. If omitted, uses window.location.search
 *                       (useful in clientLoaders where searchParams might not be available).
 *                       Pass explicitly when available (e.g., from useSearchParams).
 *
 * @returns Object containing only the tracking params that were present in the URL.
 *          Returns empty object if no tracking params found.
 *
 * @example
 * // In a clientLoader (no searchParams available)
 * const { data } = await getScreeningDetail({
 *   query: {
 *     ...trackingParamsFromSearch(),
 *   },
 * })
 *
 * @example
 * // In a component with searchParams
 * const [searchParams] = useSearchParams()
 * const { data } = await getScreeningsNear({
 *   query: {
 *     ...trackingParamsFromSearch(searchParams),
 *   },
 * })
 */
export function trackingParamsFromSearch(searchParams?: URLSearchParams): Record<string, string> {
  const sp = searchParams ?? (typeof window !== "undefined" ? new URLSearchParams(window.location.search) : undefined)

  const params: Record<string, string> = {}

  if (!sp) {
    log.error("trackingParamsFromSearch called without searchParams and window is undefined")
    return params
  }

  // TODO should clean this up with FP / ramda
  for (const key of TRACKING_PARAM_NAMES) {
    const value = sp.get(key)
    if (value) params[key] = value
  }

  return params
}
