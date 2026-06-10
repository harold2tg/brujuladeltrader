import { apiClient } from "./client";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface User {
  id: string;
  email: string;
  name: string;
  plan: string;
  language: string;
  timezone: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
}

export interface AuthResponse {
  success: boolean;
  data: {
    user: User;
    access_token: string;
    refresh_token: string;
  };
}

export interface RefreshTokenResponse {
  access_token: string;
}

export interface GetMeResponse {
  user: User;
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

export async function login(data: LoginRequest): Promise<AuthResponse> {
  const response = await apiClient.post<AuthResponse>("/auth/login", data);
  return response.data;
}

export async function register(data: RegisterRequest): Promise<AuthResponse> {
  const response = await apiClient.post<AuthResponse>("/auth/register", data);
  return response.data;
}

export async function refreshToken(
  refreshToken: string,
): Promise<RefreshTokenResponse> {
  const response = await apiClient.post<RefreshTokenResponse>(
    "/auth/refresh",
    { refresh_token: refreshToken },
  );
  return response.data;
}

export async function getMe(): Promise<GetMeResponse> {
  const response = await apiClient.get<GetMeResponse>("/auth/me");
  return response.data;
}
