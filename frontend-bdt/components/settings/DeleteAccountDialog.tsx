"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { AlertTriangle, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { extractApiError, useDeleteAccount } from "@/lib/hooks/useSettings";

interface DeleteAccountDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function DeleteAccountDialog({
  open,
  onOpenChange,
}: DeleteAccountDialogProps) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const deleteAccount = useDeleteAccount();
  const router = useRouter();

  function handleClose(nextOpen: boolean) {
    if (deleteAccount.isPending) return;
    if (!nextOpen) {
      setPassword("");
      setError(null);
    }
    onOpenChange(nextOpen);
  }

  function handleConfirm(e: React.FormEvent) {
    e.preventDefault();
    if (!password) {
      setError("Introduce tu contraseña para confirmar.");
      return;
    }

    deleteAccount.mutate(password, {
      onSuccess: () => {
        toast.success("Tu cuenta ha sido eliminada.");
        onOpenChange(false);
        router.push("/");
      },
      onError: (err) => {
        const message = extractApiError(err);
        toast.error(message);
        setError(message);
      },
    });
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent>
        <DialogHeader>
          <div className="flex items-start gap-3">
            <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-destructive/10 ring-1 ring-destructive/20">
              <AlertTriangle className="size-4.5 text-destructive" />
            </div>
            <div className="space-y-1">
              <DialogTitle>Eliminar cuenta</DialogTitle>
              <DialogDescription>
                Esta acción es permanente. Se eliminarán tu perfil, tus fuentes
                de datos y todas tus operaciones. No hay forma de deshacerla.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <form onSubmit={handleConfirm} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="delete-account-password">
              Confirma con tu contraseña
            </Label>
            <Input
              id="delete-account-password"
              type="password"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                setError(null);
              }}
              autoComplete="current-password"
              placeholder="Contraseña actual"
              aria-invalid={Boolean(error)}
            />
            {error && <p className="text-xs text-destructive">{error}</p>}
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => handleClose(false)}
              disabled={deleteAccount.isPending}
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              variant="destructive"
              disabled={deleteAccount.isPending || !password}
            >
              {deleteAccount.isPending && <Loader2 className="animate-spin" />}
              Eliminar mi cuenta
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
