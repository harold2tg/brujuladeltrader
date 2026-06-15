import { apiClient } from "./client";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface CtraderCredentials {
  id: string;
  account_name?: string;
  broker_name?: string;
  is_demo: boolean;
  has_credentials: boolean;
}

export interface TestConnectionResult {
  connected: boolean;
  latency_ms?: number;
  error?: string;
}

export interface SyncJob {
  job_id: string;
  status: string;
}

export interface SyncStatus {
  status: string;
  progress_pct?: number;
  trades_imported?: number;
  error?: string;
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

export async function saveCredentials(data: {
  client_id: string;
  client_secret: string;
  access_token: string;
  account_id: string;
}): Promise<{ connected: boolean }> {
  const response = await apiClient.post<{ connected: boolean }>(
    "/ctrader/credentials",
    data,
  );
  return response.data;
}

export async function getCredentials(): Promise<CtraderCredentials | null> {
  const response = await apiClient.get<{ data: CtraderCredentials | null }>(
    "/ctrader/credentials",
  );
  return response.data.data ?? null;
}

export async function testConnection(): Promise<TestConnectionResult> {
  const response = await apiClient.get<TestConnectionResult>("/ctrader/test");
  return response.data;
}

export async function deleteCredentials(id: string): Promise<void> {
  await apiClient.delete(`/ctrader/credentials/${id}`);
}

export async function startSync(data: {
  mode: string;
  date?: string;
}): Promise<SyncJob> {
  const response = await apiClient.post<SyncJob>("/ctrader/sync", data);
  return response.data;
}

export async function getSyncStatus(
  jobId: string,
): Promise<SyncStatus> {
  const response = await apiClient.get<SyncStatus>(
    `/ctrader/sync/${jobId}`,
  );
  return response.data;
}
