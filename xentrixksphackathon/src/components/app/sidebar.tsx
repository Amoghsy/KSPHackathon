import { Link, useRouterState } from "@tanstack/react-router";
import {
  MessageSquare,
  LayoutDashboard,
  Network,
  Wallet,
  Map,
  PieChart,
  FileSearch,
  Users,
  AlertTriangle,
  ClipboardList,
  Settings as SettingsIcon,
  Shield,
  ChevronLeft,
} from "lucide-react";
import { useAuthStore, type Role } from "@/stores/auth";
import { usePrefs } from "@/stores/prefs";
import { useT, type DictKey } from "@/lib/i18n";
import { cn } from "@/lib/utils";

interface NavItem {
  to: string;
  labelKey: DictKey;
  icon: React.ComponentType<{ className?: string }>;
  roles?: Role[];
}

const NAV: NavItem[] = [
  { to: "/", labelKey: "chat", icon: MessageSquare },
  { to: "/dashboard", labelKey: "dashboard", icon: LayoutDashboard },
  { to: "/network", labelKey: "network", icon: Network, roles: ["Investigator", "Analyst", "Supervisor"] },
  { to: "/financial", labelKey: "financial", icon: Wallet, roles: ["Investigator", "Analyst", "Supervisor"] },
  { to: "/map", labelKey: "map", icon: Map },
  { to: "/sociological", labelKey: "sociological", icon: PieChart },
  { to: "/cases", labelKey: "cases", icon: FileSearch, roles: ["Investigator", "Analyst", "Supervisor"] },
  { to: "/offenders", labelKey: "offenders", icon: Users, roles: ["Investigator", "Analyst", "Supervisor"] },
  { to: "/alerts", labelKey: "alerts", icon: AlertTriangle },
  { to: "/audit", labelKey: "audit", icon: ClipboardList, roles: ["Supervisor"] },
  { to: "/settings", labelKey: "settings", icon: SettingsIcon },
];

interface SidebarProps {
  forceExpanded?: boolean;
  onNavigate?: () => void;
}

export function Sidebar({ forceExpanded, onNavigate }: SidebarProps = {}) {
  const role = useAuthStore((s) => s.user?.role);
  const { sidebarCollapsed, toggleSidebar } = usePrefs();
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const t = useT();

  const collapsed = forceExpanded ? false : sidebarCollapsed;
  const items = NAV.filter((n) => !n.roles || (role && n.roles.includes(role)));

  return (
    <aside
      className={cn(
        "relative flex h-screen flex-col text-sidebar-foreground transition-[width] duration-300 border-r border-sidebar-border/60",
        "bg-sidebar/85 backdrop-blur-2xl",
        collapsed ? "w-16" : "w-64",
      )}
      style={{
        boxShadow: "0 20px 60px -20px oklch(0 0 0 / 0.5)",
      }}
    >
      {/* subtle top accent line */}
      <div
        className="absolute inset-x-0 top-0 h-px"
        style={{
          background:
            "linear-gradient(90deg, transparent, oklch(0.65 0.12 190 / 0.5), transparent)",
        }}
      />

      <div className="flex items-center gap-2.5 px-4 py-4 border-b border-sidebar-border/60">
        <div
          className="flex h-9 w-9 items-center justify-center rounded-lg shrink-0 text-sidebar-primary-foreground"
          style={{
            background: "var(--gradient-teal)",
            boxShadow: "0 4px 14px -4px oklch(0.65 0.12 190 / 0.5)",
          }}
        >
          <Shield className="h-5 w-5" />
        </div>
        {!collapsed && (
          <div className="min-w-0">
            <div className="text-[10px] uppercase tracking-[0.18em] text-sidebar-foreground/60 font-medium">
              {t("brandLine1")}
            </div>
            <div className="text-sm font-semibold truncate">{t("brandLine2")}</div>
          </div>
        )}
      </div>

      <nav className="flex-1 overflow-y-auto py-3 scrollbar-thin">
        <ul className="space-y-0.5 px-2">
          {items.map((item) => {
            const active =
              item.to === "/"
                ? pathname === "/"
                : pathname === item.to || pathname.startsWith(item.to + "/");
            const Icon = item.icon;
            const label = t(item.labelKey);
            return (
              <li key={item.to}>
                <Link
                  to={item.to}
                  onClick={onNavigate}
                  className={cn(
                    "group relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all duration-200",
                    active
                      ? "bg-sidebar-accent/80 text-sidebar-accent-foreground font-medium"
                      : "text-sidebar-foreground/75 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground hover:translate-x-0.5",
                  )}
                  title={collapsed ? label : undefined}
                >
                  {active && (
                    <span
                      className="absolute left-0 top-1/2 -translate-y-1/2 h-6 w-0.5 rounded-r"
                      style={{
                        background: "var(--color-sidebar-primary)",
                        boxShadow: "0 0 12px 1px oklch(0.65 0.12 190 / 0.7)",
                      }}
                    />
                  )}
                  <Icon
                    className={cn(
                      "h-4 w-4 shrink-0 transition-colors",
                      active && "text-sidebar-primary",
                    )}
                  />
                  {!collapsed && <span className="truncate">{label}</span>}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {!forceExpanded && (
        <button
          onClick={toggleSidebar}
          className="hidden md:flex items-center justify-center gap-2 border-t border-sidebar-border/60 py-2.5 text-xs text-sidebar-foreground/60 hover:text-sidebar-foreground hover:bg-sidebar-accent/40 transition-colors"
        >
          <ChevronLeft className={cn("h-4 w-4 transition-transform", collapsed && "rotate-180")} />
          {!collapsed && <span>{t("collapse")}</span>}
        </button>
      )}
    </aside>
  );
}
