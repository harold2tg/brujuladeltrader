// ---------------------------------------------------------------------------
// DataSource types — aligned with backend data_source model
// ---------------------------------------------------------------------------

export type SyncStatus = "pending" | "syncing" | "ready" | "error";

export interface DataSource {
  id: string;
  user_id: string;
  broker: string;
  broker_account_id: string;
  name: string;
  sync_status: SyncStatus;
  last_synced_at: string | null;
  trade_count: number;
  first_trade_at: string | null;
  last_trade_at: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface DataSourceListResponse {
  data_sources: DataSource[];
  total: number;
}

export interface DataSourceDetailResponse {
  data_source: DataSource;
}

export interface DataSourceFilters {
  broker?: string;
  sync_status?: SyncStatus;
  page?: number;
  limit?: number;
}
