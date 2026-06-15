"use client";

import { useTranslations } from "next-intl";
import { Activity, Upload } from "lucide-react";
import Link from "next/link";
import { PageHeader } from "@/components/layout/PageHeader";
import { buttonVariants } from "@/components/ui/button";
import { MetricsGrid } from "@/components/metrics/MetricsGrid";
import { EquityCurveChart } from "@/components/charts/EquityCurveChart";
import { MonthlyPnlChart } from "@/components/charts/MonthlyPnlChart";
import { SessionPnlBarChart } from "@/components/charts/SessionPnlBarChart";
import { EmptyState } from "@/components/shared/EmptyState";
import { useAnalytics, useAnalyticsByMonth, useAnalyticsBySession, useEquityCurve } from "@/lib/hooks/useAnalytics";
import { useUploads } from "@/lib/hooks/useUploads";

export default function DashboardPage() {
  const t = useTranslations("dashboard");

  const { data: uploadsData } = useUploads();
  const uploads = uploadsData?.data?.items ?? [];
  const latestUploadId = uploads.length > 0 ? uploads[0].id : null;

  const { data: analyticsData, isLoading: analyticsLoading } = useAnalytics(latestUploadId);
  const { data: equityData, isLoading: equityLoading } = useEquityCurve(latestUploadId);
  const { data: monthlyData, isLoading: monthlyLoading } = useAnalyticsByMonth(latestUploadId);
  const { data: sessionData, isLoading: sessionLoading } = useAnalyticsBySession(latestUploadId);

  const metrics = analyticsData?.data?.global;

  if (uploads.length === 0) {
    return (
      <div className="space-y-6">
        <PageHeader title={t("title")} />
        <EmptyState
          icon={<Upload />}
          title={t("empty")}
          description={t("emptyHint")}
          action={
            <Link href="/uploads" className={buttonVariants()}>
              {t("selectUpload")}
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
        description={t("latestUpload", { name: uploads[0]?.original_name })}
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
