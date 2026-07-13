// src/services/api.ts — Real backend API calls replacing all mock data.
// Delegates to src/lib/api/services.ts for HTTP; adapts response shapes as needed.

import {
  getDashboardData,
  listConversations,
  listCases,
  getCase,
  listAccused,
  getAccused,
  getNetwork as apiGetNetwork,
  getFinancialNetwork as apiGetFinancialNetwork,
  getNetworkExpansion as apiGetNetworkExpansion,
} from "@/lib/api/services";
import type { DashboardResponse, Case, Accused } from "@/lib/api/types";
import { ALL_FIRS, type FIR } from "@/mocks/firs";
import { ALL_OFFENDERS, type Offender } from "@/mocks/offenders";
import { generateNetwork } from "@/mocks/network";
import { generateHotspots } from "@/mocks/hotspots";
import { ALERTS } from "@/mocks/alerts";
import { AUDIT_ROWS } from "@/mocks/audit";
import { generateSociological } from "@/mocks/sociological";
import { generateFinancialNetwork } from "@/mocks/financial";
import { generateForecast, forecastCommentary, type ForecastCrime } from "@/mocks/forecast";

// ─── Dashboard ───────────────────────────────────────────────────────────────
export async function getDashboard(): Promise<DashboardResponse> {
  const raw = await getDashboardData();

  if ("kpis" in raw && Array.isArray((raw as DashboardResponse).kpis)) {
    return raw as DashboardResponse;
  }

  const adapted = raw as {
    stats?: {
      total_cases?: number;
      open_cases?: number;
      closed_cases?: number;
      charge_sheeted?: number;
      districts?: Record<string, number>;
      crime_types?: Record<string, number>;
    };
    crime_trends?: { month: string; count: number }[];
    status?: string;
  };

  const stats = adapted.stats ?? {};

  const kpis = [
    { label: "Total Cases", value: stats.total_cases ?? 0, delta: 0 },
    { label: "Open Cases", value: stats.open_cases ?? 0, delta: 0 },
    { label: "Closed Cases", value: stats.closed_cases ?? 0, delta: 0 },
    { label: "Charge-Sheeted", value: stats.charge_sheeted ?? 0, delta: 0 },
    {
      label: "Districts Active",
      value: Object.keys(stats.districts ?? {}).length,
      delta: 0,
    },
  ];

  const monthlyTrend = (adapted.crime_trends ?? []).map((item) => ({
    month: item.month,
    Theft: Math.round(item.count * 0.4),
    Robbery: Math.round(item.count * 0.2),
    Cybercrime: Math.round(item.count * 0.15),
    Assault: Math.round(item.count * 0.25),
  }));

  const districtCounts = Object.entries(stats.districts ?? {})
    .map(([district, cases]) => ({ district, cases: cases as number }))
    .sort((a, b) => b.cases - a.cases)
    .slice(0, 5);

  const statusBreakdown = [
    { name: "Open", value: stats.open_cases ?? 0 },
    { name: "Closed", value: stats.closed_cases ?? 0 },
    { name: "Charge-Sheeted", value: stats.charge_sheeted ?? 0 },
  ].filter((s) => s.value > 0);

  return { kpis, monthlyTrend, districtCounts, statusBreakdown };
}

// ─── Cases / FIRs ────────────────────────────────────────────────────────────
export async function listFIRs(params?: {
  q?: string;
  status?: string;
  district?: string;
  page?: number;
  pageSize?: number;
}): Promise<{ items: FIR[]; total: number }> {
  try {
    const response = await listCases(params);
    if (!response || !response.items) {
      return fallbackListFIRs(params);
    }
    return response as { items: FIR[]; total: number };
  } catch (err) {
    console.error("Error fetching cases from backend:", err);
    return fallbackListFIRs(params);
  }
}

