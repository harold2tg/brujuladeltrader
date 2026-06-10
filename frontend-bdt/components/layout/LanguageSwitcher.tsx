"use client";

import { useLocale } from "next-intl";
import { useRouter, usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { GlobeIcon } from "lucide-react";

const localeLabels: Record<string, string> = {
  es: "ES",
  en: "EN",
};

const nextLocale: Record<string, string> = {
  es: "en",
  en: "es",
};

export function LanguageSwitcher() {
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();

  const toggleLocale = () => {
    const newLocale = nextLocale[locale] || "en";
    // Replace the locale segment in the pathname
    const newPath = pathname.replace(`/${locale}`, `/${newLocale}`);
    router.push(newPath);
  };

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={toggleLocale}
      className="gap-1.5 text-xs"
    >
      <GlobeIcon className="size-3.5" />
      {localeLabels[locale] || locale.toUpperCase()}
    </Button>
  );
}
