"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { Loader2, RefreshCw, Calendar, CheckCircle2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import {
  useCTraderCredentials,
  useStartCTraderSync,
  useCTraderSyncStatus,
} from "@/lib/hooks/useCTrader";

export function CTraderSyncPanel() {
  const t = useTranslations("ctrader.sync");
  const { data: credentials } = useCTraderCredentials();
  const startSync = useStartCTraderSync();
  const [jobId, setJobId] = useState<string | null>(null);
  const [mode, setMode] = useState<string>("month");
  const [date, setDate] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
  });

  const { data: syncStatus } = useCTraderSyncStatus(jobId);
  const hasCredentials = credentials?.has_credentials ?? false;
  const isSyncing = syncStatus?.status === "processing" || syncStatus?.status === "pending";
  const syncComplete = syncStatus?.status === "ready";

  async function handleSync() {
    if (!hasCredentials) {
      toast.error(t("noCredentials"));
      return;
    }

    try {
      const result = await startSync.mutateAsync({ mode, date });
      setJobId(result.job_id);
      toast.info(t("syncing"));
    } catch {
      toast.error(t("error"));
    }
  }

  return (
    <Card className="border-border/40">
      <CardHeader>
        <div className="flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-xl bg-primary/10">
            <RefreshCw className="size-5 text-primary" />
          </div>
          <div>
            <CardTitle className="text-base">{t("title")}</CardTitle>
            <CardDescription>{t("description")}</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        {/* Mode selector */}
        <div className="space-y-2">
          <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground/70">
            {t("mode")}
          </Label>
          <Select value={mode} onValueChange={(v) => v && setMode(v)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="day">{t("day")}</SelectItem>
              <SelectItem value="month">{t("month")}</SelectItem>
              <SelectItem value="year">{t("year")}</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Date picker */}
        <div className="space-y-2">
          <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground/70">
            {t("date")}
          </Label>
          <div className="relative">
            <Calendar className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        {/* Sync button */}
        <Button
          onClick={handleSync}
          disabled={!hasCredentials || startSync.isPending || isSyncing}
          className="w-full shadow-lg shadow-primary/20"
        >
          {startSync.isPending || isSyncing ? (
            <Loader2 className="size-4 animate-spin" />
          ) : syncComplete ? (
            <CheckCircle2 className="size-4" />
          ) : (
            <RefreshCw className="size-4" />
          )}
          {isSyncing ? t("syncing") : syncComplete ? t("success") : t("start")}
        </Button>

        {/* Sync status */}
        {syncStatus && (
          <div className="rounded-xl bg-muted/30 p-4">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Status</span>
              <span className="font-medium capitalize">{syncStatus.status}</span>
            </div>
            {syncStatus.progress_pct !== undefined && syncStatus.progress_pct > 0 && (
              <div className="mt-2">
                <div className="h-1.5 overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full bg-primary transition-all duration-500"
                    style={{ width: `${syncStatus.progress_pct}%` }}
                  />
                </div>
                <p className="mt-1 text-right text-xs text-muted-foreground">
                  {Math.round(syncStatus.progress_pct)}%
                </p>
              </div>
            )}
            {syncStatus.trades_imported !== undefined && syncStatus.trades_imported > 0 && (
              <p className="mt-2 text-sm text-emerald-400">
                {t("successDetail", { count: syncStatus.trades_imported })}
              </p>
            )}
            {syncStatus.error && (
              <p className="mt-2 text-sm text-red-400">{syncStatus.error}</p>
            )}
          </div>
        )}

        {/* No credentials warning */}
        {!hasCredentials && (
          <p className="text-center text-sm text-muted-foreground">
            {t("noCredentials")}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
