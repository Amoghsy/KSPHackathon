import { Bell, Search, Sun, Moon, LogOut, Menu } from "lucide-react";
import { useNavigate } from "@tanstack/react-router";
import { useAuthStore } from "@/stores/auth";
import { usePrefs } from "@/stores/prefs";
import { useT } from "@/lib/i18n";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";

export function Topbar() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const { lang, setLang, theme, toggleTheme, setMobileNavOpen } = usePrefs();
  const navigate = useNavigate();
  const t = useT();

  const initials = user?.name.split(" ").map((n) => n[0]).slice(-2).join("") ?? "?";

  const roleColor: Record<string, string> = {
    Supervisor: "bg-primary text-primary-foreground",
    Investigator: "bg-info text-info-foreground",
    Analyst: "bg-chart-2/20 text-chart-2",
    Policymaker: "bg-warning text-warning-foreground",
  };

  return (
    <header
      className={cn(
        "sticky top-0 z-30 h-14 shrink-0 border-b border-border/60",
        "bg-card/60 backdrop-blur-xl",
        "grid grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-2 sm:gap-3 px-3 sm:px-4",
      )}
    >
      {/* Left cluster: mobile hamburger */}
      <div className="flex items-center gap-2 shrink-0">
        <button
          onClick={() => setMobileNavOpen(true)}
          className="md:hidden h-9 w-9 rounded-md hover:bg-accent flex items-center justify-center"
          aria-label="Open navigation"
        >
          <Menu className="h-5 w-5" />
        </button>
      </div>

      {/* Middle: search */}
      <div className="min-w-0 relative">
        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
        <input
          type="text"
          placeholder={t("search")}
          className={cn(
            "w-full h-9 rounded-lg border border-input/70 bg-background/60 backdrop-blur-md",
            "pl-9 pr-3 text-sm placeholder:text-muted-foreground",
            "focus:outline-none focus:ring-2 focus:ring-ring/40 focus:bg-background/90 transition-colors",
          )}
        />
      </div>

      {/* Right cluster */}
      <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
        <div className="hidden sm:flex items-center h-9 rounded-md border border-input/70 bg-background/40 backdrop-blur-md overflow-hidden text-xs">
          <button
            onClick={() => setLang("en")}
            className={cn(
              "h-full px-2.5 font-medium flex items-center transition-colors",
              lang === "en" ? "bg-primary text-primary-foreground" : "hover:bg-accent",
            )}
          >
            EN
          </button>
          <button
            onClick={() => setLang("kn")}
            className={cn(
              "h-full px-2.5 font-medium flex items-center transition-colors",
              lang === "kn" ? "bg-primary text-primary-foreground" : "hover:bg-accent",
            )}
          >
            KN
          </button>
        </div>

        <button
          onClick={toggleTheme}
          className="h-9 w-9 rounded-md hover:bg-accent flex items-center justify-center transition-colors"
          title={theme === "light" ? "Switch to dark" : "Switch to light"}
        >
          {theme === "light" ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
        </button>

        <button className="relative h-9 w-9 rounded-md hover:bg-accent flex items-center justify-center transition-colors">
          <Bell className="h-4 w-4" />
          <span className="absolute top-1 right-1 h-4 min-w-4 rounded-full bg-destructive text-[10px] font-medium text-destructive-foreground flex items-center justify-center px-1 ring-2 ring-card">
            3
          </span>
        </button>

        <div className="hidden md:block h-6 w-px bg-border/70 mx-0.5" />

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center gap-2 pl-1 pr-1.5 h-9 rounded-md hover:bg-accent transition-colors">
              <Avatar className="h-7 w-7">
                <AvatarFallback className="bg-primary text-primary-foreground text-xs font-semibold">
                  {initials}
                </AvatarFallback>
              </Avatar>
              <div className="hidden lg:flex flex-col text-left leading-tight min-w-0">
                <span className="text-xs font-medium truncate max-w-[120px]">{user?.name}</span>
                <span className="text-[10px] text-muted-foreground truncate">{user?.badgeNo}</span>
              </div>
              <Badge className={cn("hidden xl:inline-flex ml-1 text-[10px]", roleColor[user?.role ?? ""])}>
                {user?.role}
              </Badge>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56 glass-strong">
            <DropdownMenuLabel>
              <div className="text-sm font-medium">{user?.name}</div>
              <div className="text-xs text-muted-foreground">{user?.station}</div>
              <Badge className={cn("mt-1.5 text-[10px]", roleColor[user?.role ?? ""])}>
                {user?.role}
              </Badge>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => navigate({ to: "/settings" })}>
              {t("settings")}
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={() => {
                logout();
                navigate({ to: "/login" });
              }}
              className="text-destructive focus:text-destructive"
            >
              <LogOut className="h-4 w-4 mr-2" /> {t("signOut")}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
