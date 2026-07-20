import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.audit_agent.audit_agent import AuditAgent

logger = logging.getLogger(__name__)


async def log_security_event(
    db: AsyncSession,
    *,
    event_type: str,  # e.g., "LOGIN_SUCCESS", "LOGIN_FAILED", "OTP_FAILED", etc.
    user_id: int | None = None,
    username: str | None = None,
    role: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    target_user_id: int | None = None,
    reason: str | None = None,
    status: str = "success",
    summary: str | None = None
):
    """
    Log a security/authentication-related event to the central Audit Log.
    """
    agent = AuditAgent()
    request_id = str(uuid.uuid4())
    try:
        # Pass event_type to both api and action columns for maximum visibility
        await agent.log_action(
            db=db,
            user_id=user_id,
            username=username,
            role=role,
            api=event_type,
            action=event_type,
            ip_address=ip_address,
            user_agent=user_agent,
            target_user_id=target_user_id,
            reason=reason,
            request_id=request_id,
            status=status,
            summary=summary
        )
    except Exception as e:
        logger.error(f"Failed to log security audit event {event_type}: {str(e)}")
