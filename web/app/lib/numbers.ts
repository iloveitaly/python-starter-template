/**
 * Locale-aware numeric formatting (non-currency).
 */

/** Whole-number display with grouping separators (e.g. thousands commas in en-US). */
export function formatInteger(value: number): string {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 0,
  }).format(value)
}
