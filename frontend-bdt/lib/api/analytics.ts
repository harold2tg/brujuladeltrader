import { apiClient } from "./client";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface GlobalMetrics {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  net_pnl: number;
  gross_profit: number;
  gross_loss: number;
  avg_win: number;
  avg_loss: number;
  rr_ratio: number | null;
  profit_factor: number | null;
  total_return_pct: number;
  max_win_streak: number;
  max_loss_streak: number;
  current_streak: number;
  best_trade: number;
  worst_trade: number;
}

export interface HourMetrics {
  hour: number;
  total_trades: number;
  net_pnl: number;
  win_rate: number;
}

export interface DayMetrics {
  day_of_week: number;
  total_trades: number;
  net_pnl: number;
  win_rate: number;
}

export interface SessionMetrics {
  session: string;
  total_trades: number;
  net_pnl: number;
  win_rate: number;
}

export interface MonthlyMetrics {
  month: string;
  total_trades: number;
  net_pnl: number;
  win_rate: number;
}

export interface DistributionBin {
  range: string;
  count: number;
}

export interface AnalyticsResponse {
  success: boolean;
  data: GlobalMetrics;
}

export interface HourAnalyticsResponse {
  success: boolean;
  data: HourMetrics[];
}

export interface DayAnalyticsResponse {
  success: boolean;
  data: DayMetrics[];
}

export interface SessionAnalyticsResponse {
  success: boolean;
  data: SessionMetrics[];
}

export interface MonthlyAnalyticsResponse {
  success: boolean;
  data: MonthlyMetrics[];
}

export interface DistributionAnalyticsResponse {
  success: boolean;
  data: DistributionBin[];
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

export async function getAnalytics(uploadId: string): Promise<AnalyticsResponse> {
  const response = await apiClient.get<AnalyticsResponse>(
    `/analytics/${uploadId}`,
  );
  return response.data;
}

export async function getAnalyticsByHour(uploadId: string): Promise<HourAnalyticsResponse> {
  const response = await apiClient.get<HourAnalyticsResponse>(
    `/analytics/${uploadId}/by-hour`,
  );
  return response.data;
}

export async function getAnalyticsByDay(uploadId: string): Promise<DayAnalyticsResponse> {
  const response = await apiClient.get<DayAnalyticsResponse>(
    `/analytics/${uploadId}/by-day`,
  );
  return response.data;
}

export async function getAnalyticsBySession(uploadId: string): Promise<SessionAnalyticsResponse> {
  const response = await apiClient.get<SessionAnalyticsResponse>(
    `/analytics/${uploadId}/by-session`,
  );
  return response.data;
}

export async function getAnalyticsByMonth(uploadId: string): Promise<MonthlyAnalyticsResponse> {
  const response = await apiClient.get<MonthlyAnalyticsResponse>(
    `/analytics/${uploadId}/by-month`,
  );
  return response.data;
}

export async function getAnalyticsDistribution(uploadId: string): Promise<DistributionAnalyticsResponse> {
  const response = await apiClient.get<DistributionAnalyticsResponse>(
    `/analytics/${uploadId}/distribution`,
  );
  return response.data;
}
