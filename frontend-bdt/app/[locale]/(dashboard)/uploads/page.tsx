"use client";

import { useTranslations } from "next-intl";
import { useQuery } from "@tanstack/react-query";
import { getUploads } from "@/lib/api/uploads";
import { PageHeader } from "@/components/layout/PageHeader";
import { UploadDropzone } from "@/components/uploads/UploadDropzone";
import { UploadsList } from "@/components/uploads/UploadsList";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { Card, CardContent } from "@/components/ui/card";

export default function UploadsPage() {
  const t = useTranslations("uploads");

  const { data, isLoading, error } = useQuery({
    queryKey: ["uploads"],
    queryFn: getUploads,
  });

  return (
    <div className="space-y-6">
      <PageHeader title={t("title")} />

      <UploadDropzone />

      <Card>
        <CardContent>
          {isLoading ? (
            <LoadingSpinner className="py-12" />
          ) : error ? (
            <div className="py-12 text-center text-sm text-muted-foreground">
              {t("loadError")}
            </div>
          ) : (
            <UploadsList uploads={data?.data?.items ?? []} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
