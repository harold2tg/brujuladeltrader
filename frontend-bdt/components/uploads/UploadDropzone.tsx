"use client";

import { useCallback, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { Upload, FileSpreadsheet, X } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { uploadFile } from "@/lib/api/uploads";

const ACCEPTED_TYPES = [
  "text/csv",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "application/vnd.ms-excel",
];
const ACCEPTED_EXTENSIONS = ".csv,.xlsx,.xls";
const MAX_SIZE_BYTES = 10 * 1024 * 1024; // 10 MB

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function UploadDropzone() {
  const t = useTranslations("uploads");
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragActive, setIsDragActive] = useState(false);

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadFile(file),
    onSuccess: () => {
      toast.success(t("uploadSuccess"));
      setSelectedFile(null);
      queryClient.invalidateQueries({ queryKey: ["uploads"] });
    },
    onError: (error: Error) => {
      toast.error(t("uploadError") + error.message);
    },
  });

  const validateFile = useCallback(
    (file: File): string | null => {
      if (!ACCEPTED_TYPES.includes(file.type) && !file.name.match(/\.(csv|xlsx|xls)$/i)) {
        return t("invalidType");
      }
      if (file.size > MAX_SIZE_BYTES) {
        return t("invalidSize");
      }
      return null;
    },
    [t],
  );

  const handleFile = useCallback(
    (file: File) => {
      const error = validateFile(file);
      if (error) {
        toast.error(error);
        return;
      }
      setSelectedFile(file);
    },
    [validateFile],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragActive(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(false);
  }, []);

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
      // Reset input so same file can be selected again
      e.target.value = "";
    },
    [handleFile],
  );

  const handleUpload = () => {
    if (!selectedFile) return;
    uploadMutation.mutate(selectedFile);
  };

  return (
    <div className="space-y-3">
      {/* Dropzone */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => fileInputRef.current?.click()}
        className={cn(
          "flex flex-col items-center gap-2 rounded-lg border-2 border-dashed p-6 text-center transition-colors cursor-pointer",
          isDragActive
            ? "border-primary bg-primary/5"
            : "border-muted-foreground/25 hover:border-muted-foreground/50",
        )}
      >
        <Upload className="size-8 text-muted-foreground" />
        <p className="text-sm font-medium">{t("dropzone")}</p>
        <p className="text-xs text-muted-foreground">{t("dropzoneHint")}</p>
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPTED_EXTENSIONS}
          onChange={handleInputChange}
          className="hidden"
        />
      </div>

      {/* Selected file preview */}
      {selectedFile && (
        <div className="flex items-center justify-between rounded-lg border bg-muted/50 px-4 py-3">
          <div className="flex items-center gap-3">
            <FileSpreadsheet className="size-5 text-primary" />
            <div>
              <p className="text-sm font-medium">{selectedFile.name}</p>
              <p className="text-xs text-muted-foreground">
                {formatFileSize(selectedFile.size)}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={(e) => {
                e.stopPropagation();
                setSelectedFile(null);
              }}
              disabled={uploadMutation.isPending}
            >
              <X className="size-4" />
            </Button>
            <Button
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                handleUpload();
              }}
              disabled={uploadMutation.isPending}
            >
              {uploadMutation.isPending
                ? t("uploading")
                : t("uploadButton")}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
