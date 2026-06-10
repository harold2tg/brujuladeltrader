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
    <header className="flex h-14 items-center justify-between border-b px-4 lg:px-6">
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
          <SheetContent side="left" className="w-64 p-0">
            <SheetTitle className="sr-only">
              {t("nav.dashboard")}
            </SheetTitle>
            <SidebarContent onNavClick={() => setSidebarOpen(false)} />
          </SheetContent>
        </Sheet>
      </div>

      {/* Right: language switcher + user dropdown */}
      <div className="flex items-center gap-2">
        <LanguageSwitcher />

        <DropdownMenu>
          <DropdownMenuTrigger
            render={
              <button className="flex items-center gap-2 rounded-full outline-none focus-visible:ring-2 focus-visible:ring-ring" />
            }
          >
            <Avatar>
              <AvatarFallback>{initials}</AvatarFallback>
            </Avatar>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" sideOffset={8}>
            <DropdownMenuLabel>
              <div className="flex flex-col">
                <span className="text-sm font-medium">{user?.name}</span>
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
