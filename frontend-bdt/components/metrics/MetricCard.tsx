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

// Semantic tokens only: var(--primary) for profit/positive, var(--destructive) for loss/negative.
const trendConfig: Record<Trend, { text: string; iconText: string }> = {
  positive: {
    text: "text-primary",
    iconText: "text-primary",
  },
  negative: {
    text: "text-destructive",
    iconText: "text-destructive",
  },
  neutral: {
    text: "text-foreground",
    iconText: "text-muted-foreground",
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
      <Card className="border-border/40">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="size-9 rounded-lg bg-elevated" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-8 w-28" />
        </CardContent>
      </Card>
    );
  }

  const config = trendConfig[trend];

  return (
    <Card
      className={cn(
        "border-border/40 transition-[border-color,transform] duration-150 ease-out",
        "hover:border-border hover:-translate-y-0.5",
      )}
    >
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
          {title}
        </CardTitle>
        {icon && (
          <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-elevated ring-1 ring-foreground/5">
            <div className={cn("[&>svg]:size-4.5", config.iconText)}>{icon}</div>
          </div>
        )}
      </CardHeader>
      <CardContent>
        <p
          className={cn(
            "num-tabular font-mono text-3xl font-semibold tracking-tight",
            config.text,
          )}
        >
          {value}
        </p>
      </CardContent>
    </Card>
  );
}
