import type { Role, AuthUser } from "@/stores/auth";

// ─────────────────────────────────────────────────────────────────────────────
// CANONICAL PERMISSIONS — kept in sync with backend app/core/rbac.py
// Do NOT add role-specific logic here. One source of truth only.
// ─────────────────────────────────────────────────────────────────────────────
export const PERMISSIONS = {
  // Operational / investigative
  DASHBOARD: "DASHBOARD",
  SEARCH_CASES: "SEARCH_CASES",
  CHAT_ASSISTANT: "CHAT_ASSISTANT",
  CRIME_MAP: "CRIME_MAP",
  PATTERN_INTELLIGENCE: "PATTERN_INTELLIGENCE",
  CRIMINAL_NETWORK: "CRIMINAL_NETWORK",
  FINANCIAL_CRIME: "FINANCIAL_CRIME",
  GANG_DETECTION: "GANG_DETECTION",
  SENSITIVE_CASE_ACCESS: "SENSITIVE_CASE_ACCESS",
  EXPORT_REPORTS: "EXPORT_REPORTS",

  // Supervisory
  VIEW_AUDIT_LOGS: "VIEW_AUDIT_LOGS",
  ASSIGN_DISTRICTS: "ASSIGN_DISTRICTS",
  APPROVE_ACCESS_REQUESTS: "APPROVE_ACCESS_REQUESTS",

  // Administrative
  MANAGE_USERS: "MANAGE_USERS",
  MANAGE_ROLES: "MANAGE_ROLES",
  SYSTEM_CONFIGURATION: "SYSTEM_CONFIGURATION",

  // ── Legacy aliases kept for backward compatibility with existing components ──
  // Do NOT use these in new code. Use the canonical names above.
  /** @deprecated use PATTERN_INTELLIGENCE */
  PATTERN_ANALYSIS: "PATTERN_INTELLIGENCE",
  /** @deprecated use EXPORT_REPORTS */
  EXPORT_DATA: "EXPORT_REPORTS",
} as const;

export type Permission = (typeof PERMISSIONS)[keyof typeof PERMISSIONS];

export type RouteAccess = {
  path: string;
  moduleName: string;
  permissions?: Permission[];
  roles?: Role[];
  public?: boolean;
};

// ─────────────────────────────────────────────────────────────────────────────
// ROLE → PERMISSIONS MAP
// Exact mirror of backend ROLE_PERMISSIONS in app/core/rbac.py
// ADMINISTRATOR is a platform admin — NOT an investigator.
// ─────────────────────────────────────────────────────────────────────────────
export const ROLE_PERMISSIONS: Record<Role, Permission[]> = {
  ADMINISTRATOR: [
    PERMISSIONS.VIEW_AUDIT_LOGS,
    PERMISSIONS.MANAGE_USERS,
    PERMISSIONS.MANAGE_ROLES,
    PERMISSIONS.SYSTEM_CONFIGURATION,
  ],

  SUPERVISOR: [
    PERMISSIONS.DASHBOARD,
    PERMISSIONS.SEARCH_CASES,
    PERMISSIONS.CHAT_ASSISTANT,
    PERMISSIONS.CRIME_MAP,
    PERMISSIONS.PATTERN_INTELLIGENCE,
    PERMISSIONS.CRIMINAL_NETWORK,
    PERMISSIONS.FINANCIAL_CRIME,
    PERMISSIONS.GANG_DETECTION,
    PERMISSIONS.SENSITIVE_CASE_ACCESS,
    PERMISSIONS.VIEW_AUDIT_LOGS,
    PERMISSIONS.EXPORT_REPORTS,
    PERMISSIONS.ASSIGN_DISTRICTS,
    PERMISSIONS.APPROVE_ACCESS_REQUESTS,
  ],

  SENIOR_INVESTIGATOR: [
    PERMISSIONS.DASHBOARD,
    PERMISSIONS.SEARCH_CASES,
    PERMISSIONS.CHAT_ASSISTANT,
    PERMISSIONS.CRIME_MAP,
    PERMISSIONS.PATTERN_INTELLIGENCE,
    PERMISSIONS.CRIMINAL_NETWORK,
    PERMISSIONS.FINANCIAL_CRIME,
    PERMISSIONS.GANG_DETECTION,
    PERMISSIONS.SENSITIVE_CASE_ACCESS,
    PERMISSIONS.EXPORT_REPORTS,
  ],

  INVESTIGATOR: [
    PERMISSIONS.DASHBOARD,
    PERMISSIONS.SEARCH_CASES,
    PERMISSIONS.CHAT_ASSISTANT,
    PERMISSIONS.CRIME_MAP,
    PERMISSIONS.PATTERN_INTELLIGENCE,
    PERMISSIONS.CRIMINAL_NETWORK,
    PERMISSIONS.EXPORT_REPORTS,
  ],

  ANALYST: [
    PERMISSIONS.DASHBOARD,
    PERMISSIONS.SEARCH_CASES,
    PERMISSIONS.CHAT_ASSISTANT,
    PERMISSIONS.CRIME_MAP,
    PERMISSIONS.PATTERN_INTELLIGENCE,
    PERMISSIONS.EXPORT_REPORTS,
  ],

  POLICY_MAKER: [
    PERMISSIONS.DASHBOARD,
    PERMISSIONS.SEARCH_CASES,
    PERMISSIONS.CHAT_ASSISTANT,
    PERMISSIONS.CRIME_MAP,
    PERMISSIONS.PATTERN_INTELLIGENCE,
  ],
};

