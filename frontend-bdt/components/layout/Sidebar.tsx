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
} from "lucide-react";
import { cn } from "@/lib/utils";

interface NavItem {
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  labelKey: string;
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
    <div className="flex h-full flex-col">
      {/* Logo */}
      <div className="flex items-center gap-2 px-4 py-5">
        <Compass className="size-6 text-primary" />
        <span className="text-lg font-bold">La Brújula</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3">
        {navItems.map((item) => {
          const isActive = pathname.includes(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavClick}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground",
              )}
            >
              <item.icon className="size-4" />
              {t(item.labelKey)}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}

export function Sidebar() {
  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex lg:w-64 lg:flex-col lg:border-r lg:bg-sidebar">
        <SidebarContent />
      </aside>

      {/* Mobile sidebar (sheet is rendered by Header via SheetContent) */}
      {/* The mobile sidebar open/close is managed via uiStore.sidebarOpen */}
      {/* and rendered inside the Header component using Sheet */}
    </>
  );
}

export { SidebarContent };
