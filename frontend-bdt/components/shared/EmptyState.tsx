import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "relative flex flex-col items-center justify-center gap-5 overflow-hidden rounded-2xl border border-dashed border-border/50 bg-gradient-to-br from-muted/20 via-muted/10 to-transparent py-20 text-center",
        className,
      )}
    >
      {/* Decorative gradient orbs */}
      <div className="pointer-events-none absolute -left-20 -top-20 size-40 rounded-full bg-primary/5 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-20 -right-20 size-40 rounded-full bg-primary/5 blur-3xl" />

      {icon && (
        <div className="relative flex size-16 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/15 to-primary/5 shadow-lg shadow-primary/10">
          <div className="text-primary [&>svg]:size-7">{icon}</div>
        </div>
      )}
      <div className="relative space-y-2">
        <h3 className="text-base font-semibold">{title}</h3>
        {description && (
          <p className="max-w-sm text-sm leading-relaxed text-muted-foreground">
            {description}
          </p>
        )}
      </div>
      {action && <div className="relative mt-1">{action}</div>}
    </div>
  );
}
