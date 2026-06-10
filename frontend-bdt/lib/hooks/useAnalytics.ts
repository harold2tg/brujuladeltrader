import { useQuery } from "@tanstack/react-query";
import {
  getAnalytics,
  getAnalyticsByHour,
  getAnalyticsByDay,
  getAnalyticsBySession,
  getAnalyticsByMonth,
  getAnalyticsDistribution,
} from "@/lib/api/analytics";

export function useAnalytics(uploadId: string | null) {
  return useQuery({
    queryKey: ["analytics", uploadId],
    queryFn: () => getAnalytics(uploadId!),
    enabled: !!uploadId,
  });
}

export function useAnalyticsByHour(uploadId: string | null) {
  return useQuery({
    queryKey: ["analytics", uploadId, "by-hour"],
    queryFn: () => getAnalyticsByHour(uploadId!),
    enabled: !!uploadId,
  });
}

export function useAnalyticsByDay(uploadId: string | null) {
  return useQuery({
    queryKey: ["analytics", uploadId, "by-day"],
    queryFn: () => getAnalyticsByDay(uploadId!),
    enabled: !!uploadId,
  });
}

export function useAnalyticsBySession(uploadId: string | null) {
  return useQuery({
    queryKey: ["analytics", uploadId, "by-session"],
    queryFn: () => getAnalyticsBySession(uploadId!),
    enabled: !!uploadId,
  });
}

export function useAnalyticsByMonth(uploadId: string | null) {
  return useQuery({
    queryKey: ["analytics", uploadId, "by-month"],
    queryFn: () => getAnalyticsByMonth(uploadId!),
    enabled: !!uploadId,
  });
}

export function useAnalyticsDistribution(uploadId: string | null) {
  return useQuery({
    queryKey: ["analytics", uploadId, "distribution"],
    queryFn: () => getAnalyticsDistribution(uploadId!),
    enabled: !!uploadId,
  });
}
