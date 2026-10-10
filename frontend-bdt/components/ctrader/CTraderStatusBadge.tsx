"use client";

import { useTranslations } from "next-intl";
import { CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useCTraderCredentials } from "@/lib/hooks/useCTrader";

export function CTraderStatusBadge() {
  const t = useTranslations("ctrader");
  const { data: credentials, isLoading } = useCTraderCredentials();

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground num-tabular">
        <Loader2 className="size-3.5 animate-spin" />
        <span>{t("common.loading")}</span>
      </div>
    );
  }

  const isConnected = credentials?.has_credentials ?? false;

  return (
    <div
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium transition-colors duration-150 ease-out",
        isConnected
          ? "bg-primary/10 text-primary ring-1 ring-primary/25"
          : "bg-elevated text-muted-foreground ring-1 ring-border",
      )}
    >
      {isConnected ? (
        <CheckCircle2 className="size-3" />
      ) : (
        <XCircle className="size-3" />
      )}
      {isConnected ? t("connected") : t("notConnected")}
    </div>
  );
}
