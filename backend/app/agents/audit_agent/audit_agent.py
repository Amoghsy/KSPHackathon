import datetime
import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog
from app.core.redis import get_redis_client

logger = logging.getLogger(__name__)


class AuditAgent:
    """
    Audit Intelligence Agent.
    Logs system usage to PostgreSQL database and caches statistics in Redis
    to supply the real-time Admin Activity Dashboard.
    """
    async def log_action(
        self,
        db: AsyncSession,
        *,
        user_id: int | None,
        username: str | None,
        role: str | None,
        api: str,
        question: str | None = None,
        generated_sql: str | None = None,
        execution_time_ms: float | None = None,
        response_size: int | None = None,
        ip_address: str | None = None,
        request_id: str,
        status: str = "success",
        summary: str | None = None,
        action: str | None = None,
        target_user_id: int | None = None,
        supervisor_id: int | None = None,
        district_id: str | None = None,
        case_id: int | None = None,
        reason: str | None = None,
        user_agent: str | None = None
    ) -> None:
        try:
            # 1. Insert into database
            log = AuditLog(
                user_id=user_id,
                username=username,
                role=role,
                api=api,
                question=question,
                generated_sql=generated_sql,
                execution_time_ms=execution_time_ms,
                response_size=response_size,
                ip_address=ip_address,
                request_id=request_id,
                status=status,
                summary=summary,
                timestamp=datetime.datetime.utcnow(),
                action=action,
                target_user_id=target_user_id,
                supervisor_id=supervisor_id,
                district_id=district_id,
                case_id=case_id,
                reason=reason,
                user_agent=user_agent
            )
            db.add(log)
            await db.commit()
        except Exception as e:
            logger.error("Failed to write to DB audit log: %s", e)
            await db.rollback()

        # 2. Cache metrics in Redis for Admin Dashboard stats
        try:
            client = get_redis_client()
            today = datetime.datetime.utcnow().strftime("%Y-%m-%d")

            # Active Users
            if username:
                await client.sadd(f"audit:active_users:{today}", username)
                await client.expire(f"audit:active_users:{today}", 86400 * 2)

            # Investigations count today
            await client.incr(f"audit:investigations:{today}")
            await client.expire(f"audit:investigations:{today}", 86400 * 2)

            # Feature usage counter
            feature = api.strip("/").split("/")[0] if isinstance(api, str) and api else "chat"
            await client.hincrby(f"audit:features:{today}", feature, 1)
            await client.expire(f"audit:features:{today}", 86400 * 2)

            # Execution times (for average execution time)
            if execution_time_ms is not None:
                await client.lpush(f"audit:query_times:{today}", str(execution_time_ms))
                await client.ltrim(f"audit:query_times:{today}", 0, 99)  # Keep last 100 query times
                await client.expire(f"audit:query_times:{today}", 86400 * 2)

            # District viewed tracking (most active district)
            # Extracted from query/question or URL parameters
            district = None
            question_str = question.lower() if isinstance(question, str) else ""
            district_id_str = district_id.lower() if isinstance(district_id, str) else ""

            if "mysuru" in question_str or "mysuru" in district_id_str:
                district = "Mysuru"
            elif "bengaluru" in question_str or "bengaluru" in district_id_str:
                district = "Bengaluru"
            elif "mangalooru" in question_str or "mangaluru" in question_str or "mangalooru" in district_id_str or "mangaluru" in district_id_str:
                district = "Mangaluru"

            if district:
                await client.hincrby(f"audit:districts:{today}", district, 1)
                await client.expire(f"audit:districts:{today}", 86400 * 2)

            # Report generation tracking
            if isinstance(api, str) and ("export" in api or "report" in api):
                await client.incr(f"audit:reports:{today}")
                await client.expire(f"audit:reports:{today}", 86400 * 2)

        except Exception as re_err:
            logger.warning("Failed to cache audit stats in Redis: %s", re_err)
