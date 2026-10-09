"use client";

import { useTranslations } from "next-intl";
import { Activity, Database } from "lucide-react";
import Link from "next/link";
import { PageHeader } from "@/components/layout/PageHeader";
import { buttonVariants } from "@/components/ui/button";
import { MetricsGrid } from "@/components/metrics/MetricsGrid";
import { EquityCurveChart } from "@/components/charts/EquityCurveChart";
import { MonthlyPnlChart } from "@/components/charts/MonthlyPnlChart";
import { SessionPnlBarChart } from "@/components/charts/SessionPnlBarChart";
import { EmptyState } from "@/components/shared/EmptyState";
import { useAnalytics, useAnalyticsByMonth, useAnalyticsBySession, useEquityCurve } from "@/lib/hooks/useAnalytics";
import { useDataSources } from "@/lib/hooks/useDataSources";

export default function DashboardPage() {
  const t = useTranslations("dashboard");

  const { data: dataSourcesData } = useDataSources();
  const dataSources = dataSourcesData?.data_sources ?? [];
  const latestDataSourceId = dataSources.length > 0 ? dataSources[0].id : null;

  const { data: analyticsData, isLoading: analyticsLoading } = useAnalytics(latestDataSourceId);
  const { data: equityData, isLoading: equityLoading } = useEquityCurve(latestDataSourceId);
  const { data: monthlyData, isLoading: monthlyLoading } = useAnalyticsByMonth(latestDataSourceId);
  const { data: sessionData, isLoading: sessionLoading } = useAnalyticsBySession(latestDataSourceId);

  const metrics = analyticsData?.data?.global;

  if (dataSources.length === 0) {
    return (
      <div className="space-y-6">
        <PageHeader title={t("title")} />
        <EmptyState
          icon={<Database />}
          title={t("empty")}
          description={t("emptyHint")}
          action={
            <Link href="/data-sources" className={buttonVariants()}>
              {t("selectDataSource")}
            </Link>
          }
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("title")}
        description={t("latestDataSource", { name: dataSources[0]?.name })}
      />

      {/* Quick diagnostic banner */}
      {metrics && (
        <div
          className={`relative overflow-hidden rounded-xl border p-4 ${
            metrics.net_pnl >= 0
              ? "border-emerald-500/20 bg-gradient-to-r from-emerald-500/10 via-emerald-500/5 to-transparent"
              : "border-red-500/20 bg-gradient-to-r from-red-500/10 via-red-500/5 to-transparent"
          }`}
        >
          <div className="flex items-center gap-3">
            <div
              className={`flex size-10 items-center justify-center rounded-xl ${
                metrics.net_pnl >= 0 ? "bg-emerald-500/15" : "bg-red-500/15"
              }`}
            >
              <Activity
                className={`size-5 ${
                  metrics.net_pnl >= 0 ? "text-emerald-400" : "text-red-400"
                }`}
              />
            </div>
            <p
              className={`text-sm font-semibold ${
                metrics.net_pnl >= 0 ? "text-emerald-300" : "text-red-300"
              }`}
            >
              {metrics.net_pnl >= 0
                ? t("diagnostic.profitable")
                : t("diagnostic.notProfitable")}
            </p>
          </div>
        </div>
      )}

      {/* Metrics grid */}
      <MetricsGrid metrics={metrics} loading={analyticsLoading} />

      {/* Charts */}
      <EquityCurveChart data={equityData?.data} loading={equityLoading} />

      <div className="grid gap-6 lg:grid-cols-2">
        <MonthlyPnlChart data={monthlyData?.data} loading={monthlyLoading} />
        <SessionPnlBarChart data={sessionData?.data} loading={sessionLoading} />
      </div>
    </div>
  );
}
