import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getDataSources,
  getDataSource,
  deleteDataSource,
  syncDataSource,
} from "@/lib/api/dataSources";
import type { DataSourceFilters } from "@/lib/types/data-source";

export function useDataSources(filters?: DataSourceFilters) {
  return useQuery({
    queryKey: ["data-sources", filters],
    queryFn: () => getDataSources(filters),
  });
}

export function useDataSource(id: string | null) {
  return useQuery({
    queryKey: ["data-sources", id],
    queryFn: () => getDataSource(id!),
    enabled: !!id,
  });
}

export function useDeleteDataSource() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteDataSource,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["data-sources"] });
    },
  });
}

export function useSyncDataSource() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: syncDataSource,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["data-sources"] });
    },
  });
}