// ─────────────────────────────────────────────────────────────────────────────
// ROUTE ACCESS — maps paths to required permissions for route guards.
// The _app.tsx beforeLoad checks these to redirect unauthorized access.
// ─────────────────────────────────────────────────────────────────────────────
export const ROUTE_ACCESS: RouteAccess[] = [
  { path: "/", moduleName: "Chat Assistant", permissions: [PERMISSIONS.CHAT_ASSISTANT] },
  { path: "/dashboard", moduleName: "Dashboard", permissions: [PERMISSIONS.DASHBOARD] },
  { path: "/cases", moduleName: "Case Search", permissions: [PERMISSIONS.SEARCH_CASES] },
  { path: "/offenders", moduleName: "Offender Profiles", permissions: [PERMISSIONS.SEARCH_CASES] },
  { path: "/network", moduleName: "Criminal Network", permissions: [PERMISSIONS.CRIMINAL_NETWORK] },
  { path: "/financial", moduleName: "Financial Crime", permissions: [PERMISSIONS.FINANCIAL_CRIME] },
  { path: "/map", moduleName: "Crime Map", permissions: [PERMISSIONS.CRIME_MAP] },
  { path: "/sociological", moduleName: "Pattern Intelligence", permissions: [PERMISSIONS.PATTERN_INTELLIGENCE] },
  { path: "/alerts", moduleName: "Investigation Alerts", permissions: [PERMISSIONS.PATTERN_INTELLIGENCE] },
  { path: "/audit", moduleName: "Audit Log", permissions: [PERMISSIONS.VIEW_AUDIT_LOGS] },
  // Supervisor Panel requires supervisory permissions — NOT admin permissions
  {
    path: "/supervisor",
    moduleName: "Supervisor Panel",
    permissions: [PERMISSIONS.ASSIGN_DISTRICTS, PERMISSIONS.APPROVE_ACCESS_REQUESTS],
  },
  { path: "/admin", moduleName: "Admin Console", permissions: [PERMISSIONS.MANAGE_USERS] },
  { path: "/settings", moduleName: "Settings", public: true },
  { path: "/access-restricted", moduleName: "Access Restricted", public: true },
];

// ─────────────────────────────────────────────────────────────────────────────
// DEFAULT LANDING PAGE per role
// Used by _app.tsx to redirect users to their appropriate home page after login.
// ─────────────────────────────────────────────────────────────────────────────
export const ROLE_DEFAULT_LANDING: Record<Role, string> = {
  ADMINISTRATOR: "/admin",
  SUPERVISOR: "/dashboard",
  SENIOR_INVESTIGATOR: "/dashboard",
  INVESTIGATOR: "/dashboard",
  ANALYST: "/dashboard",
  POLICY_MAKER: "/dashboard",
};

// ─────────────────────────────────────────────────────────────────────────────
// PERMISSION HELPERS
// ─────────────────────────────────────────────────────────────────────────────

export function getPermissionsForRole(role?: Role): Permission[] {
  return role ? (ROLE_PERMISSIONS[role] ?? []) : [];
}

