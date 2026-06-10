"use client";

import { useTranslations } from "next-intl";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent } from "@/components/ui/card";

export default function DashboardPage() {
  const t = useTranslations("dashboard");

  return (
    <div className="space-y-6">
      <PageHeader title={t("title")} />

      <Card>
        <CardContent className="py-12 text-center text-muted-foreground">
          {t("placeholder")}
        </CardContent>
      </Card>
    </div>
  );
}
