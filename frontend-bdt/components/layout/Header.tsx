"use client";

import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { Menu, LogOut, User, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Avatar,
  AvatarFallback,
} from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Sheet,
  SheetContent,
  SheetTitle,
} from "@/components/ui/sheet";
import { useAuthStore } from "@/lib/stores/authStore";
import { useUIStore } from "@/lib/stores/uiStore";
import { LanguageSwitcher } from "@/components/layout/LanguageSwitcher";
import { SidebarContent } from "@/components/layout/Sidebar";

export function Header() {
  const t = useTranslations();
  const router = useRouter();
  const { user, logout } = useAuthStore();
  const { sidebarOpen, setSidebarOpen } = useUIStore();

  const initials = user?.name
    ? user.name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "??";

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <header className="relative flex h-16 items-center justify-between border-b border-border/40 bg-background/60 px-4 backdrop-blur-2xl lg:px-6">
      {/* Subtle top gradient line */}
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/20 to-transparent" />

      {/* Left: hamburger + mobile sheet */}
      <div className="flex items-center gap-2">
        <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
          <Button
            variant="ghost"
            size="icon-sm"
            className="lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="size-5" />
            <span className="sr-only">{t("common.openMenu")}</span>
          </Button>
          <SheetContent side="left" className="w-64 border-r-border/40 p-0">
            <SheetTitle className="sr-only">
              {t("nav.dashboard")}
            </SheetTitle>
            <SidebarContent onNavClick={() => setSidebarOpen(false)} />
          </SheetContent>
        </Sheet>
      </div>

      {/* Right: language switcher + user dropdown */}
      <div className="flex items-center gap-3">
        <LanguageSwitcher />

        {/* Separator */}
        <div className="h-5 w-px bg-border/40" />

        <DropdownMenu>
          <DropdownMenuTrigger
            render={
              <button className="group flex items-center gap-2.5 rounded-full outline-none transition-all duration-200 hover:ring-2 hover:ring-primary/20 focus-visible:ring-2 focus-visible:ring-primary" />
            }
          >
            <div className="relative">
              <Avatar className="size-9 ring-2 ring-border/50 transition-all duration-200 group-hover:ring-primary/30">
                <AvatarFallback className="bg-gradient-to-br from-primary/20 to-primary/5 text-xs font-bold text-primary">
                  {initials}
                </AvatarFallback>
              </Avatar>
              {/* Online indicator */}
              <div className="absolute -bottom-0.5 -right-0.5 size-3 rounded-full border-2 border-background bg-emerald-400" />
            </div>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" sideOffset={8} className="w-60 overflow-hidden">
            <DropdownMenuLabel className="pb-3">
              <div className="flex flex-col gap-1">
                <span className="text-sm font-bold">{user?.name}</span>
                <span className="text-xs text-muted-foreground">
                  {user?.email}
                </span>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => router.push("/settings")}>
              <User className="size-4" />
              {t("nav.settings")}
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => router.push("/settings")}>
              <Settings className="size-4" />
              {t("settings.profile")}
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem variant="destructive" onClick={handleLogout}>
              <LogOut className="size-4" />
              {t("nav.logout")}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
