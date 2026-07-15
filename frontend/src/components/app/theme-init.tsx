import { useEffect } from "react";
import { usePrefs } from "@/stores/prefs";

export function ThemeInit() {
  const theme = usePrefs((s) => s.theme);
  useEffect(() => {
    const root = document.documentElement;
    if (theme === "dark") root.classList.add("dark");
    else root.classList.remove("dark");
  }, [theme]);
  return null;
}
