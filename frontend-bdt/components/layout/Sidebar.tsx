"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTranslations } from "next-intl";
import {
  LayoutDashboard,
  Upload,
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
  { href: "/uploads", icon: Upload, labelKey: "nav.uploads" },
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
      <div className="relative px-5 pb-6 pt-7">
        <div className="flex items-center gap-3.5">
          <div className="relative flex size-11 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 shadow-lg shadow-primary/10">
            <Compass className="size-5.5 text-primary" />
            <div className="absolute -inset-px rounded-2xl bg-gradient-to-br from-primary/20 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
          </div>
          <div className="flex flex-col">
            <span className="text-[15px] font-bold tracking-tight text-foreground">
              La Brújula
            </span>
            <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-primary/60">
              del Trader
            </span>
          </div>
        </div>
      </div>

      {/* Divider with gradient */}
      <div className="mx-4 h-px bg-gradient-to-r from-transparent via-border to-transparent" />

      {/* Section label */}
      <div className="px-5 pt-5 pb-2">
        <span className="text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground/50">
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
                "group relative flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium transition-all duration-200",
                isActive
                  ? "bg-gradient-to-r from-primary/15 to-primary/5 text-primary shadow-md shadow-primary/5"
                  : "text-muted-foreground hover:bg-accent hover:text-foreground",
              )}
            >
              {/* Active indicator bar */}
              {isActive && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 rounded-r-full bg-primary shadow-sm shadow-primary/30">
                  <div className="h-5 w-[3px] rounded-r-full bg-primary" />
                </div>
              )}

              <item.icon
                className={cn(
                  "size-4 transition-all duration-200",
                  isActive
                    ? "text-primary drop-shadow-[0_0_6px_oklch(0.65_0.26_265/0.4)]"
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
        <div className="rounded-xl bg-gradient-to-br from-primary/8 to-transparent p-4 ring-1 ring-primary/10">
          <div className="flex items-center gap-2.5">
            <div className="flex size-8 items-center justify-center rounded-lg bg-primary/10">
              <Zap className="size-4 text-primary" />
            </div>
            <div>
              <p className="text-xs font-semibold text-foreground/90">
                XAUUSD Analytics
              </p>
              <p className="text-[10px] text-muted-foreground/60">
                v1.0 · MVP
              </p>
            </div>
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
      <aside className="hidden lg:flex lg:w-64 lg:flex-col lg:border-r lg:border-border/40 lg:bg-sidebar">
        <SidebarContent />
      </aside>
    </>
  );
}

export { SidebarContent };
