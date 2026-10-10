// Shared tooltip style for all charts — dark terminal theme.
// The design tokens in app/globals.css are oklch colors, so they are consumed
// directly as CSS variables (never wrapped in hsl(), which silently breaks).
// The cursor fill is a literal oklch value because Recharts writes it into an
// SVG presentation attribute, where custom properties are not resolved.
export const CHART_TOOLTIP_STYLE = {
  contentStyle: {
    backgroundColor: "var(--card)",
    border: "1px solid var(--border)",
    borderRadius: "8px",
    color: "var(--card-foreground)",
    boxShadow: "0 4px 12px oklch(0.043 0.025 258.8 / 0.5)",
  },
  // var(--muted) at 35% alpha
  cursor: { fill: "oklch(0.241 0.0399 255.2 / 0.35)" },
};
