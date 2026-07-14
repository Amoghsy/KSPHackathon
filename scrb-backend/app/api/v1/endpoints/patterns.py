import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.analytics.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/trends")
async def get_trends(
    district: str | None = Query(None, description="Filter by district"),
    crime_type: str | None = Query(None, description="Filter by crime type"),
    police_station: str | None = Query(None, description="Filter by police station"),
    start_date: datetime.date | None = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: datetime.date | None = Query(None, description="End date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve daily and monthly crime trends with growth and frequency metrics."""
    service = AnalyticsService(db)
    res = await service.get_trends(
        district=district,
        crime_type=crime_type,
        police_station=police_station,
        start_date=start_date,
        end_date=end_date
    )
    return res


@router.get("/hotspots")
async def get_hotspots(
    district: str | None = Query(None, description="Filter by district"),
    crime_type: str | None = Query(None, description="Filter by crime type"),
    police_station: str | None = Query(None, description="Filter by police station"),
    start_date: datetime.date | None = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: datetime.date | None = Query(None, description="End date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve geographical clusters (DBSCAN) and district-level SVG map hotspot metrics."""
    service = AnalyticsService(db)
    res = await service.get_hotspots(
        district=district,
        crime_type=crime_type,
        police_station=police_station,
        start_date=start_date,
        end_date=end_date
    )
    return res


@router.get("/anomalies")
async def get_anomalies(
    district: str | None = Query(None, description="Filter by district"),
    crime_type: str | None = Query(None, description="Filter by crime type"),
    police_station: str | None = Query(None, description="Filter by police station"),
    start_date: datetime.date | None = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: datetime.date | None = Query(None, description="End date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
):
    """Identify unexpected spikes in crime count using Z-score checks."""
    service = AnalyticsService(db)
    res = await service.get_anomalies(
        district=district,
        crime_type=crime_type,
        police_station=police_station,
        start_date=start_date,
        end_date=end_date
    )
    return res


@router.get("/distribution")
async def get_distribution(
    district: str | None = Query(None, description="Filter by district"),
    crime_type: str | None = Query(None, description="Filter by crime type"),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve district distribution, solved vs pending rates, and demographics."""
    service = AnalyticsService(db)
    res = await service.get_distribution(
        district=district,
        crime_type=crime_type
    )
    return res


@router.get("/forecast")
async def get_forecast(
    district: str | None = Query(None, description="Filter by district"),
    crime_type: str | None = Query(None, description="Filter by crime type"),
    db: AsyncSession = Depends(get_db)
):
    """Generate linear regression and moving average forecasts for next month."""
    service = AnalyticsService(db)
    res = await service.get_forecast(
        district=district,
        crime_type=crime_type
    )
    return res


@router.get("/summary")
async def get_agent_summary(
    district: str | None = Query(None, description="Filter by district"),
    crime_type: str | None = Query(None, description="Filter by crime type"),
    police_station: str | None = Query(None, description="Filter by police station"),
    start_date: datetime.date | None = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: datetime.date | None = Query(None, description="End date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
):
    """Invoke the PatternAgent to analyze patterns and return Gemini summary briefing."""
    from app.agents.pattern_agent import PatternAgent
    agent = PatternAgent()
    res = await agent.analyze_patterns(
        db=db,
        district=district,
        crime_type=crime_type,
        police_station=police_station,
        start_date=start_date,
        end_date=end_date
    )
    return res
