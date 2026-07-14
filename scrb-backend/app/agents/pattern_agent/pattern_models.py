from typing import Any
from pydantic import BaseModel


class TrendTimeSeriesPoint(BaseModel):
    month: str
    count: int
    moving_avg: float


class TrendResponse(BaseModel):
    time_series: list[TrendTimeSeriesPoint]
    daily_trends: list[dict]
    growth_rate_percent: float
    top_crimes: list[dict]
    district_ranking: list[dict]
    average_monthly_frequency: float
    total_cases: int


class HotspotClusterCenter(BaseModel):
    latitude: float
    longitude: float


class HotspotCluster(BaseModel):
    cluster_id: int
    center: HotspotClusterCenter
    cases: int
    severity: float
    dominant: str
    district: str


class DistrictHotspot(BaseModel):
    district: str
    x: float
    y: float
    cases: int
    dominant: str
    trend: float
    intensity: float


class HotspotsResponse(BaseModel):
    dbscan_clusters: list[HotspotCluster]
    district_hotspots: list[DistrictHotspot]


class AnomalyPoint(BaseModel):
    time_period: str
    count: int
    z_score: float
    confidence: float
    reason: str


class TemporalData(BaseModel):
    byHour: list[dict]
    byDay: list[dict]
    workingDays: int
    weekends: int


class DistributionResponse(BaseModel):
    status_breakdown: list[dict]
    temporal_distribution: TemporalData
    demographics: dict
    crime_heat_index: list[dict]


class ForecastPoint(BaseModel):
    period: str
    count: float
    is_forecast: bool


class ForecastResponse(BaseModel):
    points: list[ForecastPoint]
    forecast_value: float
    confidence: float
    commentary: str


class PatternAgentSummaryResponse(BaseModel):
    status: str
    summary: str
    details: Any
