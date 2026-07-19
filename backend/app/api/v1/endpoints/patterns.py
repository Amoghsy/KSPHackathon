import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.analytics.analytics_service import AnalyticsService
from app.core.security import get_current_user
from app.core.permissions import require_permission, verify_district_access, get_user_authorized_districts
from app.core.rbac import Permission

router = APIRouter()


@router.get("/trends")
async def get_trends(
    district: str | None = Query(None, description="Filter by district"),
    crime_type: str | None = Query(None, description="Filter by crime type"),
    police_station: str | None = Query(None, description="Filter by police station"),
    start_date: datetime.date | None = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: datetime.date | None = Query(None, description="End date (YYYY-MM-DD)"),
    gravity: str | None = Query(None, description="Filter by gravity"),
    status: str | None = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Retrieve daily and monthly crime trends with growth and frequency metrics."""
    check_perm = require_permission(Permission.PATTERN_INTELLIGENCE)
    await check_perm(current_user)

    allowed_district = await verify_district_access(current_user, district, db)
    auth_districts = await get_user_authorized_districts(current_user, db)

    service = AnalyticsService(db, authorized_districts=auth_districts)
    res = await service.get_trends(
        district=allowed_district,
        crime_type=crime_type,
        police_station=police_station,
        start_date=start_date,
        end_date=end_date,
        gravity=gravity,
        status=status
    )
    return res


@router.get("/hotspots")
async def get_hotspots(
    district: str | None = Query(None, description="Filter by district"),
    crime_type: str | None = Query(None, description="Filter by crime type"),
    police_station: str | None = Query(None, description="Filter by police station"),
    start_date: datetime.date | None = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: datetime.date | None = Query(None, description="End date (YYYY-MM-DD)"),
    gravity: str | None = Query(None, description="Filter by gravity"),
    status: str | None = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Retrieve geographical clusters (DBSCAN) and district-level SVG map hotspot metrics."""
    check_perm = require_permission(Permission.CRIME_MAP)
    await check_perm(current_user)

    allowed_district = await verify_district_access(current_user, district, db)
    auth_districts = await get_user_authorized_districts(current_user, db)

    service = AnalyticsService(db, authorized_districts=auth_districts)
    res = await service.get_hotspots(
        district=allowed_district,
        crime_type=crime_type,
        police_station=police_station,
        start_date=start_date,
        end_date=end_date,
        gravity=gravity,
        status=status
    )
    return res


@router.get("/anomalies")
async def get_anomalies(
    district: str | None = Query(None, description="Filter by district"),
    crime_type: str | None = Query(None, description="Filter by crime type"),
    police_station: str | None = Query(None, description="Filter by police station"),
    start_date: datetime.date | None = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: datetime.date | None = Query(None, description="End date (YYYY-MM-DD)"),
    gravity: str | None = Query(None, description="Filter by gravity"),
    status: str | None = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Identify unexpected spikes in crime count using Z-score checks."""
    check_perm = require_permission(Permission.PATTERN_INTELLIGENCE)
    await check_perm(current_user)

    allowed_district = await verify_district_access(current_user, district, db)
    auth_districts = await get_user_authorized_districts(current_user, db)

    service = AnalyticsService(db, authorized_districts=auth_districts)
    res = await service.get_anomalies(
        district=allowed_district,
        crime_type=crime_type,
        police_station=police_station,
        start_date=start_date,
        end_date=end_date,
        gravity=gravity,
        status=status
    )
    return res


@router.get("/distribution")
async def get_distribution(
    district: str | None = Query(None, description="Filter by district"),
    crime_type: str | None = Query(None, description="Filter by crime type"),
    gravity: str | None = Query(None, description="Filter by gravity"),
    status: str | None = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Retrieve district distribution, solved vs pending rates, and demographics."""
    check_perm = require_permission(Permission.PATTERN_INTELLIGENCE)
    await check_perm(current_user)

    allowed_district = await verify_district_access(current_user, district, db)
    auth_districts = await get_user_authorized_districts(current_user, db)

    service = AnalyticsService(db, authorized_districts=auth_districts)
    res = await service.get_distribution(
        district=allowed_district,
        crime_type=crime_type,
        gravity=gravity,
        status=status
    )
    return res


@router.get("/forecast")
async def get_forecast(
    district: str | None = Query(None, description="Filter by district"),
    crime_type: str | None = Query(None, description="Filter by crime type"),
    gravity: str | None = Query(None, description="Filter by gravity"),
    status: str | None = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate linear regression and moving average forecasts for next month."""
    check_perm = require_permission(Permission.PATTERN_INTELLIGENCE)
    await check_perm(current_user)

    allowed_district = await verify_district_access(current_user, district, db)
    auth_districts = await get_user_authorized_districts(current_user, db)

    service = AnalyticsService(db, authorized_districts=auth_districts)
    res = await service.get_forecast(
        district=allowed_district,
        crime_type=crime_type,
        gravity=gravity,
        status=status
    )
    return res


@router.get("/summary")
async def get_agent_summary(
    district: str | None = Query(None, description="Filter by district"),
    crime_type: str | None = Query(None, description="Filter by crime type"),
    police_station: str | None = Query(None, description="Filter by police station"),
    start_date: datetime.date | None = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: datetime.date | None = Query(None, description="End date (YYYY-MM-DD)"),
    gravity: str | None = Query(None, description="Filter by gravity"),
    status: str | None = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Invoke the PatternAgent to analyze patterns and return Gemini summary briefing."""
    check_perm = require_permission(Permission.PATTERN_INTELLIGENCE)
    await check_perm(current_user)

    allowed_district = await verify_district_access(current_user, district, db)
    auth_districts = await get_user_authorized_districts(current_user, db)

    from app.agents.pattern_agent import PatternAgent
    agent = PatternAgent()
    res = await agent.analyze_patterns(
        db=db,
        district=allowed_district,
        crime_type=crime_type,
        police_station=police_station,
        start_date=start_date,
        end_date=end_date,
        authorized_districts=auth_districts,
    )
    return res


@router.get("/heatmap")
async def get_heatmap(
    district: str | None = Query(None, description="Filter by district"),
    crime_type: str | None = Query(None, description="Filter by crime type"),
    police_station: str | None = Query(None, description="Filter by police station"),
    start_date: datetime.date | None = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: datetime.date | None = Query(None, description="End date (YYYY-MM-DD)"),
    gravity: str | None = Query(None, description="Filter by gravity"),
    status: str | None = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Retrieve raw coordinate points for generating Leaflet GIS heatmaps."""
    check_perm = require_permission(Permission.CRIME_MAP)
    await check_perm(current_user)

    allowed_district = await verify_district_access(current_user, district, db)
    auth_districts = await get_user_authorized_districts(current_user, db)

    service = AnalyticsService(db, authorized_districts=auth_districts)
    res = await service.get_heatmap(
        district=allowed_district,
        crime_type=crime_type,
        police_station=police_station,
        start_date=start_date,
        end_date=end_date,
        gravity=gravity,
        status=status
    )
    return res


@router.get("/map")
async def get_map_analytics(
    district: str | None = Query(None, description="Filter by district"),
    crime_type: str | None = Query(None, description="Filter by crime type"),
    police_station: str | None = Query(None, description="Filter by police station"),
    start_date: datetime.date | None = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: datetime.date | None = Query(None, description="End date (YYYY-MM-DD)"),
    date_range: str | None = Query(None, description="Filter by date range in days (7, 30, 90, 365)"),
    gravity: str | None = Query(None, description="Filter by gravity"),
    status: str | None = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Retrieve the aggregated GIS portal payload containing boundaries, stats, stations, and heatmaps."""
    check_perm = require_permission(Permission.CRIME_MAP)
    await check_perm(current_user)

    allowed_district = await verify_district_access(current_user, district, db)
    auth_districts = await get_user_authorized_districts(current_user, db)

    if date_range:
        try:
            days = int(date_range)
            end_date = datetime.date.today()
            start_date = end_date - datetime.timedelta(days=days)
        except ValueError:
            pass

    service = AnalyticsService(db, authorized_districts=auth_districts)
    res = await service.get_map_analytics(
        district=allowed_district,
        crime_type=crime_type,
        police_station=police_station,
        start_date=start_date,
        end_date=end_date,
        gravity=gravity,
        status=status
    )
    return res
