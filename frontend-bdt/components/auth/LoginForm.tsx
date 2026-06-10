"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { Loader2Icon } from "lucide-react";

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
import { login } from "@/lib/api/auth";
import { useAuthStore } from "@/lib/stores/authStore";
import { loginSchema, type LoginFormData } from "@/lib/validations/authSchemas";

export function LoginForm() {
  const t = useTranslations("auth.login");
  const router = useRouter();
  const authLogin = useAuthStore((s) => s.login);
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  async function onSubmit(data: LoginFormData) {
    setIsLoading(true);
    try {
      const response = await login(data);
      authLogin(
        response.data.user,
        response.data.access_token,
        response.data.refresh_token,
      );
      toast.success("Login successful");
      router.push("/dashboard");
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Login failed. Please try again.";
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <Card>
      <CardHeader className="text-center">
        <CardTitle className="text-xl">{t("title")}</CardTitle>
        <CardDescription>
          {t("noAccount")}{" "}
          <Link href="/register" className="text-primary underline underline-offset-4 hover:text-primary/80">
            {t("register")}
          </Link>
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Email */}
          <div className="space-y-2">
            <Label htmlFor="email">{t("email")}</Label>
            <Input
              id="email"
              type="email"
              placeholder="you@example.com"
              disabled={isLoading}
              aria-invalid={!!errors.email}
              {...register("email")}
            />
            {errors.email && (
              <p className="text-xs text-destructive">{errors.email.message}</p>
            )}
          </div>

          {/* Password */}
          <div className="space-y-2">
            <Label htmlFor="password">{t("password")}</Label>
            <Input
              id="password"
              type="password"
              placeholder="••••••••"
              disabled={isLoading}
              aria-invalid={!!errors.password}
              {...register("password")}
            />
            {errors.password && (
              <p className="text-xs text-destructive">
                {errors.password.message}
              </p>
            )}
          </div>

          {/* Submit */}
          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? (
              <>
                <Loader2Icon className="size-4 animate-spin" />
                {t("title")}...
              </>
            ) : (
              t("submit")
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
