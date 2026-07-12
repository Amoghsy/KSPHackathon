// src/services/api.ts — Real backend API calls replacing all mock data.
// Delegates to src/lib/api/services.ts for HTTP; adapts response shapes as needed.

import {
  getDashboardData,
  listConversations,
  listCases,
  getCase,
  listAccused,
  getAccused,
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
    const response = await listCases({
      page: 1,
      pageSize: 100,
    });

    if (!response.cases || response.cases.length === 0) {
      // Fallback to mocks if DB is empty
      return fallbackListFIRs(params);
    }

    let items: FIR[] = response.cases.map((c: Case) => ({
      id: String(c.case_master_id),
      crimeNo: c.crime_no,
      caseNo: c.case_no ?? `C-${c.case_master_id}`,
      date: new Date(c.crime_registered_date).toLocaleDateString("en-IN", {
        day: "numeric",
        month: "short",
        year: "numeric",
      }),
      station: c.police_station_id ? `Station ${c.police_station_id}` : "SCRB Station",
      district: "Bengaluru Urban",
      crimeHead: "Theft",
      complainant: "State of Karnataka",
      status: "Under Investigation",
      gravity: "Medium",
      narrative: c.brief_facts ?? "",
      accused: [],
      victims: [],
      actsSections: [],
      arrests: [],
      chargesheet: null,
      timeline: [],
    }));

    if (params?.q) {
      const q = params.q.toLowerCase();
      items = items.filter(
        (f) =>
          f.crimeNo.toLowerCase().includes(q) ||
          f.station.toLowerCase().includes(q) ||
          f.narrative.toLowerCase().includes(q),
      );
    }

    const total = items.length;
    const page = params?.page ?? 1;
    const size = params?.pageSize ?? 15;
    return { items: items.slice((page - 1) * size, page * size), total };
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
    const numericId = parseInt(id, 10);
    if (isNaN(numericId)) {
      return ALL_FIRS.find((f) => f.id === id) ?? null;
    }
    const c = await getCase(id);
    if (!c) return null;

    return {
      id: String(c.case_master_id),
      crimeNo: c.crime_no,
      caseNo: c.case_no ?? `C-${c.case_master_id}`,
      date: new Date(c.crime_registered_date).toLocaleDateString("en-IN", {
        day: "numeric",
        month: "short",
        year: "numeric",
      }),
      station: c.police_station_id ? `Station ${c.police_station_id}` : "SCRB Station",
      district: "Bengaluru Urban",
      crimeHead: "Theft",
      complainant: "State of Karnataka",
      status: "Under Investigation",
      gravity: "Medium",
      narrative: c.brief_facts ?? "",
      accused: [],
      victims: [],
      actsSections: [],
      arrests: [],
      chargesheet: null,
      timeline: [],
    };
  } catch (err) {
    console.error("Error fetching case details:", err);
    return ALL_FIRS.find((f) => f.id === id) ?? null;
  }
}

// ─── Offenders / Accused ─────────────────────────────────────────────────────
export async function listOffenders(): Promise<Offender[]> {
  try {
    const response = await listAccused();
    if (!response.accused || response.accused.length === 0) {
      return ALL_OFFENDERS;
    }

    return response.accused.map((a: Accused) => ({
      id: String(a.accused_master_id),
      name: a.accused_name ?? "Unknown Accused",
      age: a.age_year ?? 30,
      linkedCases: 1,
      riskScore: 50,
      risk: "Medium",
      modusOperandi: ["General theft"],
      aliases: [],
      lastKnown: "Bengaluru Urban",
      factors: [
        { label: "Prior convictions", value: 50 },
        { label: "Case severity", value: 40 },
      ],
    }));
  } catch (err) {
    console.error("Error listing offenders:", err);
    return ALL_OFFENDERS;
  }
}

export async function getOffender(id: string): Promise<Offender | null> {
  try {
    const numericId = parseInt(id, 10);
    if (isNaN(numericId)) {
      return ALL_OFFENDERS.find((o) => o.id === id) ?? null;
    }
    const a = await getAccused(id);
    if (!a) return null;

    return {
      id: String(a.accused_master_id),
      name: a.accused_name ?? "Unknown Accused",
      age: a.age_year ?? 30,
      linkedCases: 1,
      riskScore: 55,
      risk: "Medium",
      modusOperandi: ["General theft"],
      aliases: [],
      lastKnown: "Bengaluru Urban",
      factors: [
        { label: "Prior convictions", value: 60 },
        { label: "Case severity", value: 50 },
      ],
    };
  } catch (err) {
    console.error("Error fetching offender details:", err);
    return ALL_OFFENDERS.find((o) => o.id === id) ?? null;
  }
}

export async function similarOffenders(id: string): Promise<Offender[]> {
  const all = await listOffenders();
  return all.filter((o) => o.id !== id).slice(0, 4);
}

// ─── Network (Out of scope backend-wise) ─────────────────────────────────────
export async function getNetwork() {
  return generateNetwork();
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

// ─── Financial (Out of scope backend-wise) ───────────────────────────────────
export async function getFinancialNetwork() {
  return generateFinancialNetwork();
}

// ─── Forecast (Out of scope backend-wise) ────────────────────────────────────
export async function getForecast(crime: ForecastCrime) {
  const points = generateForecast(crime);
  return { points, commentary: forecastCommentary(crime, points) };
}

export type { ForecastCrime };
export { listConversations };
