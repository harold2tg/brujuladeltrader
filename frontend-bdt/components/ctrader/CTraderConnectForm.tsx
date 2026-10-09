"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Loader2, Plug, Trash2, CheckCircle2, XCircle, ExternalLink } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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
  useAuthorizeCTrader,
} from "@/lib/hooks/useCTrader";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";

const oauthSchema = z.object({
  client_id: z.string().min(1, "Required"),
  client_secret: z.string().min(1, "Required"),
});

type OAuthFormData = z.infer<typeof oauthSchema>;

export function CTraderConnectForm() {
  const t = useTranslations("ctrader");
  const { data: credentials, isLoading } = useCTraderCredentials();
  const deleteMutation = useDeleteCTraderCredentials();
  const authorizeMutation = useAuthorizeCTrader();
  const [showDelete, setShowDelete] = useState(false);

  const hasCredentials = credentials?.has_credentials ?? false;

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<OAuthFormData>({
    resolver: zodResolver(oauthSchema),
  });

  async function onSubmit(data: OAuthFormData) {
    try {
      const result = await authorizeMutation.mutateAsync({
        client_id: data.client_id,
        client_secret: data.client_secret,
        is_demo: false,
      });
      // Redirect to cTrader OAuth
      window.location.href = result.auth_url;
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

  // Not connected — show OAuth form
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
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground/70">
                {t("credentials.clientId")}
              </Label>
              <Input
                placeholder={t("credentials.clientIdPlaceholder")}
                {...register("client_id")}
              />
              {errors.client_id && (
                <p className="text-xs text-destructive">{errors.client_id.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground/70">
                {t("credentials.clientSecret")}
              </Label>
              <Input
                type="password"
                placeholder={t("credentials.clientSecretPlaceholder")}
                {...register("client_secret")}
              />
              {errors.client_secret && (
                <p className="text-xs text-destructive">{errors.client_secret.message}</p>
              )}
            </div>
          </div>

          <Button
            type="submit"
            disabled={authorizeMutation.isPending}
            className="shadow-lg shadow-primary/20"
          >
            {authorizeMutation.isPending ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <ExternalLink className="size-4" />
            )}
            {t("connectCtrader")}
          </Button>

          <p className="text-xs text-muted-foreground">
            {t("oauthHint")}
          </p>
        </form>
      </CardContent>
    </Card>
  );
}
