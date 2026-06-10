"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { deleteUpload } from "@/lib/api/uploads";
import type { Upload } from "@/lib/api/uploads";
import { formatCurrency, formatDate } from "@/lib/utils/formatters";

interface UploadStatusCardProps {
  upload: Upload;
  locale?: string;
}

const statusConfig: Record<
  string,
  { labelKey: string; variant: "default" | "secondary" | "destructive" | "outline" }
> = {
  pending: { labelKey: "uploads.status.pending", variant: "secondary" },
  processing: { labelKey: "uploads.status.processing", variant: "default" },
  ready: { labelKey: "uploads.status.ready", variant: "default" },
  error: { labelKey: "uploads.status.error", variant: "destructive" },
};

export function UploadStatusCard({
  upload,
  locale = "es",
}: UploadStatusCardProps) {
  const t = useTranslations();
  const queryClient = useQueryClient();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  const deleteMutation = useMutation({
    mutationFn: () => deleteUpload(upload.id),
    onSuccess: () => {
      toast.success(t("uploads.deleteSuccess"));
      queryClient.invalidateQueries({ queryKey: ["uploads"] });
    },
    onError: (error: Error) => {
      toast.error(t("uploads.deleteError") + error.message);
    },
  });

  const status = statusConfig[upload.status] || statusConfig.pending;

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between gap-2">
            <CardTitle className="truncate text-sm">
              {upload.original_name}
            </CardTitle>
            <Badge variant={status.variant}>{t(status.labelKey)}</Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="grid grid-cols-2 gap-2 text-xs">
            {upload.total_trades != null && (
              <div>
                <span className="text-muted-foreground">
                  {t("uploads.trades")}
                </span>{" "}
                <span className="font-medium">{upload.total_trades}</span>
              </div>
            )}
            {upload.net_pnl != null && (
              <div>
                <span className="text-muted-foreground">PnL</span>{" "}
                <span
                  className={
                    upload.net_pnl >= 0
                      ? "font-medium text-green-600"
                      : "font-medium text-red-600"
                  }
                >
                  {formatCurrency(upload.net_pnl, locale)}
                </span>
              </div>
            )}
          </div>
          <div className="flex items-center justify-between pt-1">
            <span className="text-xs text-muted-foreground">
              {formatDate(upload.created_at, locale)}
            </span>
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={() => setDeleteDialogOpen(true)}
              disabled={deleteMutation.isPending}
            >
              <Trash2 className="size-4 text-muted-foreground hover:text-destructive" />
            </Button>
          </div>
        </CardContent>
      </Card>

      <ConfirmDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        title={t("uploads.deleteTitle")}
        description={t("uploads.deleteConfirm")}
        onConfirm={() => deleteMutation.mutate()}
        confirmText={t("common.delete")}
        cancelText={t("common.cancel")}
        variant="destructive"
      />
    </>
  );
}
