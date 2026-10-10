"use client";

import { useTranslations } from "next-intl";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { formatCurrency } from "@/lib/utils/formatters";
import { CHART_TOOLTIP_STYLE } from "@/lib/utils/chartStyles";
import { CHART_GRADIENTS, PALETTE, PROFIT_COLOR } from "@/lib/utils/colors";
import type { EquityCurvePoint } from "@/lib/api/analytics";

interface EquityCurveChartProps {
  data: EquityCurvePoint[] | undefined;
  loading?: boolean;
}

export function EquityCurveChart({ data, loading }: EquityCurveChartProps) {
  const t = useTranslations("dashboard.charts");

  if (loading) {
    return (
      <Card className="border-border/40">
        <CardHeader>
          <CardTitle className="text-base">{t("equityCurve")}</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[300px] w-full" />
        </CardContent>
      </Card>
    );
  }

  // Use sequential index as key, but show month labels on X-axis
  const chartData = (data ?? []).map((point, index) => ({
    index,
    balance: point.balance,
    pnl: point.net_pnl,
    label: point.label,
  }));

  const minBalance = Math.min(...chartData.map((d) => d.balance));
  const maxBalance = Math.max(...chartData.map((d) => d.balance));
  const padding = (maxBalance - minBalance) * 0.1 || 50;

  // Only show labels where they exist (month boundaries)
  const tickFormatter = (value: number) => {
    const point = chartData[value];
    return point?.label ?? "";
  };

  return (
    <Card className="border-border/40">
      <CardHeader>
        <CardTitle className="text-base">{t("equityCurve")}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={chartData}>
            <defs>
              {/* SVG paint attributes cannot resolve CSS custom properties, so the
                  palette comes from lib/utils/colors (same hex as the oklch tokens). */}
              <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={CHART_GRADIENTS.positive[0]} stopOpacity={0.28} />
                <stop offset="95%" stopColor={CHART_GRADIENTS.positive[1]} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke={PALETTE.border} strokeOpacity={0.5} />
            <XAxis
              dataKey="index"
              tick={{ fontSize: 11, fill: PALETTE.mutedForeground }}
              axisLine={{ stroke: PALETTE.border }}
              tickLine={{ stroke: PALETTE.border }}
              tickFormatter={tickFormatter}
              interval={0}
            />
            <YAxis
              tick={{ fontSize: 11, fill: PALETTE.mutedForeground }}
              axisLine={{ stroke: PALETTE.border }}
              tickLine={{ stroke: PALETTE.border }}
              className="font-mono"
              tickFormatter={(v: number) => `$${v}`}
              domain={[minBalance - padding, maxBalance + padding]}
            />
            <Tooltip
              formatter={(value, name) => [
                formatCurrency(Number(value)),
                name === "balance" ? "Balance" : "PnL",
              ]}
              {...CHART_TOOLTIP_STYLE}
            />
            {/* Starting-balance baseline: neutral, subtle. */}
            <ReferenceLine
              y={chartData[0]?.balance ?? 0}
              stroke={PALETTE.mutedForeground}
              strokeOpacity={0.5}
              strokeDasharray="3 3"
            />
            <Area
              type="monotone"
              dataKey="balance"
              stroke={PROFIT_COLOR}
              strokeWidth={2}
              fill="url(#equityGradient)"
              dot={false}
              activeDot={{ r: 4, strokeWidth: 2, fill: PROFIT_COLOR }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
