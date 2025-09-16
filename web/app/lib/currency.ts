/**
 * Generic currency formatting and conversion utilities
 */

/**
 * Format a currency amount in cents to a string with two decimal places
 */
export const formatCurrency = (amount: number): string => {
  // amount is in cents, always show two decimal places
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount / 100)
}

/**
 * Whole-dollar currency formatting (no cents)
 */
export const formatDollars = (amountInCents: number): string => {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amountInCents / 100)
}
