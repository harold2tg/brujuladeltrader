"use client";

import { useState } from "react";
import { AxiosError } from "axios";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  extractApiError,
  useUpdateProfile,
  type UserProfile,
} from "@/lib/hooks/useSettings";

const COMMON_TIMEZONES = [
  "UTC",
  "Europe/Madrid",
  "America/Mexico_City",
  "America/Bogota",
  "America/Lima",
  "America/Santiago",
  "America/Argentina/Buenos_Aires",
  "America/Caracas",
  "America/Guayaquil",
  "America/La_Paz",
  "America/Montevideo",
  "America/Sao_Paulo",
  "America/New_York",
  "America/Los_Angeles",
] as const satisfies readonly string[];

const TIMEZONE_LIST: readonly string[] = COMMON_TIMEZONES;

interface ProfileFormProps {
  profile: UserProfile;
}

interface ProfileErrors {
  name?: string;
  timezone?: string;
}

function validate(name: string, timezone: string): ProfileErrors {
  const errors: ProfileErrors = {};
  const trimmed = name.trim();
  if (trimmed.length < 1) {
    errors.name = "El nombre no puede estar vacío.";
  } else if (trimmed.length > 100) {
    errors.name = "El nombre debe tener 100 caracteres o menos.";
  }
  if (!timezone) {
    errors.timezone = "Selecciona una zona horaria.";
  }
  return errors;
}

export function ProfileForm({ profile }: ProfileFormProps) {
  const [name, setName] = useState(profile.name);
  const [language, setLanguage] = useState(profile.language);
  const [timezone, setTimezone] = useState(profile.timezone);
  const [errors, setErrors] = useState<ProfileErrors>({});
  const updateProfile = useUpdateProfile();

  // Local state seeds from the profile query on mount; after a successful
  // save the local values already match the server response, so no effect
  // re-sync is needed.

  // Include the user's current zone even if it isn't in the common list.
  const timezoneOptions = timezone && !TIMEZONE_LIST.includes(timezone)
    ? [timezone, ...TIMEZONE_LIST]
    : TIMEZONE_LIST;

  const isDirty =
    name !== profile.name ||
    language !== profile.language ||
    timezone !== profile.timezone;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const nextErrors = validate(name, timezone);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;

    try {
      await updateProfile.mutateAsync({
        name: name.trim(),
        language,
        timezone,
      });
      toast.success("Perfil actualizado correctamente.");
    } catch (error) {
      const message = extractApiError(error);
      toast.error(message);
      if (error instanceof AxiosError && error.response?.status === 422) {
        setErrors({ name: message });
      }
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Perfil</CardTitle>
        <CardDescription>
          Tu nombre, idioma y zona horaria de trabajo.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <div className="space-y-1.5">
            <Label htmlFor="profile-email">Email</Label>
            <Input
              id="profile-email"
              value={profile.email}
              readOnly
              disabled
              className="bg-input/50 text-muted-foreground"
            />
            <p className="text-xs text-muted-foreground">
              El email no se puede modificar.
            </p>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="profile-name">Nombre</Label>
            <Input
              id="profile-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Tu nombre"
              aria-invalid={Boolean(errors.name)}
              maxLength={120}
            />
            {errors.name && (
              <p className="text-xs text-destructive">{errors.name}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="profile-language">Idioma</Label>
            <Select
              value={language}
              onValueChange={(v) => v && setLanguage(v)}
            >
              <SelectTrigger id="profile-language" className="w-full">
                <SelectValue placeholder="Selecciona un idioma" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="es">Español</SelectItem>
                <SelectItem value="en">English</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="profile-timezone">Zona horaria</Label>
            <Select value={timezone} onValueChange={(v) => v && setTimezone(v)}>
              <SelectTrigger id="profile-timezone" className="w-full">
                <SelectValue placeholder="Selecciona una zona horaria" />
              </SelectTrigger>
              <SelectContent>
                {timezoneOptions.map((tz) => (
                  <SelectItem key={tz} value={tz}>
                    {tz}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.timezone && (
              <p className="text-xs text-destructive">{errors.timezone}</p>
            )}
          </div>

          <div className="flex items-center justify-end gap-3 pt-1">
            {isDirty && (
              <span className="text-xs text-muted-foreground">
                Hay cambios sin guardar
              </span>
            )}
            <Button
              type="submit"
              disabled={!isDirty || updateProfile.isPending}
            >
              {updateProfile.isPending && (
                <Loader2 className="animate-spin" />
              )}
              Guardar cambios
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
