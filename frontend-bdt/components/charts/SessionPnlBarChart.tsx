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
  ReferenceLine,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { PALETTE, LOSS_COLOR, PROFIT_COLOR } from "@/lib/utils/colors";
import { formatCurrency } from "@/lib/utils/formatters";
import { CHART_TOOLTIP_STYLE } from "@/lib/utils/chartStyles";
import type { SessionMetrics } from "@/lib/api/analytics";

interface SessionPnlBarChartProps {
  data: SessionMetrics[] | undefined;
  loading?: boolean;
}

const SESSION_LABELS: Record<string, string> = {
  london_open: "London",
  ny_overlap: "Overlap",
  ny_session: "NY Session",
  off_hours: "Off Hours",
};

function getBarColor(pnl: number): string {
  // Session bars are profit/loss series: teal above zero, red below.
  if (pnl >= 0) return PROFIT_COLOR;
  return LOSS_COLOR;
}

export function SessionPnlBarChart({ data, loading }: SessionPnlBarChartProps) {
  const t = useTranslations("dashboard.charts");

  if (loading) {
    return (
      <Card className="border-border/40">
        <CardHeader>
          <CardTitle className="text-base">{t("sessionPnl")}</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[300px] w-full" />
        </CardContent>
      </Card>
    );
  }

  const chartData = (data ?? []).map((item) => ({
    session: SESSION_LABELS[item.session] ?? item.session,
    net_pnl: item.net_pnl,
    total_trades: item.total_trades,
    win_rate: item.win_rate,
  }));

  return (
    <Card className="border-border/40">
      <CardHeader>
        <CardTitle className="text-base">{t("sessionPnl")}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke={PALETTE.border} strokeOpacity={0.5} />
            <XAxis
              dataKey="session"
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
              formatter={(value) => [
                formatCurrency(Number(value)),
                "PnL Neto",
              ]}
              {...CHART_TOOLTIP_STYLE}
            />
            <ReferenceLine
              y={0}
              stroke={PALETTE.mutedForeground}
              strokeOpacity={0.5}
              strokeDasharray="3 3"
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
