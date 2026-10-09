"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import {
  Loader2,
  Trash2,
  CheckCircle2,
  XCircle,
  ExternalLink,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  useCTraderCredentials,
  useDeleteCTraderCredentials,
  useCTraderAuthUrl,
} from "@/lib/hooks/useCTrader";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";

export function CTraderConnectForm() {
  const t = useTranslations("ctrader");
  const { data: credentials, isLoading, refetch } = useCTraderCredentials();
  const deleteMutation = useDeleteCTraderCredentials();
  const authUrlMutation = useCTraderAuthUrl();
  const [showDelete, setShowDelete] = useState(false);
  const popupRef = useRef<Window | null>(null);

  const hasCredentials = credentials?.has_credentials ?? false;

  // Listen for postMessage from the OAuth callback popup
  const handleMessage = useCallback(
    (event: MessageEvent) => {
      // Accept messages from the backend (where the callback runs)
      const backendUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";
      const backendOrigin = new URL(backendUrl).origin;
      if (event.origin !== backendOrigin) return;
      if (event.data?.type !== "ctrader-oauth") return;

      if (event.data.status === "success") {
        toast.success(t("connectionSuccess"));
        refetch();
      } else {
        toast.error(t("connectionFailed") + `: ${event.data.error || "unknown"}`);
      }

      // Close popup reference
      if (popupRef.current && !popupRef.current.closed) {
        popupRef.current.close();
      }
      popupRef.current = null;
    },
    [t, refetch],
  );

  useEffect(() => {
    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, [handleMessage]);

  async function handleConnect() {
    try {
      const result = await authUrlMutation.mutateAsync();

      // Open popup window for OAuth
      const width = 600;
      const height = 700;
      const left = window.screenX + (window.outerWidth - width) / 2;
      const top = window.screenY + (window.outerHeight - height) / 2;
      popupRef.current = window.open(
        result.auth_url,
        "ctrader-oauth",
        `width=${width},height=${height},left=${left},top=${top},popup=1`,
      );
    } catch {
      toast.error(t("saveError"));
    }
  }

  function handleDelete() {
    if (!credentials?.id) return;
    deleteMutation.mutate(credentials.id, {
      onSuccess: () => {
        toast.success(t("deleted"));
        setShowDelete(false);
      },
    });
  }

  if (isLoading) {
    return (
      <Card className="border-border/40">
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="size-6 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  // Connected state
  if (hasCredentials) {
    return (
      <Card className="border-border/40">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex size-10 items-center justify-center rounded-xl bg-emerald-500/10">
                <CheckCircle2 className="size-5 text-emerald-400" />
              </div>
              <div>
                <CardTitle className="text-base">{t("connected")}</CardTitle>
                <CardDescription>
                  {credentials?.account_name && (
                    <span>{credentials.account_name}</span>
                  )}
                  {credentials?.broker_name && (
                    <span> · {credentials.broker_name}</span>
                  )}
                  {credentials?.is_demo !== undefined && (
                    <span className="ml-2">
                      ({credentials.is_demo ? t("account.demo") : t("account.live")})
                    </span>
                  )}
                </CardDescription>
              </div>
            </div>
            <Button
              variant="destructive"
              size="sm"
              onClick={() => setShowDelete(true)}
            >
              <Trash2 className="size-4" />
            </Button>
          </div>
        </CardHeader>

        <ConfirmDialog
          open={showDelete}
          onOpenChange={setShowDelete}
          title={t("deleteTitle")}
          description={t("deleteConfirm")}
          onConfirm={handleDelete}
          confirmText={t("disconnect")}
          cancelText="Cancelar"
          variant="destructive"
        />
      </Card>
    );
  }

  // Not connected — show one-click connect button
  return (
    <Card className="border-border/40">
      <CardHeader>
        <div className="flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-xl bg-primary/10">
            <XCircle className="size-5 text-muted-foreground" />
          </div>
          <div>
            <CardTitle className="text-base">{t("notConnected")}</CardTitle>
            <CardDescription>{t("description")}</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <Button
          onClick={handleConnect}
          disabled={authUrlMutation.isPending}
          className="shadow-lg shadow-primary/20"
        >
          {authUrlMutation.isPending ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <ExternalLink className="size-4" />
          )}
          {t("connectCtrader")}
        </Button>
        <p className="mt-3 text-xs text-muted-foreground">
          {t("oauthHint")}
        </p>
      </CardContent>
    </Card>
  );
}
