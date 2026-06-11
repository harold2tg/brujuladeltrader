"use client";

import { useTranslations } from "next-intl";
import { Activity, Upload } from "lucide-react";
import Link from "next/link";
import { PageHeader } from "@/components/layout/PageHeader";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { MetricsGrid } from "@/components/metrics/MetricsGrid";
import { PnlByHourChart } from "@/components/charts/PnlByHourChart";
import { WinRateByDayChart } from "@/components/charts/WinRateByDayChart";
import { EmptyState } from "@/components/shared/EmptyState";
import { useAnalytics, useAnalyticsByHour, useAnalyticsByDay } from "@/lib/hooks/useAnalytics";
import { useUploads } from "@/lib/hooks/useUploads";

export default function DashboardPage() {
  const t = useTranslations("dashboard");

  const { data: uploadsData } = useUploads();
  const uploads = uploadsData?.data?.items ?? [];
  const latestUploadId = uploads.length > 0 ? uploads[0].id : null;

  const { data: analyticsData, isLoading: analyticsLoading } = useAnalytics(latestUploadId);
  const { data: hourlyData, isLoading: hourlyLoading } = useAnalyticsByHour(latestUploadId);
  const { data: dailyData, isLoading: dailyLoading } = useAnalyticsByDay(latestUploadId);

  const metrics = analyticsData?.data;

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
        <Card
          className={
            metrics.net_pnl >= 0
              ? "border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950"
              : "border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950"
          }
        >
          <CardContent className="flex items-center gap-3 py-3">
            <Activity
              className={`size-5 ${
                metrics.net_pnl >= 0 ? "text-green-600" : "text-red-600"
              }`}
            />
            <p
              className={`text-sm font-medium ${
                metrics.net_pnl >= 0 ? "text-green-800 dark:text-green-200" : "text-red-800 dark:text-red-200"
              }`}
            >
              {metrics.net_pnl >= 0
                ? t("diagnostic.profitable")
                : t("diagnostic.notProfitable")}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Metrics grid */}
      <MetricsGrid metrics={metrics} loading={analyticsLoading} />

      {/* Charts */}
      <div className="grid gap-6 lg:grid-cols-2">
        <PnlByHourChart data={hourlyData?.data} loading={hourlyLoading} />
        <WinRateByDayChart data={dailyData?.data} loading={dailyLoading} />
      </div>
    </div>
  );
}
