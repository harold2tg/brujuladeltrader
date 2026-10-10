/**
 * Financial terminal palette — single JS source of truth.
 *
 * These hex values mirror the oklch tokens declared in app/globals.css.
 * Use them wherever a literal color is required (Recharts props, SVG
 * attributes, gradients); use the CSS variables (bg-card, text-profit, ...)
 * for normal Tailwind styling.
 */
export const PALETTE = {
  background: "#080F1A",
  sidebar: "#0B1422",
  card: "#101D2D",
  elevated: "#17263A",
  border: "#24364B",
  foreground: "#E2EAF4",
  mutedForeground: "#8FA3BA",
  primary: "#00D6B2",
  destructive: "#FF5263",
  info: "#4595FF",
  warning: "#F5B942",
  /** Fifth chart slot — violet, kept for session-overlap series. */
  violet: "#7C5CFF",
} as const;

export const CHART_COLORS = {
  positive: PALETTE.primary, // teal — profit, high win rate
  negative: PALETTE.destructive, // red — loss, low win rate
  neutral: PALETTE.mutedForeground, // slate — neutral data
  london: PALETTE.info, // blue — London session
  overlap: PALETTE.violet, // violet — NY/London overlap
  ny: PALETTE.warning, // amber — New York session
  off: PALETTE.border, // dark slate — outside any session
} as const;

/** Gradient pairs for chart fills (from → to) */
export const CHART_GRADIENTS = {
  positive: [PALETTE.primary, "#00A184"],
  negative: [PALETTE.destructive, "#CC3B4A"],
  primary: [PALETTE.info, "#2F6BC9"],
  secondary: [PALETTE.violet, "#5B3AD6"],
  amber: [PALETTE.warning, "#D99A2B"],
} as const;

/** Semantic color exports — the meaning layer used by metrics and charts. */
export const PROFIT_COLOR = CHART_COLORS.positive;
export const LOSS_COLOR = CHART_COLORS.negative;
export const INFO_COLOR = PALETTE.info;
export const WARNING_COLOR = PALETTE.warning;

/** Ordered categorical series colors (chart 1 → 5 in globals.css). */
export const SERIES_COLORS = [
  PALETTE.primary,
  PALETTE.info,
  PALETTE.warning,
  PALETTE.destructive,
  PALETTE.violet,
] as const;
