import type { Role, AuthUser } from "@/stores/auth";

export const PERMISSIONS = {
  SEARCH_CASES: "search_cases",
  CRIMINAL_NETWORK: "criminal_network",
  CRIME_MAP: "crime_map",
  PATTERN_ANALYSIS: "pattern_analysis",
  CHAT_ASSISTANT: "chat_assistant",
  FINANCIAL_CRIME: "financial_crime",
  GANG_DETECTION: "gang_detection",
  SENSITIVE_CASE_ACCESS: "sensitive_case_access",
  VIEW_AUDIT_LOGS: "view_audit_logs",
  MANAGE_USERS: "manage_users",
  SYSTEM_CONFIGURATION: "system_configuration",
  EXPORT_DATA: "export_data",
} as const;

export type Permission = (typeof PERMISSIONS)[keyof typeof PERMISSIONS];

export type RouteAccess = {
  path: string;
  moduleName: string;
  permissions?: Permission[];
  roles?: Role[];
  public?: boolean;
};

const ALL_PERMISSIONS = Object.values(PERMISSIONS);

export const ROLE_PERMISSIONS: Record<Role, Permission[]> = {
  Investigator: [
    PERMISSIONS.SEARCH_CASES,
    PERMISSIONS.CRIMINAL_NETWORK,
    PERMISSIONS.CRIME_MAP,
    PERMISSIONS.PATTERN_ANALYSIS,
    PERMISSIONS.CHAT_ASSISTANT,
  ],
  "Senior Investigator": [
    PERMISSIONS.SEARCH_CASES,
    PERMISSIONS.CRIMINAL_NETWORK,
    PERMISSIONS.CRIME_MAP,
    PERMISSIONS.PATTERN_ANALYSIS,
    PERMISSIONS.CHAT_ASSISTANT,
    PERMISSIONS.FINANCIAL_CRIME,
    PERMISSIONS.GANG_DETECTION,
    PERMISSIONS.SENSITIVE_CASE_ACCESS,
  ],
  Analyst: [
    PERMISSIONS.SEARCH_CASES,
    PERMISSIONS.CRIME_MAP,
    PERMISSIONS.PATTERN_ANALYSIS,
    PERMISSIONS.CHAT_ASSISTANT,
  ],
  Supervisor: [
    PERMISSIONS.SEARCH_CASES,
    PERMISSIONS.CRIMINAL_NETWORK,
    PERMISSIONS.CRIME_MAP,
    PERMISSIONS.PATTERN_ANALYSIS,
    PERMISSIONS.CHAT_ASSISTANT,
    PERMISSIONS.FINANCIAL_CRIME,
    PERMISSIONS.GANG_DETECTION,
    PERMISSIONS.SENSITIVE_CASE_ACCESS,
    PERMISSIONS.VIEW_AUDIT_LOGS,
    PERMISSIONS.EXPORT_DATA,
  ],
  Policymaker: [
    PERMISSIONS.SEARCH_CASES,
    PERMISSIONS.CRIME_MAP,
    PERMISSIONS.PATTERN_ANALYSIS,
    PERMISSIONS.CHAT_ASSISTANT,
    PERMISSIONS.EXPORT_DATA,
  ],
  Admin: ALL_PERMISSIONS,
};

export const ROUTE_ACCESS: RouteAccess[] = [
  { path: "/", moduleName: "Chat Assistant", permissions: [PERMISSIONS.CHAT_ASSISTANT] },
  { path: "/dashboard", moduleName: "Dashboard", permissions: [PERMISSIONS.SEARCH_CASES] },
  { path: "/cases", moduleName: "Case Search", permissions: [PERMISSIONS.SEARCH_CASES] },
  { path: "/offenders", moduleName: "Offender Profiles", permissions: [PERMISSIONS.SEARCH_CASES] },
  { path: "/network", moduleName: "Criminal Network", permissions: [PERMISSIONS.CRIMINAL_NETWORK] },
  { path: "/financial", moduleName: "Financial Crime", permissions: [PERMISSIONS.FINANCIAL_CRIME] },
  { path: "/map", moduleName: "Crime Map", permissions: [PERMISSIONS.CRIME_MAP] },
  { path: "/sociological", moduleName: "Pattern Intelligence", permissions: [PERMISSIONS.PATTERN_ANALYSIS] },
  { path: "/alerts", moduleName: "Alerts", permissions: [PERMISSIONS.PATTERN_ANALYSIS] },
  { path: "/audit", moduleName: "Audit Dashboard", permissions: [PERMISSIONS.VIEW_AUDIT_LOGS] },
  { path: "/admin", moduleName: "User Administration", permissions: [PERMISSIONS.MANAGE_USERS] },
  { path: "/settings", moduleName: "Settings", public: true },
  { path: "/access-restricted", moduleName: "Access Restricted", public: true },
];

const ROLE_LABELS: Record<Permission, string> = {
  [PERMISSIONS.SEARCH_CASES]: "Investigator, Crime Analyst, Supervisor, Policy Maker, or Administrator",
  [PERMISSIONS.CRIMINAL_NETWORK]: "Investigator, Senior Investigator, Supervisor, or Administrator",
  [PERMISSIONS.CRIME_MAP]: "Any authenticated SCRB role",
  [PERMISSIONS.PATTERN_ANALYSIS]: "Investigator, Crime Analyst, Supervisor, Policy Maker, or Administrator",
  [PERMISSIONS.CHAT_ASSISTANT]: "Any authenticated SCRB role",
  [PERMISSIONS.FINANCIAL_CRIME]: "Senior Investigator, Supervisor, or Administrator",
  [PERMISSIONS.GANG_DETECTION]: "Senior Investigator, Supervisor, or Administrator",
  [PERMISSIONS.SENSITIVE_CASE_ACCESS]: "Senior Investigator, Supervisor, or Administrator",
  [PERMISSIONS.VIEW_AUDIT_LOGS]: "Supervisor or Administrator",
  [PERMISSIONS.MANAGE_USERS]: "Administrator",
  [PERMISSIONS.SYSTEM_CONFIGURATION]: "Administrator",
  [PERMISSIONS.EXPORT_DATA]: "Supervisor, Policy Maker, or Administrator",
};

export function getPermissionsForRole(role?: Role): Permission[] {
  return role ? ROLE_PERMISSIONS[role] ?? [] : [];
}

export function hasPermission(user: Pick<AuthUser, "role" | "permissions"> | null | undefined, permission: Permission) {
  if (!user) return false;
  return (user.permissions?.length ? user.permissions : getPermissionsForRole(user.role)).includes(permission);
}

export function hasAnyPermission(
  user: Pick<AuthUser, "role" | "permissions"> | null | undefined,
  permissions: Permission[] = [],
) {
  if (permissions.length === 0) return true;
  return permissions.some((permission) => hasPermission(user, permission));
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

export function requiredRoleLabel(permissions?: Permission[]) {
  if (!permissions?.length) return "Authorized SCRB personnel";
  return permissions.map((permission) => ROLE_LABELS[permission]).join(" or ");
}

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
