"use client";

import { useTranslations } from "next-intl";
import { BarChart3, Upload } from "lucide-react";
import Link from "next/link";
import { PageHeader } from "@/components/layout/PageHeader";
import { buttonVariants } from "@/components/ui/button";
import { EmptyState } from "@/components/shared/EmptyState";
import { useUploads } from "@/lib/hooks/useUploads";
import { Card, CardContent } from "@/components/ui/card";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";

export default function AnalyticsPage() {
  const t = useTranslations("analytics");
  const { data: uploadsData, isLoading } = useUploads();

  const uploads = uploadsData?.data?.items ?? [];

  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader title={t("title")} />
        <LoadingSpinner className="py-12" />
      </div>
    );
  }

  if (uploads.length === 0) {
    return (
      <div className="space-y-6">
        <PageHeader title={t("title")} />
        <EmptyState
          icon={<Upload />}
          title={t("noUploads")}
          description={t("noUploadsHint")}
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
      <PageHeader
        title={t("title")}
        description={t("selectUpload")}
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {uploads.map((upload) => (
          <Link key={upload.id} href={`/analytics/${upload.id}`}>
            <Card className="group relative overflow-hidden border-border/40 transition-all duration-300 hover:border-primary/30 hover:shadow-lg hover:shadow-primary/5 cursor-pointer">
              <div className="absolute inset-0 bg-gradient-to-br from-primary/[0.03] to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
              <CardContent className="relative p-5">
                <div className="flex items-center gap-4">
                  <div className="flex size-10 items-center justify-center rounded-xl bg-primary/10 transition-all duration-300 group-hover:bg-primary/15 group-hover:shadow-md group-hover:shadow-primary/10">
                    <BarChart3 className="size-5 text-primary" />
                  </div>
                  <div>
                    <p className="font-semibold">{upload.original_name}</p>
                    <p className="text-sm text-muted-foreground">
                      {upload.status === "ready" ? (
                        <>
                          {upload.total_trades ?? 0} trades •{" "}
                          {upload.net_pnl !== undefined ? (
                            <span
                              className={
                                upload.net_pnl >= 0
                                  ? "text-emerald-400"
                                  : "text-red-400"
                              }
                            >
                              ${upload.net_pnl.toFixed(2)}
                            </span>
                          ) : (
                            "Pendiente"
                          )}
                        </>
                      ) : (
                        <span className="text-amber-400">Procesando...</span>
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
