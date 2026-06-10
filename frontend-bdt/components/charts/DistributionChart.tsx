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
import type { DistributionBin } from "@/lib/api/analytics";

interface DistributionChartProps {
  data: DistributionBin[] | undefined;
  loading?: boolean;
}

function getBarColor(range: string): string {
  if (range.startsWith("<") || range.startsWith("-")) {
    const num = parseFloat(range.replace(/[<>]/g, "").split("/")[0]);
    if (num < -5) return CHART_COLORS.negative;
  }
  if (range.startsWith(">") || (!range.startsWith("-") && !range.startsWith("<"))) {
    return CHART_COLORS.positive;
  }
  return CHART_COLORS.neutral;
}

export function DistributionChart({ data, loading }: DistributionChartProps) {
  const t = useTranslations("analytics.charts");

  if (loading) {
    return (
      <Card>
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
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{t("distribution")}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="range"
              tick={{ fontSize: 12 }}
              className="text-muted-foreground"
            />
            <YAxis
              tick={{ fontSize: 12 }}
              className="text-muted-foreground"
            />
            <Tooltip
              formatter={(value) => [String(value), "Trades"]}
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "8px",
              }}
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
