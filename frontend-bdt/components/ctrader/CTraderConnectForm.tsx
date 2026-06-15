"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Loader2, Plug, Trash2, CheckCircle2, XCircle } from "lucide-react";

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
  useSaveCTraderCredentials,
  useDeleteCTraderCredentials,
  useTestCTraderConnection,
} from "@/lib/hooks/useCTrader";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";

const credentialSchema = z.object({
  client_id: z.string().min(1, "Required"),
  client_secret: z.string().min(1, "Required"),
  access_token: z.string().min(1, "Required"),
  account_id: z.string().min(1, "Required"),
});

type CredentialFormData = z.infer<typeof credentialSchema>;

export function CTraderConnectForm() {
  const t = useTranslations("ctrader");
  const { data: credentials, isLoading } = useCTraderCredentials();
  const saveMutation = useSaveCTraderCredentials();
  const deleteMutation = useDeleteCTraderCredentials();
  const testMutation = useTestCTraderConnection();
  const [showDelete, setShowDelete] = useState(false);

  const hasCredentials = credentials?.has_credentials ?? false;

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<CredentialFormData>({
    resolver: zodResolver(credentialSchema),
  });

  async function onSubmit(data: CredentialFormData) {
    try {
      const result = await saveMutation.mutateAsync(data);
      if (result.connected) {
        toast.success(t("connectionSuccess"));
      } else {
        toast.warning(t("saved") + " — " + t("connectionFailed"));
      }
      reset();
    } catch {
      toast.error(t("saveError"));
    }
  }

  async function handleTest() {
    try {
      const result = await testMutation.mutateAsync();
      if (result.connected) {
        toast.success(`${t("connectionSuccess")} (${result.latency_ms}ms)`);
      } else {
        toast.error(result.error || t("connectionFailed"));
      }
    } catch {
      toast.error(t("connectionFailed"));
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
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleTest}
                disabled={testMutation.isPending}
              >
                {testMutation.isPending ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <Plug className="size-4" />
                )}
                {t("testConnection")}
              </Button>
              <Button
                variant="destructive"
                size="sm"
                onClick={() => setShowDelete(true)}
              >
                <Trash2 className="size-4" />
              </Button>
            </div>
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

  // Not connected — show form
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
            <div className="space-y-2">
              <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground/70">
                {t("credentials.accessToken")}
              </Label>
              <Input
                type="password"
                placeholder={t("credentials.accessTokenPlaceholder")}
                {...register("access_token")}
              />
              {errors.access_token && (
                <p className="text-xs text-destructive">{errors.access_token.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground/70">
                {t("credentials.accountId")}
              </Label>
              <Input
                placeholder={t("credentials.accountIdPlaceholder")}
                {...register("account_id")}
              />
              {errors.account_id && (
                <p className="text-xs text-destructive">{errors.account_id.message}</p>
              )}
            </div>
          </div>

          <Button
            type="submit"
            disabled={saveMutation.isPending}
            className="shadow-lg shadow-primary/20"
          >
            {saveMutation.isPending ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Plug className="size-4" />
            )}
            {t("save")}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
