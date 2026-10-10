"use client";

import { useState } from "react";
import { AlertTriangle } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ProfileForm } from "@/components/settings/ProfileForm";
import { PasswordForm } from "@/components/settings/PasswordForm";
import { StatsCard } from "@/components/settings/StatsCard";
import { DeleteAccountDialog } from "@/components/settings/DeleteAccountDialog";
import { extractApiError, useProfile, useUserStats } from "@/lib/hooks/useSettings";

function SettingsSkeleton() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-48" />
          <Skeleton className="h-4 w-64" />
        </CardHeader>
        <CardContent className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-14 rounded-lg" />
          ))}
        </CardContent>
      </Card>
      <div className="grid gap-6 lg:grid-cols-2">
        <Skeleton className="h-96 rounded-xl" />
        <Skeleton className="h-96 rounded-xl" />
      </div>
    </div>
  );
}

function SettingsError({ message }: { message: string }) {
  return (
    <Card className="ring-destructive/30">
      <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
        <div className="flex size-10 items-center justify-center rounded-xl bg-destructive/10 ring-1 ring-destructive/20">
          <AlertTriangle className="size-5 text-destructive" />
        </div>
        <div className="space-y-1">
          <p className="text-sm font-medium text-foreground">
            No se pudo cargar la configuración
          </p>
          <p className="text-sm text-muted-foreground">{message}</p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => window.location.reload()}
        >
          Reintentar
        </Button>
      </CardContent>
    </Card>
  );
}

export default function SettingsPage() {
  const [deleteOpen, setDeleteOpen] = useState(false);
  const profileQuery = useProfile();
  const statsQuery = useUserStats();

  const isLoading = profileQuery.isLoading || statsQuery.isLoading;
  const error = profileQuery.error ?? statsQuery.error;
  // Forms require the profile; a stats-only failure degrades gracefully below.
  const profile = profileQuery.data;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-2xl font-semibold text-foreground">
          Configuración
        </h1>
        <p className="text-sm text-muted-foreground">
          Gestiona tu perfil, seguridad y cuenta.
        </p>
      </div>

      {isLoading && <SettingsSkeleton />}

      {!isLoading && error && !profile && (
        <SettingsError message={extractApiError(error)} />
      )}

      {!isLoading && profile && (
        <>
          {statsQuery.data ? (
            <StatsCard stats={statsQuery.data} />
          ) : statsQuery.error ? (
            <p className="text-xs text-muted-foreground">
              No se pudieron cargar las estadísticas en este momento.
            </p>
          ) : (
            <Skeleton className="h-32 rounded-xl" />
          )}

          <div className="grid gap-6 lg:grid-cols-2">
            <ProfileForm profile={profile} />
            <PasswordForm />
          </div>

          <Card className="ring-destructive/20">
            <CardHeader>
              <CardTitle className="text-destructive">Zona de peligro</CardTitle>
              <CardDescription>
                Elimina tu cuenta y todos tus datos de forma permanente.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="destructive" onClick={() => setDeleteOpen(true)}>
                Eliminar cuenta
              </Button>
            </CardContent>
          </Card>

          <DeleteAccountDialog
            open={deleteOpen}
            onOpenChange={setDeleteOpen}
          />
        </>
      )}
    </div>
  );
}
