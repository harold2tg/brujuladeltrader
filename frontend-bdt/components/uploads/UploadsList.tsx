"use client";

import { useTranslations } from "next-intl";
import { Upload } from "lucide-react";
import { EmptyState } from "@/components/shared/EmptyState";
import { UploadStatusCard } from "@/components/uploads/UploadStatusCard";
import type { Upload as UploadType } from "@/lib/api/uploads";

interface UploadsListProps {
  uploads: UploadType[];
  locale?: string;
}

export function UploadsList({ uploads, locale = "es" }: UploadsListProps) {
  const t = useTranslations("uploads");

  if (uploads.length === 0) {
    return (
      <EmptyState
        icon={<Upload />}
        title={t("empty")}
        description={t("emptyHint")}
      />
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {uploads.map((upload) => (
        <UploadStatusCard key={upload.id} upload={upload} locale={locale} />
      ))}
    </div>
  );
}
