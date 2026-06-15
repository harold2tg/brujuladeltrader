import type { ReactNode } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

type Trend = "positive" | "negative" | "neutral";

interface MetricCardProps {
  title: string;
  value: string;
  icon?: ReactNode;
  trend?: Trend;
  loading?: boolean;
}

const trendConfig: Record<Trend, { text: string; iconBg: string; glow: string }> = {
  positive: {
    text: "text-emerald-400",
    iconBg: "bg-emerald-500/10",
    glow: "shadow-emerald-500/5",
  },
  negative: {
    text: "text-red-400",
    iconBg: "bg-red-500/10",
    glow: "shadow-red-500/5",
  },
  neutral: {
    text: "text-muted-foreground",
    iconBg: "bg-muted",
    glow: "",
  },
};

export function MetricCard({
  title,
  value,
  icon,
  trend = "neutral",
  loading,
}: MetricCardProps) {
  if (loading) {
    return (
      <Card className="overflow-hidden border-border/40">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="size-10 rounded-xl" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-9 w-24" />
        </CardContent>
      </Card>
    );
  }

  const config = trendConfig[trend];

  return (
    <Card className={cn("group relative overflow-hidden border-border/40 transition-all duration-300 hover:border-border/60 hover:shadow-lg", config.glow)}>
      {/* Subtle gradient overlay on hover */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/[0.02] to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />

      <CardHeader className="relative flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground/70">
          {title}
        </CardTitle>
        {icon && (
          <div
            className={cn(
              "flex size-10 items-center justify-center rounded-xl transition-all duration-300 group-hover:scale-105",
              config.iconBg,
            )}
          >
            <div className={cn("[&>svg]:size-5", config.text)}>{icon}</div>
          </div>
        )}
      </CardHeader>
      <CardContent className="relative">
        <p
          className={cn(
            "text-3xl font-bold tracking-tight",
            config.text,
          )}
        >
          {value}
        </p>
      </CardContent>
    </Card>
  );
}
