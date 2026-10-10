"use client";

import { AxiosError } from "axios";
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import { useAuthStore } from "@/lib/stores/authStore";

// ---------------------------------------------------------------------------
// Types — mirror of the backend /users endpoints (Bakend app/modules/users)
// ---------------------------------------------------------------------------

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  plan: string;
  language: string;
  timezone: string;
  created_at: string;
  is_active: boolean;
}

export interface ProfileUpdate {
  name?: string;
  language?: string;
  timezone?: string;
}

export interface PasswordChangeRequest {
  current_password: string;
  new_password: string;
}

export interface UserStats {
  total_data_sources: number;
  total_trades: number;
  total_pnl: number;
  win_rate: number; // ratio 0..1 from the backend
  avg_rr_ratio: number | null;
  best_month: number | null;
  worst_month: number | null;
}

interface ApiEnvelope<T> {
  success: boolean;
  data: T;
  message?: string | null;
}

// ---------------------------------------------------------------------------
// Error helper — extracts a human-readable message from an Axios error.
// Handles both the standard ErrorResponse ({ detail: string }) shape and
// FastAPI validation errors ({ detail: [{ msg, loc, ... }] }).
// ---------------------------------------------------------------------------

export function extractApiError(error: unknown): string {
  if (error instanceof AxiosError) {
    const detail = (error.response?.data as { detail?: unknown })?.detail;
    if (typeof detail === "string" && detail.trim()) return detail;
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0] as { msg?: string };
      if (typeof first?.msg === "string" && first.msg.trim()) return first.msg;
    }
    if (error.code === "ECONNABORTED") return "La petición tardó demasiado.";
  }
  if (error instanceof Error && error.message) return error.message;
  return "Ocurrió un error inesperado. Intenta de nuevo.";
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

export async function fetchProfile(): Promise<UserProfile> {
  const response = await apiClient.get<ApiEnvelope<UserProfile>>(
    "/users/profile",
  );
  return response.data.data;
}

export async function updateProfile(data: ProfileUpdate): Promise<UserProfile> {
  const response = await apiClient.put<ApiEnvelope<UserProfile>>(
    "/users/profile",
    data,
  );
  return response.data.data;
}

export async function changePassword(
  data: PasswordChangeRequest,
): Promise<void> {
  await apiClient.put<ApiEnvelope<Record<string, never>>>(
    "/users/password",
    data,
  );
}

export async function fetchStats(): Promise<UserStats> {
  const response = await apiClient.get<ApiEnvelope<UserStats>>("/users/stats");
  return response.data.data;
}

export async function deleteAccount(password: string): Promise<void> {
  await apiClient.delete<ApiEnvelope<Record<string, never>>>("/users/account", {
    data: { password },
  });
}

// ---------------------------------------------------------------------------
// Query hooks
// ---------------------------------------------------------------------------

export const PROFILE_QUERY_KEY = ["users", "profile"];
export const STATS_QUERY_KEY = ["users", "stats"];

export function useProfile() {
  return useQuery({
    queryKey: PROFILE_QUERY_KEY,
    queryFn: fetchProfile,
  });
}

export function useUserStats() {
  return useQuery({
    queryKey: STATS_QUERY_KEY,
    queryFn: fetchStats,
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  const setUser = useAuthStore((s) => s.setUser);

  return useMutation({
    mutationFn: (data: ProfileUpdate) => updateProfile(data),
    onSuccess: (profile) => {
      queryClient.setQueryData(PROFILE_QUERY_KEY, profile);
      // Keep the auth store in sync (name / language / timezone).
      setUser({
        id: profile.id,
        email: profile.email,
        name: profile.name,
        plan: profile.plan,
        language: profile.language,
        timezone: profile.timezone,
      });
    },
  });
}

export function useChangePassword() {
  return useMutation({
    mutationFn: (data: PasswordChangeRequest) => changePassword(data),
  });
}

export function useDeleteAccount() {
  const logout = useAuthStore((s) => s.logout);

  return useMutation({
    mutationFn: (password: string) => deleteAccount(password),
    onSuccess: () => {
      logout();
    },
  });
}
