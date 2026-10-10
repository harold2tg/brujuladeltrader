"use client";

import { useMemo, useState } from "react";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import { extractApiError, useChangePassword } from "@/lib/hooks/useSettings";

interface PasswordErrors {
  current_password?: string;
  new_password?: string;
  confirm_new_password?: string;
}

function validatePassword(password: string): string | null {
  if (password.length < 8) {
    return "La contraseña debe tener al menos 8 caracteres.";
  }
  if (!/[A-Z]/.test(password)) {
    return "Debe contener al menos una letra mayúscula.";
  }
  if (!/[a-z]/.test(password)) {
    return "Debe contener al menos una letra minúscula.";
  }
  if (!/\d/.test(password)) {
    return "Debe contener al menos un número.";
  }
  return null;
}

interface Strength {
  score: 0 | 1 | 2 | 3 | 4;
  label: string;
  barClass: string;
  textClass: string;
}

function computeStrength(password: string): Strength {
  if (!password) {
    return { score: 0, label: "", barClass: "bg-border", textClass: "text-muted-foreground" };
  }
  let points = 0;
  if (password.length >= 8) points += 1;
  if (/[A-Z]/.test(password)) points += 1;
  if (/[a-z]/.test(password)) points += 1;
  if (/\d/.test(password)) points += 1;
  if (password.length >= 12 || /[^A-Za-z0-9]/.test(password)) points += 1;

  if (points <= 2) {
    return { score: 1, label: "Débil", barClass: "bg-destructive", textClass: "text-destructive" };
  }
  if (points === 3) {
    return {
      score: 2,
      label: "Aceptable",
      barClass: "bg-warning",
      textClass: "text-warning",
    };
  }
  if (points === 4) {
    return {
      score: 3,
      label: "Buena",
      barClass: "bg-primary",
      textClass: "text-primary",
    };
  }
  return {
    score: 4,
    label: "Excelente",
    barClass: "bg-primary",
    textClass: "text-primary",
  };
}

export function PasswordForm() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [errors, setErrors] = useState<PasswordErrors>({});
  const changePassword = useChangePassword();

  const strength = useMemo(
    () => computeStrength(newPassword),
    [newPassword],
  );

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const nextErrors: PasswordErrors = {};

    if (!currentPassword) {
      nextErrors.current_password = "Introduce tu contraseña actual.";
    }
    const newError = validatePassword(newPassword);
    if (newError) {
      nextErrors.new_password = newError;
    }
    if (!confirmPassword) {
      nextErrors.confirm_new_password = "Confirma la nueva contraseña.";
    } else if (confirmPassword !== newPassword) {
      nextErrors.confirm_new_password = "Las contraseñas no coinciden.";
    }

    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;

    changePassword.mutate(
      { current_password: currentPassword, new_password: newPassword },
      {
        onSuccess: () => {
          setCurrentPassword("");
          setNewPassword("");
          setConfirmPassword("");
          setErrors({});
          toast.success("Contraseña actualizada correctamente.");
        },
        onError: (error) => {
          const message = extractApiError(error);
          toast.error(message);
          if (message.toLowerCase().includes("current password")) {
            setErrors({ current_password: message });
          }
        },
      },
    );
  }

  const fieldErrorClass = "text-xs text-destructive";

  return (
    <Card>
      <CardHeader>
        <CardTitle>Contraseña</CardTitle>
        <CardDescription>
          Mínimo 8 caracteres, con mayúsculas, minúsculas y un número.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <div className="space-y-1.5">
            <Label htmlFor="current-password">Contraseña actual</Label>
            <Input
              id="current-password"
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              autoComplete="current-password"
              aria-invalid={Boolean(errors.current_password)}
            />
            {errors.current_password && (
              <p className={fieldErrorClass}>{errors.current_password}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="new-password">Nueva contraseña</Label>
            <Input
              id="new-password"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              autoComplete="new-password"
              aria-invalid={Boolean(errors.new_password)}
            />
            {newPassword && (
              <div className="space-y-1 pt-0.5">
                <div className="flex gap-1" aria-hidden>
                  {[1, 2, 3, 4].map((segment) => (
                    <div
                      key={segment}
                      className={cn(
                        "h-1 flex-1 rounded-full transition-colors",
                        segment <= strength.score
                          ? strength.barClass
                          : "bg-border",
                      )}
                    />
                  ))}
                </div>
                <p className={cn("text-xs", strength.textClass)}>
                  Fortaleza: {strength.label}
                </p>
              </div>
            )}
            {errors.new_password && (
              <p className={fieldErrorClass}>{errors.new_password}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="confirm-password">Confirmar nueva contraseña</Label>
            <Input
              id="confirm-password"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              autoComplete="new-password"
              aria-invalid={Boolean(errors.confirm_new_password)}
            />
            {errors.confirm_new_password && (
              <p className={fieldErrorClass}>{errors.confirm_new_password}</p>
            )}
          </div>

          <div className="flex justify-end pt-1">
            <Button
              type="submit"
              variant="outline"
              disabled={
                changePassword.isPending ||
                !currentPassword ||
                !newPassword ||
                !confirmPassword
              }
            >
              {changePassword.isPending && <Loader2 className="animate-spin" />}
              Cambiar contraseña
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
