"use client";

import { Activity, BarChart3, Layers, Percent, Scale } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { UserStats } from "@/lib/hooks/useSettings";

interface StatsCardProps {
  stats: UserStats;
}

function formatPnl(value: number): string {
  const sign = value > 0 ? "+" : "";
  return `${sign}$${value.toLocaleString("es-ES", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function formatRatio(value: number): string {
  return `${(value * 100).toLocaleString("es-ES", {
    maximumFractionDigits: 1,
  })}%`;
}

function formatRr(value: number): string {
  return `1 : ${value.toLocaleString("es-ES", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

interface StatItemProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  valueClass?: string;
  muted?: boolean;
}

function StatItem({ icon, label, value, valueClass, muted }: StatItemProps) {
  return (
    <div className="flex items-center gap-3 rounded-lg bg-elevated/50 px-3 py-2.5 ring-1 ring-border">
      <div className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary ring-1 ring-primary/20 [&_svg]:size-4">
        {icon}
      </div>
      <div className="min-w-0">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p
          className={cn(
            "num-tabular truncate text-sm font-semibold",
            muted ? "text-muted-foreground" : "text-foreground",
            valueClass,
          )}
        >
          {value}
        </p>
      </div>
    </div>
  );
}

export function StatsCard({ stats }: StatsCardProps) {
  const pnlPositive = stats.total_pnl >= 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Resumen de tu actividad</CardTitle>
        <CardDescription>
          Métricas agregadas de tus datos y operaciones.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <StatItem
            icon={<Layers />}
            label="Fuentes de datos"
            value={stats.total_data_sources.toLocaleString("es-ES")}
          />
          <StatItem
            icon={<Activity />}
            label="Operaciones"
            value={stats.total_trades.toLocaleString("es-ES")}
          />
          <StatItem
            icon={<BarChart3 />}
            label="PnL total"
            value={formatPnl(stats.total_pnl)}
            valueClass={pnlPositive ? "text-primary" : "text-destructive"}
          />
          <StatItem
            icon={<Percent />}
            label="Tasa de acierto"
            value={formatRatio(stats.win_rate)}
          />
          <StatItem
            icon={<Scale />}
            label="R:R promedio"
            value={
              stats.avg_rr_ratio === null
                ? "Sin datos"
                : formatRr(stats.avg_rr_ratio)
            }
            muted={stats.avg_rr_ratio === null}
          />
        </div>
      </CardContent>
    </Card>
  );
}
