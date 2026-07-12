from enum import Enum


class UserRole(str, Enum):
    INVESTIGATOR = "Investigator"
    ANALYST = "Analyst"
    SUPERVISOR = "Supervisor"
    POLICYMAKER = "Policymaker"
