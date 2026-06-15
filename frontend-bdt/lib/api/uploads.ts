import { apiClient } from "./client";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface Upload {
  id: string;
  original_name: string;
  status: string;
  total_trades?: number;
  winning_trades?: number;
  losing_trades?: number;
  net_pnl?: number;
  created_at: string;
}

export interface UploadListResponse {
  success: boolean;
  data: {
    items: Upload[];
    total: number;
    page: number;
    limit: number;
  };
}

export interface UploadDetailResponse {
  success: boolean;
  data: Upload;
}

export interface UploadFileResponse {
  upload_id: string;
  status: string;
}

export interface UploadStatusResponse {
  status: string;
  progress_pct?: number;
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

export async function getUploads(): Promise<UploadListResponse> {
  const response = await apiClient.get<UploadListResponse>("/uploads");
  return response.data;
}

export async function getUpload(id: string): Promise<UploadDetailResponse> {
  const response = await apiClient.get<UploadDetailResponse>(`/uploads/${id}`);
  return response.data;
}

export async function uploadFile(
  file: File,
  periodLabel?: string,
): Promise<UploadFileResponse> {
  const formData = new FormData();
  formData.append("file", file);
  if (periodLabel) {
    formData.append("period_label", periodLabel);
  }

  const response = await apiClient.post<UploadFileResponse>(
    "/uploads",
    formData,
    {
      headers: { "Content-Type": "multipart/form-data" },
    },
  );
  return response.data;
}

export async function deleteUpload(id: string): Promise<void> {
  await apiClient.delete(`/uploads/${id}`);
}

export async function getUploadStatus(
  id: string,
): Promise<UploadStatusResponse> {
  const response = await apiClient.get<UploadStatusResponse>(
    `/uploads/${id}/status`,
  );
  return response.data;
}
