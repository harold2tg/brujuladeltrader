"use client";

import { useTranslations } from "next-intl";
import { TrendingUp, DollarSign, Target, BarChart3 } from "lucide-react";
import { MetricCard } from "./MetricCard";
import type { GlobalMetrics } from "@/lib/api/analytics";
import { formatCurrency, formatPercent } from "@/lib/utils/formatters";

interface MetricsGridProps {
  metrics: GlobalMetrics | undefined;
  loading?: boolean;
}

export function MetricsGrid({ metrics, loading }: MetricsGridProps) {
  const t = useTranslations("dashboard.metrics");

  return (
    <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
      <MetricCard
        title={t("winRate")}
        value={loading ? "—" : formatPercent(metrics?.win_rate ?? 0)}
        icon={<Target />}
        trend={
          loading
            ? "neutral"
            : (metrics?.win_rate ?? 0) >= 0.5
              ? "positive"
              : "negative"
        }
        loading={loading}
      />
      <MetricCard
        title={t("netPnl")}
        value={loading ? "—" : formatCurrency(metrics?.net_pnl ?? 0)}
        icon={<DollarSign />}
        trend={
          loading
            ? "neutral"
            : (metrics?.net_pnl ?? 0) >= 0
              ? "positive"
              : "negative"
        }
        loading={loading}
      />
      <MetricCard
        title={t("rrRatio")}
        value={
          loading
            ? "—"
            : metrics?.rr_ratio != null
              ? `${metrics.rr_ratio.toFixed(2)}`
              : "N/A"
        }
        icon={<TrendingUp />}
        trend={
          loading
            ? "neutral"
            : (metrics?.rr_ratio ?? 0) >= 1
              ? "positive"
              : "negative"
        }
        loading={loading}
      />
      <MetricCard
        title={t("totalTrades")}
        value={loading ? "—" : String(metrics?.total_trades ?? 0)}
        icon={<BarChart3 />}
        trend="neutral"
        loading={loading}
      />
    </div>
  );
}
