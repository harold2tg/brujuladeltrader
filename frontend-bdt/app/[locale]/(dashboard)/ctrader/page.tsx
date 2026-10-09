"use client";

import { useEffect } from "react";
import { useTranslations } from "next-intl";
import { useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { PageHeader } from "@/components/layout/PageHeader";
import { CTraderConnectForm } from "@/components/ctrader/CTraderConnectForm";
import { CTraderSyncPanel } from "@/components/ctrader/CTraderSyncPanel";
import { CTraderStatusBadge } from "@/components/ctrader/CTraderStatusBadge";

export default function CTraderPage() {
  const t = useTranslations("ctrader");
  const searchParams = useSearchParams();

  useEffect(() => {
    const connected = searchParams.get("connected");
    const error = searchParams.get("error");

    if (connected === "true") {
      toast.success(t("connectionSuccess"));
      // Clean URL
      window.history.replaceState({}, "", "/es/ctrader");
    } else if (error) {
      toast.error(t("connectionFailed") + `: ${error}`);
      window.history.replaceState({}, "", "/es/ctrader");
    }
  }, [searchParams, t]);

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
