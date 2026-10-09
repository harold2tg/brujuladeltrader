"use client";

import { useTranslations } from "next-intl";
import { BarChart3, Database } from "lucide-react";
import Link from "next/link";
import { PageHeader } from "@/components/layout/PageHeader";
import { buttonVariants } from "@/components/ui/button";
import { EmptyState } from "@/components/shared/EmptyState";
import { useDataSources } from "@/lib/hooks/useDataSources";
import { Card, CardContent } from "@/components/ui/card";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";

export default function AnalyticsPage() {
  const t = useTranslations("analytics");
  const { data: dataSourcesData, isLoading } = useDataSources();

  const dataSources = dataSourcesData?.data?.items ?? [];

  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader title={t("title")} />
        <LoadingSpinner className="py-12" />
      </div>
    );
  }

  if (dataSources.length === 0) {
    return (
      <div className="space-y-6">
        <PageHeader title={t("title")} />
        <EmptyState
          icon={<Database />}
          title={t("noDataSources")}
          description={t("noDataSourcesHint")}
          action={
            <Link href="/data-sources" className={buttonVariants()}>
              {t("goToDataSources")}
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
        description={t("selectDataSource")}
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {dataSources.map((ds) => (
          <Link key={ds.id} href={`/analytics/${ds.id}`}>
            <Card className="group relative overflow-hidden border-border/40 transition-all duration-300 hover:border-primary/30 hover:shadow-lg hover:shadow-primary/5 cursor-pointer">
              <div className="absolute inset-0 bg-gradient-to-br from-primary/[0.03] to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
              <CardContent className="relative p-5">
                <div className="flex items-center gap-4">
                  <div className="flex size-10 items-center justify-center rounded-xl bg-primary/10 transition-all duration-300 group-hover:bg-primary/15 group-hover:shadow-md group-hover:shadow-primary/10">
                    <BarChart3 className="size-5 text-primary" />
                  </div>
                  <div>
                    <p className="font-semibold">{ds.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {ds.sync_status === "ready" ? (
                        <>
                          {ds.trade_count} trades
                          {ds.last_synced_at && (
                            <> · {new Date(ds.last_synced_at).toLocaleDateString()}</>
                          )}
                        </>
                      ) : (
                        <span className="text-amber-400">
                          {ds.sync_status === "syncing" ? "Syncing..." : "Pending"}
                        </span>
                      )}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
