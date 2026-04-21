/**
 * Generic currency formatting and conversion utilities
 */

/** Format cents as USD with exactly two fractional digits. */
export const formatCurrency = (amountInCents: number): string => {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amountInCents / 100)
}

/** Format cents as whole US dollars (no fractional digits). */
export const formatDollars = (amountInCents: number): string => {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amountInCents / 100)
}

/** Format cents as USD, omitting unnecessary trailing zeros after the decimal. */
export const formatShortestCurrency = (amountInCents: number): string => {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(amountInCents / 100)
}
