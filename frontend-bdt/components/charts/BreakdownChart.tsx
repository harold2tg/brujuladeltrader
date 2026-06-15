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
  Legend,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { CHART_COLORS } from "@/lib/utils/colors";
import { formatCurrency } from "@/lib/utils/formatters";
import { CHART_TOOLTIP_STYLE } from "@/lib/utils/chartStyles";

interface BreakdownItem {
  label: string;
  trades: number;
  wins: number;
  losses: number;
  win_rate: number;
  net_pnl: number;
  avg_pnl: number;
}

interface BreakdownChartProps {
  title: string;
  data: BreakdownItem[] | undefined;
  loading?: boolean;
}

function getBarColor(pnl: number): string {
  if (pnl > 0) return CHART_COLORS.positive;
  if (pnl < 0) return CHART_COLORS.negative;
  return CHART_COLORS.neutral;
}

export function BreakdownChart({ title, data, loading }: BreakdownChartProps) {
  const t = useTranslations("analytics.charts");

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[300px] w-full" />
        </CardContent>
      </Card>
    );
  }

  const chartData = (data ?? []).map((item) => ({
    label: item.label,
    net_pnl: item.net_pnl,
    win_rate: item.win_rate,
    trades: item.trades,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 12 }}
              className="text-muted-foreground"
            />
            <YAxis
              yAxisId="pnl"
              tick={{ fontSize: 12 }}
              className="text-muted-foreground"
              tickFormatter={(v: number) => formatCurrency(v)}
            />
            <YAxis
              yAxisId="wr"
              orientation="right"
              tick={{ fontSize: 12 }}
              className="text-muted-foreground"
              tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
              domain={[0, 1]}
            />
            <Tooltip
              formatter={(value, name) => {
                if (name === "PnL") return [formatCurrency(Number(value)), "PnL"];
                if (name === "Win Rate") return [`${(Number(value) * 100).toFixed(1)}%`, "Win Rate"];
                return [value, name];
              }}
              {...CHART_TOOLTIP_STYLE}
            />
            <Legend />
            <Bar yAxisId="pnl" dataKey="net_pnl" name="PnL" radius={[4, 4, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getBarColor(entry.net_pnl)} />
              ))}
            </Bar>
            <Bar yAxisId="wr" dataKey="win_rate" name="Win Rate" fill={CHART_COLORS.neutral} radius={[4, 4, 0, 0]} opacity={0.6} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
