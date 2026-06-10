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
import { formatPercent } from "@/lib/utils/formatters";
import type { DayMetrics } from "@/lib/api/analytics";

interface WinRateByDayChartProps {
  data: DayMetrics[] | undefined;
  loading?: boolean;
}

const DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

function getBarColor(winRate: number): string {
  if (winRate >= 0.5) return CHART_COLORS.positive;
  return CHART_COLORS.negative;
}

export function WinRateByDayChart({ data, loading }: WinRateByDayChartProps) {
  const t = useTranslations("analytics.charts");

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t("winRateByDay")}</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[300px] w-full" />
        </CardContent>
      </Card>
    );
  }

  const chartData = DAY_NAMES.map((name, index) => {
    const found = data?.find((d) => d.day_of_week === index + 1);
    return {
      day: name,
      win_rate: found?.win_rate ?? 0,
      total_trades: found?.total_trades ?? 0,
    };
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{t("winRateByDay")}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="day"
              tick={{ fontSize: 12 }}
              className="text-muted-foreground"
            />
            <YAxis
              tick={{ fontSize: 12 }}
              className="text-muted-foreground"
              tickFormatter={(v: number) => formatPercent(v)}
              domain={[0, 1]}
            />
            <Tooltip
              formatter={(value) => [formatPercent(Number(value)), "Win Rate"]}
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "8px",
              }}
            />
            <Bar dataKey="win_rate" radius={[4, 4, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={getBarColor(entry.win_rate)}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
