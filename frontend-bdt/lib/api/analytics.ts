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
  month: number;
  label: string;
  total_trades: number;
  net_pnl: number;
  win_rate: number;
}

export interface WeeklyMetrics {
  week: number;
  label: string;
  trades: number;
  wins: number;
  losses: number;
  win_rate: number;
  net_pnl: number;
  avg_pnl: number;
}

export interface SemesterMetrics {
  semester: number;
  label: string;
  trades: number;
  wins: number;
  losses: number;
  win_rate: number;
  net_pnl: number;
  avg_pnl: number;
}

export interface YearlyMetrics {
  year: number;
  label: string;
  trades: number;
  wins: number;
  losses: number;
  win_rate: number;
  net_pnl: number;
  avg_pnl: number;
}

export interface DistributionBin {
  range: string;
  count: number;
}

export interface AnalyticsResponse {
  success: boolean;
  data: {
    global: GlobalMetrics;
    by_hour: HourMetrics[];
    by_day: DayMetrics[];
    by_month: MonthlyMetrics[];
    by_direction: { buy: DirectionMetrics; sell: DirectionMetrics };
    by_session: SessionMetrics[];
    distribution: DistributionBin[];
    streaks: StreakMetrics;
    simulations: SimulationMetrics;
  };
}

export interface DirectionMetrics {
  trades: number;
  wins: number;
  losses: number;
  win_rate: number;
  net_pnl: number;
  avg_win: number;
  avg_loss: number;
}

export interface StreakMetrics {
  max_win_streak: number;
  max_loss_streak: number;
  current_streak: number;
  loss_streak_3_plus_count: number;
}

export interface SimulationMetrics {
  sim_max_loss_5_pnl: number;
  sim_best_3_hours_pnl: number;
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

export interface WeeklyAnalyticsResponse {
  success: boolean;
  data: WeeklyMetrics[];
}

export interface SemesterAnalyticsResponse {
  success: boolean;
  data: SemesterMetrics[];
}

export interface YearlyAnalyticsResponse {
  success: boolean;
  data: YearlyMetrics[];
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

export async function getAnalyticsByWeek(uploadId: string): Promise<WeeklyAnalyticsResponse> {
  const response = await apiClient.get<WeeklyAnalyticsResponse>(
    `/analytics/${uploadId}/by-week`,
  );
  return response.data;
}

export async function getAnalyticsBySemester(uploadId: string): Promise<SemesterAnalyticsResponse> {
  const response = await apiClient.get<SemesterAnalyticsResponse>(
    `/analytics/${uploadId}/by-semester`,
  );
  return response.data;
}

export async function getAnalyticsByYear(uploadId: string): Promise<YearlyAnalyticsResponse> {
  const response = await apiClient.get<YearlyAnalyticsResponse>(
    `/analytics/${uploadId}/by-year`,
  );
  return response.data;
}

// ---------------------------------------------------------------------------
// Equity Curve
// ---------------------------------------------------------------------------

export interface EquityCurvePoint {
  trade_number: number;
  balance: number;
  net_pnl: number;
  label: string;
}

export interface EquityCurveResponse {
  success: boolean;
  data: EquityCurvePoint[];
}

export async function getEquityCurve(uploadId: string): Promise<EquityCurveResponse> {
  const response = await apiClient.get<EquityCurveResponse>(
    `/analytics/${uploadId}/equity-curve`,
  );
  return response.data;
}