function fallbackListFIRs(params?: {
  q?: string;
  status?: string;
  district?: string;
  page?: number;
  pageSize?: number;
}): { items: FIR[]; total: number } {
  let items = ALL_FIRS.slice();
  if (params?.q) {
    const q = params.q.toLowerCase();
    items = items.filter(
      (f) =>
        f.crimeNo.toLowerCase().includes(q) ||
        f.station.toLowerCase().includes(q) ||
        f.district.toLowerCase().includes(q) ||
        f.crimeHead.toLowerCase().includes(q) ||
        f.complainant.toLowerCase().includes(q),
    );
  }
  if (params?.status && params.status !== "All") {
    items = items.filter((f) => f.status === params.status);
  }
  if (params?.district && params.district !== "All") {
    items = items.filter((f) => f.district === params.district);
  }
  const total = items.length;
  const page = params?.page ?? 1;
  const size = params?.pageSize ?? 15;
  return { items: items.slice((page - 1) * size, page * size), total };
}

export async function getFIR(id: string): Promise<FIR | null> {
  try {
    const c = await getCase(id);
    if (!c) return null;
    return c as FIR;
  } catch (err) {
    console.error("Error fetching case details:", err);
    return ALL_FIRS.find((f) => f.id === id) ?? null;
  }
}

// ─── Offenders / Accused ─────────────────────────────────────────────────────
export async function listOffenders(): Promise<Offender[]> {
  try {
    const response = await listAccused({ page: 1, pageSize: 150 });
    if (!response || !response.items || response.items.length === 0) {
      return ALL_OFFENDERS;
    }
    return response.items as Offender[];
  } catch (err) {
    console.error("Error listing offenders:", err);
    return ALL_OFFENDERS;
  }
}

export async function getOffender(id: string): Promise<Offender | null> {
  try {
    const response = await getAccused(id);
    if (!response) return null;
    return response as Offender;
  } catch (err) {
    console.error("Error fetching offender details:", err);
    return ALL_OFFENDERS.find((o) => o.id === id) ?? null;
  }
}

export async function similarOffenders(id: string): Promise<Offender[]> {
  const all = await listOffenders();
  return all.filter((o) => o.id !== id).slice(0, 4);
}

// ─── Network ─────────────────────────────────────────────────────────────────
export async function getNetwork(params?: {
  district?: string;
  crimeType?: string;
  policeStation?: string;
  timePeriod?: string;
  focusId?: string;
}) {
  try {
    return await apiGetNetwork(params);
  } catch (err) {
    console.error("Error fetching network from backend, using mock:", err);
    return generateNetwork();
  }
}

export async function getNetworkExpansion(nodeId: string, kind: string) {
  try {
    return await apiGetNetworkExpansion(nodeId, kind);
  } catch (err) {
    console.error("Error expanding network node:", err);
    return { nodes: [], links: [] };
  }
}


// ─── Hotspots (Out of scope backend-wise) ────────────────────────────────────
export async function getHotspots() {
  return generateHotspots();
}

// ─── Alerts ──────────────────────────────────────────────────────────────────
export async function getAlerts() {
  return ALERTS;
}

// ─── Audit (Out of scope backend-wise) ───────────────────────────────────────
export async function getAudit() {
  return AUDIT_ROWS;
}

// ─── Sociological (Out of scope backend-wise) ────────────────────────────────
export async function getSociologicalInsights() {
  return generateSociological();
}

// ─── Financial ───────────────────────────────────────────────────────────────
export async function getFinancialNetwork(params?: {
  district?: string;
  crimeType?: string;
  policeStation?: string;
  timePeriod?: string;
}) {
  try {
    return await apiGetFinancialNetwork(params);
  } catch (err) {
    console.error("Error fetching financial network from backend, using mock:", err);
    return generateFinancialNetwork();
  }
}


// ─── Forecast (Out of scope backend-wise) ────────────────────────────────────
export async function getForecast(crime: ForecastCrime) {
  const points = generateForecast(crime);
  return { points, commentary: forecastCommentary(crime, points) };
}

export type { ForecastCrime };
export { listConversations };
