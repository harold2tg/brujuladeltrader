"use client";

import { useTranslations } from "next-intl";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { CHART_COLORS } from "@/lib/utils/colors";
import { formatCurrency } from "@/lib/utils/formatters";
import { CHART_TOOLTIP_STYLE } from "@/lib/utils/chartStyles";
import type { SessionMetrics } from "@/lib/api/analytics";

interface SessionPieChartProps {
  data: SessionMetrics[] | undefined;
  loading?: boolean;
}

const SESSION_COLORS: Record<string, string> = {
  london_open: CHART_COLORS.london,
  ny_overlap: CHART_COLORS.overlap,
  ny_session: CHART_COLORS.ny,
  off_hours: CHART_COLORS.off,
};

const SESSION_LABELS: Record<string, string> = {
  london_open: "London Open",
  ny_overlap: "NY / London Overlap",
  ny_session: "NY Session",
  off_hours: "Off Hours",
};

export function SessionPieChart({ data, loading }: SessionPieChartProps) {
  const t = useTranslations("analytics.charts");

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t("bySession")}</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[300px] w-full" />
        </CardContent>
      </Card>
    );
  }

  const chartData = (data ?? []).map((item) => ({
    name: SESSION_LABELS[item.session] ?? item.session,
    value: Math.abs(item.net_pnl),
    net_pnl: item.net_pnl,
    fill: SESSION_COLORS[item.session] ?? CHART_COLORS.neutral,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{t("bySession")}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              paddingAngle={2}
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.fill} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value, name) => [
                formatCurrency(Number(value)),
                String(name),
              ]}
              {...CHART_TOOLTIP_STYLE}
            />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
