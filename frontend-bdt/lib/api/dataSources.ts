import { apiClient } from "./client";
import type {
  DataSource,
  DataSourceListResponse,
  DataSourceDetailResponse,
  DataSourceFilters,
} from "@/lib/types/data-source";

// ---------------------------------------------------------------------------
// Re-export types for convenience
// ---------------------------------------------------------------------------

export type { DataSource, DataSourceListResponse, DataSourceDetailResponse, DataSourceFilters };

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

export async function getDataSources(
  filters?: DataSourceFilters,
): Promise<DataSourceListResponse> {
  const response = await apiClient.get<DataSourceListResponse>("/data-sources", {
    params: filters,
  });
  return response.data;
}

export async function getDataSource(
  id: string,
): Promise<DataSourceDetailResponse> {
  const response = await apiClient.get<DataSourceDetailResponse>(
    `/data-sources/${id}`,
  );
  return response.data;
}

export async function deleteDataSource(id: string): Promise<void> {
  await apiClient.delete(`/data-sources/${id}`);
}

export async function syncDataSource(id: string): Promise<{ status: string }> {
  const response = await apiClient.post<{ status: string }>(
    `/data-sources/${id}/sync`,
  );
  return response.data;
}
