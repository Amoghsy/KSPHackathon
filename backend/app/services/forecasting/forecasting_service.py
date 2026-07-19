import hashlib
import json
import logging
import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.core.redis import get_redis_client
from app.core.permissions import get_user_authorized_districts, resolve_authorized_districts
from app.core.rbac import normalize_role
from app.models.case import CaseMaster
from app.models.police_station import PoliceStation
from app.models.crime_type import CrimeType
from app.services.forecasting.arima_model import forecast_arima_or_fallback

logger = logging.getLogger(__name__)

class ForecastingService:
    """
    Forecasting service coordinating historical monthly query construction,
    ABAC verification, forecasting model execution, and caching.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_crime_forecast(
        self,
        current_user: dict | None,
        district: str | None = None,
        crime_type: str | None = None,
        periods: int = 3
    ) -> dict:
        """
        Fetch historical trends and project future counts with cache and ABAC isolation.
        """
        # 1. Enforce RBAC
        # Administrators are strictly barred from viewing investigative/forecasting details
        if current_user:
            role = normalize_role(current_user.get("role"))
            if role == "ADMINISTRATOR":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Administrators do not have permission to view advanced crime forecasting."
                )

        # 2. Enforce ABAC
        auth_districts_raw = await get_user_authorized_districts(current_user, self.db)
        auth_districts = resolve_authorized_districts(auth_districts_raw)

        # If district is requested, check access
        if district and district != "All":
            if auth_districts is not None and district not in auth_districts:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied for district: {district}."
                )
        
        # 3. Check Redis Cache
        auth_str = ",".join(sorted(auth_districts)) if auth_districts else "__ALL__"
        cache_key = f"forecast:{auth_str}:{district or 'all'}:{crime_type or 'all'}:{periods}"

        try:
            redis_client = get_redis_client()
            cached = await redis_client.get(cache_key)
            if cached:
                logger.info("ForecastingService CACHE HIT key=%s", cache_key)
                return json.loads(cached)
        except Exception as exc:
            logger.warning("Redis read error in ForecastingService (non-fatal): %s", exc)

        # 4. Fetch history from DB
        month_trunc = func.date_trunc('month', CaseMaster.crime_registered_date)
        stmt = (
            select(month_trunc.label('month_date'), func.count(CaseMaster.case_master_id).label('count'))
            .select_from(CaseMaster)
            .group_by(month_trunc)
            .order_by(month_trunc)
        )

        conditions = []
        has_joined_ps = False

        if district and district != "All":
            stmt = stmt.join(CaseMaster.police_station)
            conditions.append(PoliceStation.district == district)
            has_joined_ps = True
        elif auth_districts is not None:
            stmt = stmt.join(CaseMaster.police_station)
            conditions.append(PoliceStation.district.in_(auth_districts))
            has_joined_ps = True

        if crime_type and crime_type != "All":
            stmt = stmt.join(CaseMaster.crime_type)
            conditions.append(CrimeType.name == crime_type)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        res = await self.db.execute(stmt)
        history_rows = res.all()

        # Parse history into list of values and labels
        history_data = []
        history_values = []
        for r in history_rows:
            if r.month_date:
                m_str = r.month_date.strftime("%Y-%m")
                history_data.append({"month": m_str, "count": r.count})
                history_values.append(r.count)

        # 5. Generate Forecast
        forecast_res = forecast_arima_or_fallback(history_values, periods=periods)

        # Append forecast months to labels using calendar addition
        last_date = None
        if history_rows and history_rows[-1].month_date:
            last_date = history_rows[-1].month_date
        else:
            last_date = datetime.datetime.utcnow()

        forecast_data = []
        current_year = last_date.year
        current_month = last_date.month

        for idx, val in enumerate(forecast_res["forecast"]):
            current_month += 1
            if current_month > 12:
                current_month = 1
                current_year += 1
            m_str = f"{current_year}-{current_month:02d}"
            forecast_data.append({"month": m_str, "count": val})

        result = {
            "history": history_data,
            "forecast": forecast_data,
            "method": forecast_res["method"],
            "confidence": forecast_res["confidence"]
        }

        # 6. Save to Cache
        try:
            redis_client = get_redis_client()
            await redis_client.set(cache_key, json.dumps(result), ex=300)
            logger.info("ForecastingService CACHE SET key=%s", cache_key)
        except Exception as exc:
            logger.warning("Redis write error in ForecastingService (non-fatal): %s", exc)

        return result
