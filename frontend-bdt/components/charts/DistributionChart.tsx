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
import { CHART_TOOLTIP_STYLE } from "@/lib/utils/chartStyles";
import type { DistributionBin } from "@/lib/api/analytics";

interface DistributionChartProps {
  data: DistributionBin[] | undefined;
  loading?: boolean;
}

function getBarColor(range: string): string {
  if (range.startsWith("<") || range.startsWith("-")) {
    const num = parseFloat(range.replace(/[<>]/g, "").split("/")[0]);
    if (num < -5) return LOSS_COLOR;
  }
  if (range.startsWith(">") || (!range.startsWith("-") && !range.startsWith("<"))) {
    return PROFIT_COLOR;
  }
  return CHART_COLORS.neutral;
}

export function DistributionChart({ data, loading }: DistributionChartProps) {
  const t = useTranslations("analytics.charts");

  if (loading) {
    return (
      <Card className="border-border/40">
        <CardHeader>
          <CardTitle className="text-base">{t("distribution")}</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[300px] w-full" />
        </CardContent>
      </Card>
    );
  }

  const chartData = (data ?? []).map((item) => ({
    range: item.range,
    count: item.count,
    fill: getBarColor(item.range),
  }));

  return (
    <Card className="border-border/40">
      <CardHeader>
        <CardTitle className="text-base">{t("distribution")}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke={PALETTE.border} strokeOpacity={0.5} />
            <XAxis
              dataKey="range"
              tick={{ fontSize: 12, fill: PALETTE.mutedForeground }}
              axisLine={{ stroke: PALETTE.border }}
              tickLine={{ stroke: PALETTE.border }}
            />
            <YAxis
              tick={{ fontSize: 12, fill: PALETTE.mutedForeground }}
              axisLine={{ stroke: PALETTE.border }}
              tickLine={{ stroke: PALETTE.border }}
              className="font-mono"
            />
            <Tooltip
              formatter={(value) => [String(value), "Trades"]}
              {...CHART_TOOLTIP_STYLE}
            />
            <Bar dataKey="count" radius={[4, 4, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
