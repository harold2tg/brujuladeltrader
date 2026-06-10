import { z } from "zod";

export const alertRuleSchema = z.object({
  alert_type: z.string().min(1, "Tipo de alerta requerido"),
  threshold: z.number().positive("El umbral debe ser un número positivo"),
});

export type AlertRuleFormData = z.infer<typeof alertRuleSchema>;

export const ALERT_TYPE_OPTIONS = [
  "daily_loss",
  "weekly_loss",
  "monthly_loss",
  "max_drawdown",
  "win_rate_drop",
] as const;

export type AlertTypeOption = (typeof ALERT_TYPE_OPTIONS)[number];
