/**
 * Number and date formatters using Intl API.
 * All formatters respect the active locale.
 */

/**
 * Format a number as currency (USD by default).
 */
export function formatCurrency(amount: number, locale = "es"): string {
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

/**
 * Format a decimal value as a percentage (e.g. 0.65 → "65.00%").
 */
export function formatPercent(value: number, locale = "es"): string {
  return new Intl.NumberFormat(locale, {
    style: "percent",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

/**
 * Format a date string or Date object to a locale-aware short date.
 */
export function formatDate(
  date: string | Date,
  locale = "es",
): string {
  const d = typeof date === "string" ? new Date(date) : date;
  return new Intl.DateTimeFormat(locale, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(d);
}
