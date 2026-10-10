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
  DropdownMenuGroup,
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
    <header className="relative flex h-16 items-center justify-between border-b border-border bg-background/80 px-4 backdrop-blur-md lg:px-6">
      {/* Left: hamburger + mobile sheet */}
      <div className="flex items-center gap-2">
        <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
          <Button
            variant="ghost"
            size="icon-sm"
            className="text-muted-foreground transition-colors duration-150 hover:text-foreground lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="size-5" />
            <span className="sr-only">{t("common.openMenu")}</span>
          </Button>
          <SheetContent
            side="left"
            className="w-64 border-r border-border bg-sidebar p-0 text-sidebar-foreground"
          >
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
        <div className="h-5 w-px bg-border" />

        <DropdownMenu>
          <DropdownMenuTrigger
            render={
              <button className="group flex items-center gap-2.5 rounded-full outline-none transition-colors duration-150 hover:ring-2 hover:ring-primary/30 focus-visible:ring-2 focus-visible:ring-primary" />
            }
          >
            <div className="relative">
              <Avatar className="size-9 ring-2 ring-border transition-all duration-150 group-hover:ring-primary/40">
                <AvatarFallback className="bg-elevated text-xs font-bold text-primary">
                  {initials}
                </AvatarFallback>
              </Avatar>
              {/* Online indicator */}
              <div className="absolute -bottom-0.5 -right-0.5 size-3 rounded-full border-2 border-background bg-primary" />
            </div>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" sideOffset={8} className="w-60 overflow-hidden">
            <DropdownMenuGroup>
              <DropdownMenuLabel className="pb-3">
                <div className="flex flex-col gap-1">
                  <span className="text-sm font-semibold text-foreground">{user?.name}</span>
                  <span className="text-xs text-muted-foreground">
                    {user?.email}
                  </span>
                </div>
              </DropdownMenuLabel>
            </DropdownMenuGroup>
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
