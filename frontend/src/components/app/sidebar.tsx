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
  ChevronLeft,
  ShieldAlert,
  Shield,
} from "lucide-react";
import { useAuthStore } from "@/stores/auth";
import { usePrefs } from "@/stores/prefs";
import { useT, type DictKey } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import { hasAnyPermission, PERMISSIONS, type Permission } from "@/lib/rbac";

// ─────────────────────────────────────────────────────────────────────────────
// CENTRAL NAVIGATION DEFINITION
// Each item declares which permission is required to see it.
// Sidebar filters this list — unauthorized items are NEVER RENDERED.
// Do NOT add role-specific conditions here. Use permissions only.
// ─────────────────────────────────────────────────────────────────────────────
interface NavItem {
  to: string;
  labelKey: DictKey;
  icon: React.ComponentType<{ className?: string }>;
  /** If omitted or empty, item is visible to all authenticated users (e.g. Settings). */
  permissions?: Permission[];
}

const NAV: NavItem[] = [
  {
    to: "/",
    labelKey: "chat",
    icon: MessageSquare,
    permissions: [PERMISSIONS.CHAT_ASSISTANT],
  },
  {
    to: "/dashboard",
    labelKey: "dashboard",
    icon: LayoutDashboard,
    permissions: [PERMISSIONS.DASHBOARD],
  },
  {
    to: "/network",
    labelKey: "network",
    icon: Network,
    permissions: [PERMISSIONS.CRIMINAL_NETWORK],
  },
  {
    to: "/financial",
    labelKey: "financial",
    icon: Wallet,
    permissions: [PERMISSIONS.FINANCIAL_CRIME],
  },
  {
    to: "/map",
    labelKey: "map",
    icon: Map,
    permissions: [PERMISSIONS.CRIME_MAP],
  },
  {
    to: "/sociological",
    labelKey: "sociological",
    icon: PieChart,
    permissions: [PERMISSIONS.PATTERN_INTELLIGENCE],
  },
  {
    to: "/cases",
    labelKey: "cases",
    icon: FileSearch,
    permissions: [PERMISSIONS.SEARCH_CASES],
  },
  {
    to: "/offenders",
    labelKey: "offenders",
    icon: Users,
    permissions: [PERMISSIONS.SEARCH_CASES],
  },
  {
    to: "/alerts",
    labelKey: "alerts",
    icon: AlertTriangle,
    permissions: [PERMISSIONS.PATTERN_INTELLIGENCE],
  },
  {
    to: "/audit",
    labelKey: "audit",
    icon: ClipboardList,
    permissions: [PERMISSIONS.VIEW_AUDIT_LOGS],
  },
  {
    // Supervisor Panel: requires supervisory capability — NOT admin permission.
    // ADMINISTRATOR does not have ASSIGN_DISTRICTS or APPROVE_ACCESS_REQUESTS.
    to: "/supervisor",
    labelKey: "supervisor",
    icon: Shield,
    permissions: [PERMISSIONS.ASSIGN_DISTRICTS, PERMISSIONS.APPROVE_ACCESS_REQUESTS],
  },
  {
    // Admin Console: only users who can manage the platform
    to: "/admin",
    labelKey: "admin",
    icon: ShieldAlert,
    permissions: [PERMISSIONS.MANAGE_USERS],
  },
  {
    // Settings: accessible to all authenticated users (personal preferences)
    to: "/settings",
    labelKey: "settings",
    icon: SettingsIcon,
    // No permissions field → visible to all authenticated users
  },
];

import { useRBAC } from "@/hooks/useRBAC";

interface SidebarProps {
  forceExpanded?: boolean;
  onNavigate?: () => void;
}

export function DynamicSidebar({ forceExpanded, onNavigate }: SidebarProps = {}) {
  const { user } = useRBAC();
  const { sidebarCollapsed, toggleSidebar } = usePrefs();
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const t = useT();

  const collapsed = forceExpanded ? false : sidebarCollapsed;

  // ── Core filtering: only render items the current user has permission for.
  // Items without permissions are visible to all authenticated users.
  const items = NAV.filter((n) => !n.permissions || hasAnyPermission(user, n.permissions));

  return (
    <aside
      className={cn(
        "relative flex h-screen flex-col text-sidebar-foreground transition-[width] duration-300 border-r border-white/10",
        "backdrop-blur-xl",
        collapsed ? "w-16" : "w-64",
      )}
      style={{
        background: `
          radial-gradient(300px 300px at 0% 0%, oklch(0.4 0.1 220 / 0.45), transparent 80%),
          radial-gradient(300px 300px at 100% 100%, oklch(0.45 0.1 190 / 0.35), transparent 80%),
          linear-gradient(180deg, oklch(0.22 0.06 262 / 0.82) 0%, oklch(0.14 0.04 262 / 0.9) 100%)
        `,
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
          className="flex h-9 w-9 items-center justify-center rounded-lg shrink-0 overflow-hidden"
          style={{
            boxShadow: "0 4px 14px -4px oklch(0.65 0.12 190 / 0.3)",
          }}
        >
          <img src="/logo.png" alt="KSP Logo" className="h-full w-full object-cover" />
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

export { DynamicSidebar as Sidebar };
