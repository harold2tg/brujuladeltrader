import type { ReactNode } from "react";
import { Compass } from "lucide-react";
import { LanguageSwitcher } from "@/components/layout/LanguageSwitcher";

interface AuthLayoutProps {
  children: ReactNode;
}

export default function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden bg-background px-4 py-8">
      {/* Gradient mesh background — subtle terminal glow */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/4 top-1/4 size-[500px] rounded-full bg-primary/[0.025] blur-[120px]" />
        <div className="absolute bottom-1/4 right-1/4 size-[400px] rounded-full bg-primary/[0.02] blur-[100px]" />
      </div>

      {/* Grid pattern overlay — barely visible terminal texture */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.04]"
        style={{
          backgroundImage: `linear-gradient(var(--border) 1px, transparent 1px), linear-gradient(90deg, var(--border) 1px, transparent 1px)`,
          backgroundSize: "64px 64px",
        }}
      />

      {/* Language switcher — top right */}
      <div className="absolute right-4 top-4 z-10">
        <LanguageSwitcher />
      </div>

      {/* Logo */}
      <div className="relative z-10 mb-10 flex items-center gap-4">
        <div className="flex size-12 items-center justify-center rounded-xl border border-border bg-card">
          <Compass className="size-6 text-primary" />
        </div>
        <div className="flex flex-col">
          <span className="text-2xl font-bold tracking-tight text-foreground">La Brújula</span>
          <span className="text-[11px] font-semibold uppercase tracking-[0.25em] text-muted-foreground">
            del Trader
          </span>
        </div>
      </div>

      {/* Auth card */}
      <div className="relative z-10 w-full max-w-md">{children}</div>

      {/* Footer */}
      <div className="relative z-10 mt-8">
        <p className="text-[11px] text-muted-foreground">
          XAUUSD Statistical Analysis Platform
        </p>
      </div>
    </div>
  );
}
