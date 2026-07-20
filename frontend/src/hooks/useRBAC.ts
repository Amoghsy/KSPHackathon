import { useAuthStore } from "@/stores/auth";
import { hasPermission, PERMISSIONS } from "@/lib/rbac";

export function useRBAC() {
  const user = useAuthStore((s) => s.user);

  return {
    user,
    role: user?.role,
    isLoading: false,

    // Capability flags derived from central permission model
    canSearchCases: hasPermission(user, PERMISSIONS.SEARCH_CASES),
    canViewCriminalNetwork: hasPermission(user, PERMISSIONS.CRIMINAL_NETWORK),
    canViewCrimeMap: hasPermission(user, PERMISSIONS.CRIME_MAP),
    canViewPatternAnalysis: hasPermission(user, PERMISSIONS.PATTERN_INTELLIGENCE),
    canUseChatAssistant: hasPermission(user, PERMISSIONS.CHAT_ASSISTANT),
    canViewFinancialCrime: hasPermission(user, PERMISSIONS.FINANCIAL_CRIME),
    canDetectGangs: hasPermission(user, PERMISSIONS.GANG_DETECTION),
    canAccessSensitiveCases: hasPermission(user, PERMISSIONS.SENSITIVE_CASE_ACCESS),
    canViewAuditLogs: hasPermission(user, PERMISSIONS.VIEW_AUDIT_LOGS),
    canManageUsers: hasPermission(user, PERMISSIONS.MANAGE_USERS),
    canManageRoles: hasPermission(user, PERMISSIONS.MANAGE_ROLES),
    canConfigureSystem: hasPermission(user, PERMISSIONS.SYSTEM_CONFIGURATION),
    canExportData: hasPermission(user, PERMISSIONS.EXPORT_REPORTS),
    canAssignDistricts: hasPermission(user, PERMISSIONS.ASSIGN_DISTRICTS),
    canApproveAccessRequests: hasPermission(user, PERMISSIONS.APPROVE_ACCESS_REQUESTS),
    canAccessDashboard: hasPermission(user, PERMISSIONS.DASHBOARD),
  };
}
