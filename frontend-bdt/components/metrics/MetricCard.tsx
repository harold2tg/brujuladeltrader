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

const trendColors: Record<Trend, string> = {
  positive: "text-green-600",
  negative: "text-red-600",
  neutral: "text-muted-foreground",
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
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="size-4" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-7 w-20" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        {icon && (
          <div className="text-muted-foreground [&>svg]:size-4">{icon}</div>
        )}
      </CardHeader>
      <CardContent>
        <p className={cn("text-2xl font-bold", trendColors[trend])}>{value}</p>
      </CardContent>
    </Card>
  );
}
