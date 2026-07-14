import { apiGet } from "@/lib/api/axios";

export interface MapAnalyticsPayload {
  heatmap_points: Array<{
    latitude: number;
    longitude: number;
    crime_type: string;
    gravity: number;
    district: string;
  }>;
  hotspots: Array<{
    cluster_id: number;
    center: { latitude: number; longitude: number };
    cases: number;
    dominant: string;
    severity: number;
    district?: string;
  }>;
  police_stations: Array<{
    name: string;
    district: string;
    latitude: number;
    longitude: number;
    cases: number;
    solved: number;
    pending: number;
    dominant: string;
    repeat_offenders: number;
  }>;
  district_statistics: Record<string, {
    district: string;
    cases: number;
    solved: number;
    pending: number;
    growth: number;
    dominant: string;
    repeat_offenders: number;
    gangs: number;
    hotspots: number;
    prediction: number;
  }>;
}

export async function getMapAnalytics(filters?: any): Promise<MapAnalyticsPayload> {
  try {
    const res = await apiGet<MapAnalyticsPayload>("/pattern/map", filters);
    return res || {
      heatmap_points: [],
      hotspots: [],
      police_stations: [],
      district_statistics: {}
    };
  } catch (err) {
    console.error("Error fetching map analytics aggregation:", err);
    return {
      heatmap_points: [],
      hotspots: [],
      police_stations: [],
      district_statistics: {}
    };
  }
}
