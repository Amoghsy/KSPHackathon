import { useAuthStore } from "@/stores/auth";
import { hasPermission, PERMISSIONS } from "@/lib/rbac";

export function useRBAC() {
  const user = useAuthStore((s) => s.user);

  return {
    user,
    role: user?.role,
    isLoading: false,

    // Capability flags based on roles/permissions matrix
    canSearchCases: hasPermission(user, PERMISSIONS.SEARCH_CASES),
    canViewCriminalNetwork: hasPermission(user, PERMISSIONS.CRIMINAL_NETWORK),
    canViewCrimeMap: hasPermission(user, PERMISSIONS.CRIME_MAP),
    canViewPatternAnalysis: hasPermission(user, PERMISSIONS.PATTERN_ANALYSIS),
    canUseChatAssistant: hasPermission(user, PERMISSIONS.CHAT_ASSISTANT),
    canViewFinancialCrime: hasPermission(user, PERMISSIONS.FINANCIAL_CRIME),
    canDetectGangs: hasPermission(user, PERMISSIONS.GANG_DETECTION),
    canAccessSensitiveCases: hasPermission(user, PERMISSIONS.SENSITIVE_CASE_ACCESS),
    canViewAuditLogs: hasPermission(user, PERMISSIONS.VIEW_AUDIT_LOGS),
    canManageUsers: hasPermission(user, PERMISSIONS.MANAGE_USERS),
    canConfigureSystem: hasPermission(user, PERMISSIONS.SYSTEM_CONFIGURATION),
    canExportData: hasPermission(user, PERMISSIONS.EXPORT_DATA),
  };
}
