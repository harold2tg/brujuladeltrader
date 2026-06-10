import { create } from "zustand";
import { persist } from "zustand/middleware";

interface UIState {
  sidebarOpen: boolean;
  locale: "es" | "en";
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setLocale: (locale: "es" | "en") => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      locale: (process.env.NEXT_PUBLIC_DEFAULT_LOCALE as "es" | "en") || "es",

      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      setLocale: (locale) => set({ locale }),
    }),
    {
      name: "brujula-ui",
      partialize: (state) => ({ locale: state.locale }),
    },
  ),
);
