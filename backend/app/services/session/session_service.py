import datetime
import uuid
import logging
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.session import UserSession

logger = logging.getLogger(__name__)


def parse_user_agent(user_agent: str | None) -> tuple[str, str, str, str]:
    """
    Derive best-effort device name, type, browser, and OS from User-Agent.
    """
    if not user_agent:
        return "Unknown Device", "Unknown", "Unknown", "Unknown"

    ua = user_agent.lower()

    # Browser detection
    if "edg/" in ua or "edge" in ua:
        browser = "Edge"
    elif "firefox" in ua or "fxios" in ua:
        browser = "Firefox"
    elif "chrome" in ua or "crios" in ua:
        browser = "Chrome"
    elif "safari" in ua and "version" in ua:
        browser = "Safari"
    else:
        browser = "Browser"

    # OS detection
    if "windows" in ua:
        os = "Windows"
    elif "macintosh" in ua or "mac os x" in ua:
        os = "macOS"
    elif "android" in ua:
        os = "Android"
    elif "iphone" in ua:
        os = "iOS"
    elif "ipad" in ua:
        os = "iPadOS"
    elif "linux" in ua:
        os = "Linux"
    else:
        os = "OS"

    # Device type detection
    if "mobile" in ua or "iphone" in ua or "android" in ua:
        device_type = "Mobile"
    elif "ipad" in ua or "tablet" in ua:
        device_type = "Tablet"
    else:
        device_type = "Desktop"

    device_name = f"{browser} on {os}"
    return device_name, device_type, browser, os


class SessionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        # Absolute session lifetime (default 24 hours if not configured)
        self.absolute_lifetime_hours = 24
        # Inactivity timeout (default 10 minutes)
        self.inactivity_minutes = 10

    async def create_session(
        self, user_id: int, ip_address: str, user_agent: str | None, token_identifier: str | None = None
    ) -> UserSession:
        """Create a new active device session for a user."""
        device_name, device_type, browser, os = parse_user_agent(user_agent)
        
        session_id = str(uuid.uuid4())
        now = datetime.datetime.now(datetime.timezone.utc)
        expires_at = now + datetime.timedelta(hours=self.absolute_lifetime_hours)

        session = UserSession(
            id=session_id,
            user_id=user_id,
            token_identifier=token_identifier,
            device_name=device_name,
            device_type=device_type,
            browser=browser,
            operating_system=os,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=now,
            last_activity_at=now,
            expires_at=expires_at,
            is_active=True,
        )

        self.db.add(session)
        await self.db.flush()
        logger.info(f"Created session {session_id} for user {user_id} ({device_name}, IP: {ip_address})")
        return session

    async def get_session(self, session_id: str) -> UserSession | None:
        """Retrieve a session by ID."""
        stmt = select(UserSession).where(UserSession.id == session_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_last_activity(self, session: UserSession) -> bool:
        """
        Throttled update of last_activity_at in DB to prevent excessive database writes.
        Only updates if the last write was more than 60 seconds ago.
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        elapsed = (now - session.last_activity_at).total_seconds()
        
        if elapsed > 60:
            session.last_activity_at = now
            self.db.add(session)
            await self.db.flush()
            return True
        return False

    async def revoke_session(self, session_id: str, revoked_by: int | None = None, reason: str | None = None) -> bool:
        """Revoke a specific session."""
        session = await self.get_session(session_id)
        if not session or not session.is_active:
            return False

        now = datetime.datetime.now(datetime.timezone.utc)
        session.is_active = False
        session.revoked_at = now
        session.revoked_by = revoked_by
        session.revoke_reason = reason or "LOGOUT"
        
        self.db.add(session)
        await self.db.flush()
        logger.info(f"Session {session_id} revoked by {revoked_by}. Reason: {reason}")
        return True

    async def revoke_all_user_sessions(self, user_id: int, except_session_id: str | None = None, revoked_by: int | None = None, reason: str | None = None) -> None:
        """Revoke all sessions for a user (optionally keeping one active)."""
        now = datetime.datetime.now(datetime.timezone.utc)
        stmt = (
            update(UserSession)
            .where(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            )
        )
        if except_session_id:
            stmt = stmt.where(UserSession.id != except_session_id)

        stmt = stmt.values(
            is_active=False,
            revoked_at=now,
            revoked_by=revoked_by,
            revoke_reason=reason or "REVOKE_ALL"
        )
        await self.db.execute(stmt)
        await self.db.flush()
        logger.info(f"Revoked all sessions for user {user_id} (except: {except_session_id})")

    async def get_active_sessions(self, user_id: int) -> list[UserSession]:
        """List all active sessions for a user."""
        now = datetime.datetime.now(datetime.timezone.utc)
        stmt = (
            select(UserSession)
            .where(
                UserSession.user_id == user_id,
                UserSession.is_active == True,
                UserSession.expires_at > now,
                UserSession.revoked_at == None
            )
            .order_by(UserSession.last_activity_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
