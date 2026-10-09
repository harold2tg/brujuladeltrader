import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getCredentials,
  getAuthUrl,
  authorizeCtrader,
  deleteCredentials,
  startSync,
  getSyncStatus,
} from "@/lib/api/ctrader";

export function useCTraderCredentials() {
  return useQuery({
    queryKey: ["ctrader", "credentials"],
    queryFn: getCredentials,
  });
}

export function useCTraderAuthUrl() {
  return useMutation({
    mutationFn: getAuthUrl,
  });
}

export function useAuthorizeCTrader() {
  return useMutation({
    mutationFn: authorizeCtrader,
  });
}

export function useDeleteCTraderCredentials() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteCredentials,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ctrader", "credentials"] });
    },
  });
}

export function useStartCTraderSync() {
  return useMutation({
    mutationFn: startSync,
  });
}

export function useCTraderSyncStatus(jobId: string | null) {
  return useQuery({
    queryKey: ["ctrader", "sync", jobId],
    queryFn: () => getSyncStatus(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "processing" || status === "pending") {
        return 2000;
      }
      return false;
    },
  });
}
