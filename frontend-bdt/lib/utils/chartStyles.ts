// Shared tooltip style for all charts — works in light and dark mode
export const CHART_TOOLTIP_STYLE = {
  contentStyle: {
    backgroundColor: "hsl(var(--card))",
    border: "1px solid hsl(var(--border))",
    borderRadius: "8px",
    color: "hsl(var(--card-foreground))",
    boxShadow: "0 4px 12px rgba(0, 0, 0, 0.15)",
  },
  cursor: { fill: "hsl(var(--muted) / 0.3)" },
};
