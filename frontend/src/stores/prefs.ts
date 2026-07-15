import { create } from "zustand";
import { persist } from "zustand/middleware";

export type Lang = "en" | "kn";
export type Theme = "light" | "dark";

interface PrefsState {
  lang: Lang;
  theme: Theme;
  sidebarCollapsed: boolean;
  mobileNavOpen: boolean;
  setLang: (l: Lang) => void;
  setTheme: (t: Theme) => void;
  toggleTheme: () => void;
  toggleSidebar: () => void;
  setMobileNavOpen: (open: boolean) => void;
}

export const usePrefs = create<PrefsState>()(
  persist(
    (set, get) => ({
      lang: "en",
      theme: "light",
      sidebarCollapsed: false,
      mobileNavOpen: false,
      setLang: (lang) => set({ lang }),
      setTheme: (theme) => set({ theme }),
      toggleTheme: () => set({ theme: get().theme === "light" ? "dark" : "light" }),
      toggleSidebar: () => set({ sidebarCollapsed: !get().sidebarCollapsed }),
      setMobileNavOpen: (mobileNavOpen) => set({ mobileNavOpen }),
    }),
    {
      name: "cia-prefs",
      partialize: (s) => ({
        lang: s.lang,
        theme: s.theme,
        sidebarCollapsed: s.sidebarCollapsed,
      }),
    },
  ),
);
