import { apiClient } from "./client";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface AIProvider {
  name: string;
  display_name: string;
  models: string[];
}

export interface AIJob {
  job_id: string;
  status: string;
}

export interface AIInsight {
  type: string;
  content: string;
}

export interface AIJobStatus {
  status: string;
  result?: Record<string, unknown>;
  fallback_used?: boolean;
}

export interface AIInsightsResponse {
  insights: AIInsight[];
  cached: boolean;
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

export async function getProviders(): Promise<AIProvider[]> {
  const response = await apiClient.get<{ data: AIProvider[] }>(
    "/ai/providers",
  );
  return response.data.data ?? [];
}

export async function startAnalysis(
  uploadId: string,
  data: { analysis_type: string; language: string },
): Promise<AIJob> {
  const response = await apiClient.post<AIJob>(
    `/ai/analyze/${uploadId}`,
    data,
  );
  return response.data;
}

export async function getJobStatus(jobId: string): Promise<AIJobStatus> {
  const response = await apiClient.get<AIJobStatus>(`/ai/jobs/${jobId}`);
  return response.data;
}

export async function getInsights(
  uploadId: string,
): Promise<AIInsightsResponse> {
  const response = await apiClient.get<AIInsightsResponse>(
    `/ai/insights/${uploadId}`,
  );
  return response.data;
}
