import { useQuery } from "@tanstack/react-query";
import {
  getAnalytics,
  getAnalyticsByHour,
  getAnalyticsByDay,
  getAnalyticsBySession,
  getAnalyticsByMonth,
  getAnalyticsByWeek,
  getAnalyticsBySemester,
  getAnalyticsByYear,
  getAnalyticsDistribution,
  getEquityCurve,
} from "@/lib/api/analytics";

export function useAnalytics(dataSourceId: string | null) {
  return useQuery({
    queryKey: ["analytics", dataSourceId],
    queryFn: () => getAnalytics(dataSourceId!),
    enabled: !!dataSourceId,
  });
}

export function useAnalyticsByHour(dataSourceId: string | null) {
  return useQuery({
    queryKey: ["analytics", dataSourceId, "by-hour"],
    queryFn: () => getAnalyticsByHour(dataSourceId!),
    enabled: !!dataSourceId,
  });
}

export function useAnalyticsByDay(dataSourceId: string | null) {
  return useQuery({
    queryKey: ["analytics", dataSourceId, "by-day"],
    queryFn: () => getAnalyticsByDay(dataSourceId!),
    enabled: !!dataSourceId,
  });
}

export function useAnalyticsBySession(dataSourceId: string | null) {
  return useQuery({
    queryKey: ["analytics", dataSourceId, "by-session"],
    queryFn: () => getAnalyticsBySession(dataSourceId!),
    enabled: !!dataSourceId,
  });
}

export function useAnalyticsByMonth(dataSourceId: string | null) {
  return useQuery({
    queryKey: ["analytics", dataSourceId, "by-month"],
    queryFn: () => getAnalyticsByMonth(dataSourceId!),
    enabled: !!dataSourceId,
  });
}

export function useAnalyticsDistribution(dataSourceId: string | null) {
  return useQuery({
    queryKey: ["analytics", dataSourceId, "distribution"],
    queryFn: () => getAnalyticsDistribution(dataSourceId!),
    enabled: !!dataSourceId,
  });
}

export function useAnalyticsByWeek(dataSourceId: string | null) {
  return useQuery({
    queryKey: ["analytics", dataSourceId, "by-week"],
    queryFn: () => getAnalyticsByWeek(dataSourceId!),
    enabled: !!dataSourceId,
  });
}

export function useAnalyticsBySemester(dataSourceId: string | null) {
  return useQuery({
    queryKey: ["analytics", dataSourceId, "by-semester"],
    queryFn: () => getAnalyticsBySemester(dataSourceId!),
    enabled: !!dataSourceId,
  });
}

export function useAnalyticsByYear(dataSourceId: string | null) {
  return useQuery({
    queryKey: ["analytics", dataSourceId, "by-year"],
    queryFn: () => getAnalyticsByYear(dataSourceId!),
    enabled: !!dataSourceId,
  });
}

export function useEquityCurve(dataSourceId: string | null) {
  return useQuery({
    queryKey: ["analytics", dataSourceId, "equity-curve"],
    queryFn: () => getEquityCurve(dataSourceId!),
    enabled: !!dataSourceId,
  });
}
