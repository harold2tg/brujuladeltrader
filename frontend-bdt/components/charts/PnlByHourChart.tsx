"use client";

import { useTranslations } from "next-intl";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { CHART_COLORS } from "@/lib/utils/colors";
import { formatCurrency } from "@/lib/utils/formatters";
import type { HourMetrics } from "@/lib/api/analytics";

interface PnlByHourChartProps {
  data: HourMetrics[] | undefined;
  loading?: boolean;
}

const HOURS = Array.from({ length: 24 }, (_, i) => i);

function getBarColor(pnl: number): string {
  if (pnl > 0) return CHART_COLORS.positive;
  if (pnl < 0) return CHART_COLORS.negative;
  return CHART_COLORS.neutral;
}

export function PnlByHourChart({ data, loading }: PnlByHourChartProps) {
  const t = useTranslations("analytics.charts");

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t("pnlByHour")}</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[300px] w-full" />
        </CardContent>
      </Card>
    );
  }

  const chartData = HOURS.map((hour) => {
    const found = data?.find((d) => d.hour === hour);
    return {
      hour: `${String(hour).padStart(2, "0")}:00`,
      net_pnl: found?.net_pnl ?? 0,
    };
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{t("pnlByHour")}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="hour"
              tick={{ fontSize: 12 }}
              className="text-muted-foreground"
            />
            <YAxis
              tick={{ fontSize: 12 }}
              className="text-muted-foreground"
              tickFormatter={(v: number) => formatCurrency(v)}
            />
            <Tooltip
              formatter={(value) => [formatCurrency(Number(value)), "PnL"]}
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "8px",
              }}
            />
            <Bar dataKey="net_pnl" radius={[4, 4, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getBarColor(entry.net_pnl)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