export function hasPermission(
  user: Pick<AuthUser, "role" | "permissions"> | null | undefined,
  permission: Permission,
) {
  if (!user) return false;
  const effectivePerms = user.permissions?.length ? user.permissions : getPermissionsForRole(user.role);
  return effectivePerms.includes(permission);
}

export function hasAnyPermission(
  user: Pick<AuthUser, "role" | "permissions"> | null | undefined,
  permissions: Permission[] = [],
) {
  if (permissions.length === 0) return true;
  return permissions.some((permission) => hasPermission(user, permission));
}

export function hasAllPermissions(
  user: Pick<AuthUser, "role" | "permissions"> | null | undefined,
  permissions: Permission[] = [],
) {
  if (permissions.length === 0) return true;
  return permissions.every((permission) => hasPermission(user, permission));
}

export function canAccessRoute(user: AuthUser | null | undefined, route: RouteAccess) {
  if (route.public) return true;
  if (!user) return false;
  const roleOk = !route.roles?.length || route.roles.includes(user.role);
  return roleOk && hasAnyPermission(user, route.permissions);
}

export function findRouteAccess(pathname: string) {
  return ROUTE_ACCESS
    .filter((route) => pathname === route.path || pathname.startsWith(route.path + "/"))
    .sort((a, b) => b.path.length - a.path.length)[0];
}

// ─────────────────────────────────────────────────────────────────────────────
// HUMAN-READABLE LABELS
// ─────────────────────────────────────────────────────────────────────────────
const PERMISSION_LABELS: Partial<Record<Permission, string>> = {
  [PERMISSIONS.SEARCH_CASES]: "Investigator, Analyst, Supervisor, Policy Maker",
  [PERMISSIONS.CRIMINAL_NETWORK]: "Investigator, Senior Investigator, or Supervisor",
  [PERMISSIONS.CRIME_MAP]: "Any authenticated SCRB role",
  [PERMISSIONS.PATTERN_INTELLIGENCE]: "Investigator, Analyst, Supervisor, or Policy Maker",
  [PERMISSIONS.CHAT_ASSISTANT]: "Any authenticated SCRB role",
  [PERMISSIONS.FINANCIAL_CRIME]: "Senior Investigator or Supervisor",
  [PERMISSIONS.GANG_DETECTION]: "Senior Investigator or Supervisor",
  [PERMISSIONS.SENSITIVE_CASE_ACCESS]: "Senior Investigator or Supervisor",
  [PERMISSIONS.VIEW_AUDIT_LOGS]: "Supervisor or Administrator",
  [PERMISSIONS.MANAGE_USERS]: "Administrator",
  [PERMISSIONS.SYSTEM_CONFIGURATION]: "Administrator",
  [PERMISSIONS.EXPORT_REPORTS]: "Investigator, Senior Investigator, Supervisor, or Analyst",
  [PERMISSIONS.ASSIGN_DISTRICTS]: "Supervisor",
  [PERMISSIONS.APPROVE_ACCESS_REQUESTS]: "Supervisor",
  [PERMISSIONS.DASHBOARD]: "Investigator, Analyst, Supervisor, Senior Investigator, or Policy Maker",
};

export function requiredRoleLabel(permissions?: Permission[]) {
  if (!permissions?.length) return "Authorized SCRB personnel";
  return permissions
    .map((p) => PERMISSION_LABELS[p] ?? p)
    .join(" or ");
}

// ─────────────────────────────────────────────────────────────────────────────
// DATA MASKING UTILITIES
// ─────────────────────────────────────────────────────────────────────────────
export function maskName(value?: string | null) {
  if (!value) return "Hidden";
  const trimmed = value.trim();
  if (trimmed.length <= 2) return trimmed[0] + "*";
  return `${trimmed[0]}${"*".repeat(Math.min(trimmed.length - 2, 8))}${trimmed[trimmed.length - 1]}`;
}

export function maskPhone(value?: string | null) {
  if (!value) return "Hidden";
  const digits = value.replace(/\D/g, "");
  if (digits.length < 4) return "Hidden";
  return `${digits.slice(0, 2)}${"*".repeat(Math.max(2, digits.length - 4))}${digits.slice(-2)}`;
}

export function maskAccount(value?: string | null) {
  if (!value) return "Hidden";
  const clean = value.replace(/\s/g, "");
  return `XXXXXX${clean.slice(-4)}`;
}
