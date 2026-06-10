import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getUploads,
  getUpload,
  uploadFile,
  deleteUpload,
  getUploadStatus,
} from "@/lib/api/uploads";

export function useUploads() {
  return useQuery({
    queryKey: ["uploads"],
    queryFn: getUploads,
  });
}

export function useUpload(id: string | null) {
  return useQuery({
    queryKey: ["uploads", id],
    queryFn: () => getUpload(id!),
    enabled: !!id,
  });
}

export function useUploadStatus(id: string | null) {
  return useQuery({
    queryKey: ["uploads", id, "status"],
    queryFn: () => getUploadStatus(id!),
    enabled: !!id,
    refetchInterval: 2000,
  });
}

export function useUploadFile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ file, periodLabel }: { file: File; periodLabel?: string }) =>
      uploadFile(file, periodLabel),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["uploads"] });
    },
  });
}

export function useDeleteUpload() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteUpload,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["uploads"] });
    },
  });
}
