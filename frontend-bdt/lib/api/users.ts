import { apiClient } from "./client";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  plan: string;
  language: string;
  timezone: string;
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

export async function getProfile(): Promise<UserProfile> {
  const response = await apiClient.get<{ data: UserProfile }>("/users/me");
  return response.data.data;
}

export async function updateProfile(data: {
  name?: string;
  language?: string;
  timezone?: string;
}): Promise<UserProfile> {
  const response = await apiClient.patch<{ data: UserProfile }>(
    "/users/me",
    data,
  );
  return response.data.data;
}

export async function changePassword(data: {
  current_password: string;
  new_password: string;
}): Promise<void> {
  await apiClient.post("/users/change-password", data);
}

export async function deleteAccount(password: string): Promise<void> {
  await apiClient.post("/users/delete-account", { password });
}
