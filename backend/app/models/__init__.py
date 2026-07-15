"""
app/models/__init__.py

Import all ORM model modules here so that:
1. Alembic autogenerate can discover all tables via Base.metadata.
2. A single `import app.models` anywhere in the codebase registers everything.
"""

from app.models.accused import AccusedMaster  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.case import CaseMaster  # noqa: F401
from app.models.crime_type import CrimeType  # noqa: F401
from app.models.financial_transaction import FinancialTransaction  # noqa: F401
from app.models.police_station import PoliceStation  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.victim import VictimMaster  # noqa: F401
from app.models.investigation_history import InvestigationHistory  # noqa: F401

