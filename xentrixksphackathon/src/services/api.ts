// MOCK service layer — replace with real HTTP calls when backend is ready.
import { ALL_FIRS, type FIR } from "@/mocks/firs";
import { ALL_OFFENDERS, type Offender } from "@/mocks/offenders";
import { generateNetwork } from "@/mocks/network";
import { generateDashboard } from "@/mocks/dashboard";
import { generateHotspots } from "@/mocks/hotspots";
import { ALERTS } from "@/mocks/alerts";
import { AUDIT_ROWS } from "@/mocks/audit";
import { generateSociological } from "@/mocks/sociological";
import { generateFinancialNetwork } from "@/mocks/financial";
import { generateForecast, forecastCommentary, type ForecastCrime } from "@/mocks/forecast";
import { latency } from "@/mocks/rng";

// ============================== CASES ==============================
export async function listFIRs(params?: {
  q?: string;
  status?: string;
  district?: string;
  page?: number;
  pageSize?: number;
}): Promise<{ items: FIR[]; total: number }> {
  await latency();
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
  await latency();
  return ALL_FIRS.find((f) => f.id === id) ?? null;
}

// ============================== OFFENDERS ==============================
export async function listOffenders(): Promise<Offender[]> {
  await latency();
  return ALL_OFFENDERS;
}
export async function getOffender(id: string): Promise<Offender | null> {
  await latency();
  return ALL_OFFENDERS.find((o) => o.id === id) ?? null;
}
export async function similarOffenders(id: string): Promise<Offender[]> {
  await latency();
  return ALL_OFFENDERS.filter((o) => o.id !== id).slice(0, 4);
}

// ============================== NETWORK ==============================
export async function getNetwork() {
  await latency();
  return generateNetwork();
}

// ============================== DASHBOARD ==============================
export async function getDashboard() {
  await latency();
  return generateDashboard();
}

// ============================== MAP ==============================
export async function getHotspots() {
  await latency();
  return generateHotspots();
}

// ============================== ALERTS ==============================
export async function getAlerts() {
  await latency();
  return ALERTS;
}

// ============================== AUDIT ==============================
export async function getAudit() {
  await latency();
  return AUDIT_ROWS;
}

// ============================== SOCIOLOGICAL ==============================
export async function getSociologicalInsights() {
  await latency();
  return generateSociological();
}

// ============================== FINANCIAL ==============================
export async function getFinancialNetwork() {
  await latency();
  return generateFinancialNetwork();
}

// ============================== FORECAST ==============================
export async function getForecast(crime: ForecastCrime) {
  await latency();
  const points = generateForecast(crime);
  return { points, commentary: forecastCommentary(crime, points) };
}
export type { ForecastCrime };
