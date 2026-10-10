"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTranslations } from "next-intl";
import {
  LayoutDashboard,
  Database,
  BarChart3,
  TrendingUp,
  Bell,
  FileText,
  Settings,
  Compass,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface NavItem {
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  labelKey: string;
  badge?: string;
}

const navItems: NavItem[] = [
  { href: "/dashboard", icon: LayoutDashboard, labelKey: "nav.dashboard" },
  { href: "/data-sources", icon: Database, labelKey: "nav.dataSources" },
  { href: "/analytics", icon: BarChart3, labelKey: "nav.analytics" },
  { href: "/ctrader", icon: TrendingUp, labelKey: "nav.ctrader" },
  { href: "/alerts", icon: Bell, labelKey: "nav.alerts" },
  { href: "/reports", icon: FileText, labelKey: "nav.reports" },
  { href: "/settings", icon: Settings, labelKey: "nav.settings" },
];

interface SidebarContentProps {
  onNavClick?: () => void;
}

function SidebarContent({ onNavClick }: SidebarContentProps) {
  const pathname = usePathname();
  const t = useTranslations();

  return (
    <div className="flex h-full flex-col bg-sidebar">
      {/* Logo */}
      <div className="px-5 pb-6 pt-7">
        <div className="flex items-center gap-3.5">
          <div className="flex size-11 items-center justify-center rounded-xl border border-border bg-card">
            <Compass className="size-5.5 text-primary" />
          </div>
          <div className="flex flex-col">
            <span className="text-[15px] font-bold tracking-tight text-foreground">
              La Brújula
            </span>
            <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-muted-foreground">
              del Trader
            </span>
          </div>
        </div>
      </div>

      {/* Divider */}
      <div className="mx-4 h-px bg-border/60" />

      {/* Section label */}
      <div className="px-5 pt-5 pb-2">
        <span className="text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground">
          Navigation
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-0.5 px-3">
        {navItems.map((item) => {
          const isActive = pathname.includes(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavClick}
              className={cn(
                "group relative flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium transition-colors duration-150",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-elevated/60 hover:text-foreground",
              )}
            >
              {/* Active indicator bar */}
              {isActive && (
                <div className="absolute left-0 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-r-full bg-primary" />
              )}

              <item.icon
                className={cn(
                  "size-4 transition-colors duration-150",
                  isActive
                    ? "text-primary"
                    : "text-muted-foreground group-hover:text-foreground",
                )}
              />
              <span className="flex-1">{t(item.labelKey)}</span>

              {/* Badge (for future use) */}
              {item.badge && (
                <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-primary/20 px-1.5 text-[10px] font-bold text-primary">
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Bottom status card */}
      <div className="px-3 pb-4">
        <div className="flex items-center gap-2.5 rounded-lg border border-border/50 bg-card/40 px-3 py-2.5">
          <Zap className="size-4 shrink-0 text-muted-foreground" />
          <div className="min-w-0">
            <p className="truncate text-xs font-medium text-muted-foreground">
              XAUUSD Analytics
            </p>
            <p className="num-tabular text-[10px] text-muted-foreground/70">
              v1.0 · MVP
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export function Sidebar() {
  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex lg:w-64 lg:flex-col lg:border-r lg:border-border lg:bg-sidebar">
        <SidebarContent />
      </aside>
    </>
  );
}

export { SidebarContent };
