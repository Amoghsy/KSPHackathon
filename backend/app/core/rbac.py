from enum import Enum


class UserRole(str, Enum):
    INVESTIGATOR = "Investigator"
    SENIOR_INVESTIGATOR = "Senior Investigator"
    ANALYST = "Analyst"
    SUPERVISOR = "Supervisor"
    POLICYMAKER = "Policy Maker"
    POLICYMAKER_ALT = "Policymaker"
    ADMIN = "Admin"
    ADMIN_ALT = "Administrator"


class Permission:
    SEARCH_CASES = "search_cases"
    CRIMINAL_NETWORK = "criminal_network"
    CRIME_MAP = "crime_map"
    PATTERN_ANALYSIS = "pattern_analysis"
    CHAT_ASSISTANT = "chat_assistant"
    FINANCIAL_CRIME = "financial_crime"
    GANG_DETECTION = "gang_detection"
    SENSITIVE_CASE_ACCESS = "sensitive_case_access"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    MANAGE_USERS = "manage_users"
    SYSTEM_CONFIGURATION = "system_configuration"
    EXPORT_DATA = "export_data"


ROLE_PERMISSIONS = {
    "Investigator": {
        Permission.SEARCH_CASES,
        Permission.CRIMINAL_NETWORK,
        Permission.CRIME_MAP,
        Permission.PATTERN_ANALYSIS,
        Permission.CHAT_ASSISTANT,
    },
    "Senior Investigator": {
        Permission.SEARCH_CASES,
        Permission.CRIMINAL_NETWORK,
        Permission.CRIME_MAP,
        Permission.PATTERN_ANALYSIS,
        Permission.CHAT_ASSISTANT,
        Permission.FINANCIAL_CRIME,
        Permission.GANG_DETECTION,
        Permission.SENSITIVE_CASE_ACCESS,
    },
    "Analyst": {
        Permission.SEARCH_CASES,
        Permission.CRIME_MAP,
        Permission.PATTERN_ANALYSIS,
        Permission.CHAT_ASSISTANT,
    },
    "Supervisor": {
        Permission.SEARCH_CASES,
        Permission.CRIMINAL_NETWORK,
        Permission.CRIME_MAP,
        Permission.PATTERN_ANALYSIS,
        Permission.CHAT_ASSISTANT,
        Permission.FINANCIAL_CRIME,
        Permission.GANG_DETECTION,
        Permission.SENSITIVE_CASE_ACCESS,
        Permission.VIEW_AUDIT_LOGS,
    },
    "Admin": {
        Permission.SEARCH_CASES,
        Permission.CRIMINAL_NETWORK,
        Permission.CRIME_MAP,
        Permission.PATTERN_ANALYSIS,
        Permission.CHAT_ASSISTANT,
        Permission.FINANCIAL_CRIME,
        Permission.GANG_DETECTION,
        Permission.SENSITIVE_CASE_ACCESS,
        Permission.VIEW_AUDIT_LOGS,
        Permission.MANAGE_USERS,
        Permission.SYSTEM_CONFIGURATION,
        Permission.EXPORT_DATA,
    },
    "Administrator": {
        Permission.SEARCH_CASES,
        Permission.CRIMINAL_NETWORK,
        Permission.CRIME_MAP,
        Permission.PATTERN_ANALYSIS,
        Permission.CHAT_ASSISTANT,
        Permission.FINANCIAL_CRIME,
        Permission.GANG_DETECTION,
        Permission.SENSITIVE_CASE_ACCESS,
        Permission.VIEW_AUDIT_LOGS,
        Permission.MANAGE_USERS,
        Permission.SYSTEM_CONFIGURATION,
        Permission.EXPORT_DATA,
    },
    "Policy Maker": {
        Permission.SEARCH_CASES,
        Permission.CRIME_MAP,
        Permission.PATTERN_ANALYSIS,
        Permission.CHAT_ASSISTANT,
    },
    "Policymaker": {
        Permission.SEARCH_CASES,
        Permission.CRIME_MAP,
        Permission.PATTERN_ANALYSIS,
        Permission.CHAT_ASSISTANT,
    }
}


def check_permission(role: str, permission: str) -> bool:
    """Verify if a role has a specific permission."""
    perms = ROLE_PERMISSIONS.get(role, set())
    return permission in perms
