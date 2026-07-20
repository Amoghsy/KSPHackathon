from enum import Enum


class UserRole(str, Enum):
    ADMINISTRATOR = "ADMINISTRATOR"
    SUPERVISOR = "SUPERVISOR"
    SENIOR_INVESTIGATOR = "SENIOR_INVESTIGATOR"
    INVESTIGATOR = "INVESTIGATOR"
    ANALYST = "ANALYST"
    POLICY_MAKER = "POLICY_MAKER"


class Permission:
    DASHBOARD = "DASHBOARD"
    SEARCH_CASES = "SEARCH_CASES"
    CHAT_ASSISTANT = "CHAT_ASSISTANT"
    CRIME_MAP = "CRIME_MAP"
    PATTERN_INTELLIGENCE = "PATTERN_INTELLIGENCE"
    CRIMINAL_NETWORK = "CRIMINAL_NETWORK"
    FINANCIAL_CRIME = "FINANCIAL_CRIME"
    GANG_DETECTION = "GANG_DETECTION"
    SENSITIVE_CASE_ACCESS = "SENSITIVE_CASE_ACCESS"
    VIEW_AUDIT_LOGS = "VIEW_AUDIT_LOGS"
    MANAGE_USERS = "MANAGE_USERS"
    MANAGE_ROLES = "MANAGE_ROLES"
    SYSTEM_CONFIGURATION = "SYSTEM_CONFIGURATION"
    EXPORT_REPORTS = "EXPORT_REPORTS"
    ASSIGN_DISTRICTS = "ASSIGN_DISTRICTS"
    APPROVE_ACCESS_REQUESTS = "APPROVE_ACCESS_REQUESTS"


# Centralized permission matrix enforcing the principal of least privilege
ROLE_PERMISSIONS = {
    UserRole.ADMINISTRATOR: {
        Permission.VIEW_AUDIT_LOGS,
        Permission.MANAGE_USERS,
        Permission.MANAGE_ROLES,
        Permission.SYSTEM_CONFIGURATION,
        Permission.ASSIGN_DISTRICTS,
    },
    UserRole.SUPERVISOR: {
        Permission.DASHBOARD,
        Permission.SEARCH_CASES,
        Permission.CHAT_ASSISTANT,
        Permission.CRIME_MAP,
        Permission.PATTERN_INTELLIGENCE,
        Permission.CRIMINAL_NETWORK,
        Permission.FINANCIAL_CRIME,
        Permission.GANG_DETECTION,
        Permission.SENSITIVE_CASE_ACCESS,
        Permission.VIEW_AUDIT_LOGS,
        Permission.EXPORT_REPORTS,
        Permission.ASSIGN_DISTRICTS,
        Permission.APPROVE_ACCESS_REQUESTS,
    },
    UserRole.SENIOR_INVESTIGATOR: {
        Permission.DASHBOARD,
        Permission.SEARCH_CASES,
        Permission.CHAT_ASSISTANT,
        Permission.CRIME_MAP,
        Permission.PATTERN_INTELLIGENCE,
        Permission.CRIMINAL_NETWORK,
        Permission.FINANCIAL_CRIME,
        Permission.GANG_DETECTION,
        Permission.SENSITIVE_CASE_ACCESS,
        Permission.EXPORT_REPORTS,
    },
    UserRole.INVESTIGATOR: {
        Permission.DASHBOARD,
        Permission.SEARCH_CASES,
        Permission.CHAT_ASSISTANT,
        Permission.CRIME_MAP,
        Permission.PATTERN_INTELLIGENCE,
        Permission.CRIMINAL_NETWORK,
        Permission.EXPORT_REPORTS,
    },
    UserRole.ANALYST: {
        Permission.DASHBOARD,
        Permission.SEARCH_CASES,
        Permission.CHAT_ASSISTANT,
        Permission.CRIME_MAP,
        Permission.PATTERN_INTELLIGENCE,
        Permission.EXPORT_REPORTS,
    },
    UserRole.POLICY_MAKER: {
        Permission.DASHBOARD,
        Permission.SEARCH_CASES,
        Permission.CHAT_ASSISTANT,
        Permission.CRIME_MAP,
        Permission.PATTERN_INTELLIGENCE,
    },
}


def normalize_role(role_str: str | None) -> str | None:
    """Normalize mixed case or legacy role names to canonical uppercase representation."""
    if not role_str:
        return None
    r = role_str.strip().lower().replace(" ", "_").replace("-", "_")
    if r in ("admin", "administrator"):
        return "ADMINISTRATOR"
    if r == "supervisor":
        return "SUPERVISOR"
    if r == "senior_investigator":
        return "SENIOR_INVESTIGATOR"
    if r == "investigator":
        return "INVESTIGATOR"
    if r == "analyst":
        return "ANALYST"
    if r in ("policy_maker", "policymaker"):
        return "POLICY_MAKER"
    return role_str.upper()


def check_permission(role: str | None, permission: str) -> bool:
    """Verify if a role has a specific permission with legacy fallback compatibility."""
    if not role:
        return False
    norm_role = normalize_role(role)
    perms = ROLE_PERMISSIONS.get(norm_role, set())
    
    # 1. Direct match check
    if permission in perms:
        return True
        
    # 2. Legacy fallback mapping
    legacy_map = {
        "pattern_analysis": "PATTERN_INTELLIGENCE",
        "export_data": "EXPORT_REPORTS",
        "search_cases": "SEARCH_CASES",
        "criminal_network": "CRIMINAL_NETWORK",
        "crime_map": "CRIME_MAP",
        "chat_assistant": "CHAT_ASSISTANT",
        "financial_crime": "FINANCIAL_CRIME",
        "gang_detection": "GANG_DETECTION",
        "sensitive_case_access": "SENSITIVE_CASE_ACCESS",
        "view_audit_logs": "VIEW_AUDIT_LOGS",
        "manage_users": "MANAGE_USERS",
        "system_configuration": "SYSTEM_CONFIGURATION",
    }
    
    mapped_perm = legacy_map.get(permission)
    if mapped_perm and mapped_perm in perms:
        return True
        
    # Handle direct match of mapped string
    norm_permission = permission.upper()
    if norm_permission in perms:
        return True
        
    return False
