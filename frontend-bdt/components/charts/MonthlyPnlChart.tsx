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
import { PALETTE, CHART_COLORS, LOSS_COLOR, PROFIT_COLOR } from "@/lib/utils/colors";
import { formatCurrency } from "@/lib/utils/formatters";
import { CHART_TOOLTIP_STYLE } from "@/lib/utils/chartStyles";
import type { MonthlyMetrics } from "@/lib/api/analytics";

interface MonthlyPnlChartProps {
  data: MonthlyMetrics[] | undefined;
  loading?: boolean;
}

function getBarColor(pnl: number): string {
  if (pnl > 0) return PROFIT_COLOR;
  if (pnl < 0) return LOSS_COLOR;
  return CHART_COLORS.neutral;
}

export function MonthlyPnlChart({ data, loading }: MonthlyPnlChartProps) {
  const t = useTranslations("analytics.charts");

  if (loading) {
    return (
      <Card className="border-border/40">
        <CardHeader>
          <CardTitle className="text-base">{t("monthlyPnl")}</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[300px] w-full" />
        </CardContent>
      </Card>
    );
  }

  const chartData = (data ?? []).map((item) => ({
    month: item.label?.split(" ")[0] ?? String(item.month),
    net_pnl: item.net_pnl,
  }));

  return (
    <Card className="border-border/40">
      <CardHeader>
        <CardTitle className="text-base">{t("monthlyPnl")}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke={PALETTE.border} strokeOpacity={0.5} />
            <XAxis
              dataKey="month"
              tick={{ fontSize: 12, fill: PALETTE.mutedForeground }}
              axisLine={{ stroke: PALETTE.border }}
              tickLine={{ stroke: PALETTE.border }}
            />
            <YAxis
              tick={{ fontSize: 12, fill: PALETTE.mutedForeground }}
              axisLine={{ stroke: PALETTE.border }}
              tickLine={{ stroke: PALETTE.border }}
              className="font-mono"
              tickFormatter={(v: number) => formatCurrency(v)}
            />
            <Tooltip
              formatter={(value) => [formatCurrency(Number(value)), "PnL"]}
              {...CHART_TOOLTIP_STYLE}
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
