"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Trash2, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { deleteDataSource, syncDataSource } from "@/lib/api/dataSources";
import type { DataSource, SyncStatus } from "@/lib/types/data-source";
import { formatDate } from "@/lib/utils/formatters";

interface DataSourceStatusCardProps {
  dataSource: DataSource;
  locale?: string;
}

const syncStatusConfig: Record<
  SyncStatus,
  { labelKey: string; variant: "default" | "secondary" | "destructive" | "outline" }
> = {
  pending: { labelKey: "dataSources.status.pending", variant: "secondary" },
  syncing: { labelKey: "dataSources.status.syncing", variant: "default" },
  ready: { labelKey: "dataSources.status.ready", variant: "outline" },
  error: { labelKey: "dataSources.status.error", variant: "destructive" },
};

export function DataSourceStatusCard({
  dataSource,
  locale = "es",
}: DataSourceStatusCardProps) {
  const t = useTranslations();
  const queryClient = useQueryClient();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  const deleteMutation = useMutation({
    mutationFn: () => deleteDataSource(dataSource.id),
    onSuccess: () => {
      toast.success(t("dataSources.deleteSuccess"));
      queryClient.invalidateQueries({ queryKey: ["data-sources"] });
    },
    onError: (error: Error) => {
      toast.error(t("dataSources.deleteError") + error.message);
    },
  });

  const syncMutation = useMutation({
    mutationFn: () => syncDataSource(dataSource.id),
    onSuccess: () => {
      toast.success(t("dataSources.syncSuccess"));
      queryClient.invalidateQueries({ queryKey: ["data-sources"] });
    },
    onError: (error: Error) => {
      toast.error(t("dataSources.syncError") + error.message);
    },
  });

  const status = syncStatusConfig[dataSource.sync_status] || syncStatusConfig.pending;

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0 flex-1">
              <CardTitle className="truncate text-sm font-semibold">
                {dataSource.name}
              </CardTitle>
              <p className="mt-0.5 truncate text-xs text-muted-foreground num-tabular">
                {dataSource.broker} · {dataSource.broker_account_id}
              </p>
            </div>
            <Badge variant={status.variant} className="shrink-0">
              {t(status.labelKey)}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="min-w-0">
              <span className="text-muted-foreground">
                {t("dataSources.trades")}
              </span>{" "}
              <span className="font-medium text-foreground num-tabular font-mono">
                {dataSource.trade_count}
              </span>
            </div>
            {dataSource.last_synced_at && (
              <div className="min-w-0">
                <span className="text-muted-foreground">
                  {t("dataSources.lastSync")}
                </span>{" "}
                <span className="font-medium text-foreground num-tabular">
                  {formatDate(dataSource.last_synced_at, locale)}
                </span>
              </div>
            )}
          </div>
          <div className="flex items-center justify-between gap-2 border-t border-border/60 pt-2">
            <span className="min-w-0 truncate text-xs text-muted-foreground num-tabular">
              {formatDate(dataSource.created_at, locale)}
            </span>
            <div className="flex shrink-0 items-center gap-1">
              <Button
                variant="ghost"
                size="icon-sm"
                className="text-muted-foreground hover:text-foreground"
                onClick={() => syncMutation.mutate()}
                disabled={syncMutation.isPending || dataSource.sync_status === "syncing"}
                title={t("dataSources.sync")}
              >
                <RefreshCw
                  className={`size-4 transition-colors duration-150 ${
                    syncMutation.isPending ? "animate-spin text-primary" : ""
                  }`}
                />
              </Button>
              <Button
                variant="ghost"
                size="icon-sm"
                className="text-muted-foreground hover:text-foreground"
                onClick={() => setDeleteDialogOpen(true)}
                disabled={deleteMutation.isPending}
              >
                <Trash2 className="size-4 transition-colors duration-150 group-hover/button:text-destructive" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <ConfirmDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        title={t("dataSources.deleteTitle")}
        description={t("dataSources.deleteConfirm")}
        onConfirm={() => deleteMutation.mutate()}
        confirmText={t("common.delete")}
        cancelText={t("common.cancel")}
        variant="destructive"
      />
    </>
  );
}
