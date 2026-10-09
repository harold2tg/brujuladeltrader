"use client";

import { useTranslations } from "next-intl";
import { PageHeader } from "@/components/layout/PageHeader";
import { DataSourcesList } from "@/components/data-sources/DataSourcesList";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { Card, CardContent } from "@/components/ui/card";
import { useDataSources } from "@/lib/hooks/useDataSources";

export default function DataSourcesPage() {
  const t = useTranslations("dataSources");

  const { data, isLoading, error } = useDataSources();

  return (
    <div className="space-y-6">
      <PageHeader title={t("title")} />

      <Card className="border-border/40">
        <CardContent className="pt-6">
          {isLoading ? (
            <LoadingSpinner className="py-12" />
          ) : error ? (
            <div className="py-12 text-center text-sm text-muted-foreground">
              {t("loadError")}
            </div>
          ) : (
            <DataSourcesList dataSources={data?.data?.items ?? []} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
