export const CHART_COLORS = {
  positive: "#22c55e",   // emerald — ganancia, win rate alto
  negative: "#ef4444",   // rojo — pérdida, win rate bajo
  neutral: "#64748b",    // slate — datos neutros
  london: "#6366f1",     // indigo — sesión Londres
  overlap: "#a855f7",    // púrpura — overlap NY/Londres
  ny: "#f59e0b",         // ámbar — sesión NY
  off: "#475569",        // slate oscuro — fuera de sesión
} as const;

/** Gradient pairs for chart fills (from → to) */
export const CHART_GRADIENTS = {
  positive: ["#22c55e", "#16a34a"],
  negative: ["#ef4444", "#dc2626"],
  primary: ["#6366f1", "#4f46e5"],
  secondary: ["#a855f7", "#9333ea"],
  amber: ["#f59e0b", "#d97706"],
} as const;
