"use client";

import { useTranslations } from "next-intl";
import { Database } from "lucide-react";
import { EmptyState } from "@/components/shared/EmptyState";
import { DataSourceStatusCard } from "@/components/data-sources/DataSourceStatusCard";
import type { DataSource } from "@/lib/types/data-source";

interface DataSourcesListProps {
  dataSources: DataSource[];
  locale?: string;
}

export function DataSourcesList({
  dataSources,
  locale = "es",
}: DataSourcesListProps) {
  const t = useTranslations("dataSources");

  if (dataSources.length === 0) {
    return (
      <EmptyState
        icon={<Database />}
        title={t("empty")}
        description={t("emptyHint")}
      />
    );
  }

  return (
    <div className="grid gap-6 min-w-0 sm:grid-cols-2 lg:grid-cols-3">
      {dataSources.map((ds) => (
        <DataSourceStatusCard
          key={ds.id}
          dataSource={ds}
          locale={locale}
        />
      ))}
    </div>
  );
}
