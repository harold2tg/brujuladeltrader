import { apiClient } from "./client";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface AlertRule {
  id: string;
  alert_type: string;
  threshold: number;
  is_active: boolean;
  created_at: string;
}

export interface AlertHistory {
  id: string;
  rule_id: string;
  triggered_value: number;
  triggered_at: string;
}

export interface PaginatedHistory {
  items: AlertHistory[];
  total: number;
  pages: number;
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

export async function getRules(): Promise<AlertRule[]> {
  const response = await apiClient.get<{ data: AlertRule[] }>(
    "/alerts/rules",
  );
  return response.data.data ?? [];
}

export async function createRule(data: {
  alert_type: string;
  threshold: number;
}): Promise<AlertRule> {
  const response = await apiClient.post<AlertRule>("/alerts/rules", data);
  return response.data;
}

export async function updateRule(
  id: string,
  data: { threshold?: number; is_active?: boolean },
): Promise<AlertRule> {
  const response = await apiClient.patch<AlertRule>(
    `/alerts/rules/${id}`,
    data,
  );
  return response.data;
}

export async function deleteRule(id: string): Promise<void> {
  await apiClient.delete(`/alerts/rules/${id}`);
}

export async function getHistory(
  page?: number,
  limit?: number,
): Promise<PaginatedHistory> {
  const response = await apiClient.get<PaginatedHistory>("/alerts/history", {
    params: { page, limit },
  });
  return response.data;
}
