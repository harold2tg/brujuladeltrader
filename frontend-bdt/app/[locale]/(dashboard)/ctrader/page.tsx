"use client";

import { useTranslations } from "next-intl";
import { PageHeader } from "@/components/layout/PageHeader";
import { CTraderConnectForm } from "@/components/ctrader/CTraderConnectForm";
import { CTraderSyncPanel } from "@/components/ctrader/CTraderSyncPanel";
import { CTraderStatusBadge } from "@/components/ctrader/CTraderStatusBadge";

export default function CTraderPage() {
  const t = useTranslations("ctrader");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <PageHeader title={t("title")} description={t("description")} />
        <CTraderStatusBadge />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Left: Credentials */}
        <CTraderConnectForm />

        {/* Right: Sync */}
        <CTraderSyncPanel />
      </div>
    </div>
  );
}
