import type { ReactNode } from "react";
import { Compass } from "lucide-react";
import { LanguageSwitcher } from "@/components/layout/LanguageSwitcher";

interface AuthLayoutProps {
  children: ReactNode;
}

export default function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-4 py-8">
      {/* Language switcher — top right */}
      <div className="absolute top-4 right-4">
        <LanguageSwitcher />
      </div>

      {/* Logo */}
      <div className="mb-8 flex items-center gap-2">
        <Compass className="size-8 text-primary" />
        <span className="text-xl font-bold">La Brújula del Trader</span>
      </div>

      {/* Auth card */}
      <div className="w-full max-w-md">{children}</div>
    </div>
  );
}
