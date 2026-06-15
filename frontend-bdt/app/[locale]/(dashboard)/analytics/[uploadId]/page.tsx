"use client";

import { useTranslations } from "next-intl";
import { useParams } from "next/navigation";
import { Upload } from "lucide-react";
import Link from "next/link";
import { PageHeader } from "@/components/layout/PageHeader";
import { buttonVariants } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { EmptyState } from "@/components/shared/EmptyState";
import { MetricsGrid } from "@/components/metrics/MetricsGrid";
import { PnlByHourChart } from "@/components/charts/PnlByHourChart";
import { WinRateByDayChart } from "@/components/charts/WinRateByDayChart";
import { SessionPieChart } from "@/components/charts/SessionPieChart";
import { MonthlyPnlChart } from "@/components/charts/MonthlyPnlChart";
import { BreakdownChart } from "@/components/charts/BreakdownChart";
import { DistributionChart } from "@/components/charts/DistributionChart";
import {
  useAnalytics,
  useAnalyticsByHour,
  useAnalyticsByDay,
  useAnalyticsBySession,
  useAnalyticsByMonth,
  useAnalyticsByWeek,
  useAnalyticsBySemester,
  useAnalyticsByYear,
  useAnalyticsDistribution,
} from "@/lib/hooks/useAnalytics";
import { useState } from "react";

type TabValue =
  | "summary"
  | "by-hour"
  | "by-day"
  | "by-session"
  | "by-month"
  | "by-week"
  | "by-semester"
  | "by-year"
  | "distribution";

export default function AnalyticsPage() {
  const t = useTranslations("analytics");
  const params = useParams();
  const uploadId = params.uploadId as string;

  const [activeTab, setActiveTab] = useState<TabValue>("summary");

  const { data: analyticsData, isLoading: analyticsLoading } = useAnalytics(uploadId);
  const { data: hourlyData, isLoading: hourlyLoading } = useAnalyticsByHour(
    activeTab === "by-hour" ? uploadId : null,
  );
  const { data: dailyData, isLoading: dailyLoading } = useAnalyticsByDay(
    activeTab === "by-day" ? uploadId : null,
  );
  const { data: sessionData, isLoading: sessionLoading } = useAnalyticsBySession(
    activeTab === "by-session" ? uploadId : null,
  );
  const { data: monthlyData, isLoading: monthlyLoading } = useAnalyticsByMonth(
    activeTab === "by-month" ? uploadId : null,
  );
  const { data: weeklyData, isLoading: weeklyLoading } = useAnalyticsByWeek(
    activeTab === "by-week" ? uploadId : null,
  );
  const { data: semesterData, isLoading: semesterLoading } = useAnalyticsBySemester(
    activeTab === "by-semester" ? uploadId : null,
  );
  const { data: yearlyData, isLoading: yearlyLoading } = useAnalyticsByYear(
    activeTab === "by-year" ? uploadId : null,
  );
  const { data: distributionData, isLoading: distributionLoading } =
    useAnalyticsDistribution(activeTab === "distribution" ? uploadId : null);

  if (!uploadId) {
    return (
      <div className="space-y-6">
        <PageHeader title={t("title")} />
        <EmptyState
          icon={<Upload />}
          title={t("noUpload")}
          description={t("noUploadHint")}
          action={
            <Link href="/uploads" className={buttonVariants()}>
              {t("goToUploads")}
            </Link>
          }
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader title={t("title")} />

      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as TabValue)}>
        <TabsList className="w-full justify-start overflow-x-auto">
          <TabsTrigger value="summary">{t("tabs.summary")}</TabsTrigger>
          <TabsTrigger value="by-hour">{t("tabs.byHour")}</TabsTrigger>
          <TabsTrigger value="by-day">{t("tabs.byDay")}</TabsTrigger>
          <TabsTrigger value="by-week">{t("tabs.byWeek")}</TabsTrigger>
          <TabsTrigger value="by-month">{t("tabs.byMonth")}</TabsTrigger>
          <TabsTrigger value="by-semester">{t("tabs.bySemester")}</TabsTrigger>
          <TabsTrigger value="by-year">{t("tabs.byYear")}</TabsTrigger>
          <TabsTrigger value="by-session">{t("tabs.bySession")}</TabsTrigger>
          <TabsTrigger value="distribution">{t("tabs.distribution")}</TabsTrigger>
        </TabsList>

        {/* Summary Tab */}
        <TabsContent value="summary" className="space-y-6 pt-4">
          <MetricsGrid metrics={analyticsData?.data?.global} loading={analyticsLoading} />
          <div className="grid gap-6 lg:grid-cols-2">
            <PnlByHourChart
              data={hourlyData?.data}
              loading={hourlyLoading}
            />
            <WinRateByDayChart
              data={dailyData?.data}
              loading={dailyLoading}
            />
          </div>
        </TabsContent>

        {/* By Hour Tab */}
        <TabsContent value="by-hour" className="pt-4">
          <PnlByHourChart
            data={hourlyData?.data}
            loading={hourlyLoading}
          />
        </TabsContent>

        {/* By Day Tab */}
        <TabsContent value="by-day" className="pt-4">
          <WinRateByDayChart
            data={dailyData?.data}
            loading={dailyLoading}
          />
        </TabsContent>

        {/* By Week Tab */}
        <TabsContent value="by-week" className="pt-4">
          <BreakdownChart
            title={t("tabs.byWeek")}
            data={weeklyData?.data}
            loading={weeklyLoading}
          />
        </TabsContent>

        {/* By Month Tab */}
        <TabsContent value="by-month" className="pt-4">
          <MonthlyPnlChart
            data={monthlyData?.data}
            loading={monthlyLoading}
          />
        </TabsContent>

        {/* By Semester Tab */}
        <TabsContent value="by-semester" className="pt-4">
          <BreakdownChart
            title={t("tabs.bySemester")}
            data={semesterData?.data}
            loading={semesterLoading}
          />
        </TabsContent>

        {/* By Year Tab */}
        <TabsContent value="by-year" className="pt-4">
          <BreakdownChart
            title={t("tabs.byYear")}
            data={yearlyData?.data}
            loading={yearlyLoading}
          />
        </TabsContent>

        {/* By Session Tab */}
        <TabsContent value="by-session" className="pt-4">
          <SessionPieChart
            data={sessionData?.data}
            loading={sessionLoading}
          />
        </TabsContent>

        {/* Distribution Tab */}
        <TabsContent value="distribution" className="pt-4">
          <DistributionChart
            data={distributionData?.data}
            loading={distributionLoading}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}
