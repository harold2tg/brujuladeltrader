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
            <Card className="transition-colors hover:bg-muted cursor-pointer">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <BarChart3 className="size-5 text-muted-foreground" />
                  <div>
                    <p className="font-medium">{upload.original_name}</p>
                    <p className="text-sm text-muted-foreground">
                      {upload.status === "ready" ? (
                        <>
                          {upload.total_trades ?? 0} trades •{" "}
                          {upload.net_pnl !== undefined
                            ? `$${upload.net_pnl.toFixed(2)}`
                            : "Pendiente"}
                        </>
                      ) : (
                        <span className="text-yellow-600">Procesando...</span>
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
