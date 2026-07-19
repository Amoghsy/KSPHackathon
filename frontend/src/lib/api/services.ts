// src/lib/api/services.ts — Backend API service functions using apiClient.

import { apiGet, apiPost, apiPostChat, apiPatch, apiDelete } from "./axios";
import { ENDPOINTS } from "@/config/api";
import type {
  LoginRequest,
  LoginResponse,
  ChatRequest,
  ChatResponse,
  ConversationSession,
  DashboardResponse,
  CasesResponse,
  Case,
  Accused,
  AccusedResponse,
  UserResponse,
  UserCreatePayload,
  DistrictAssignmentRecord,
} from "./types";

// ─── Auth ────────────────────────────────────────────────────────────────────

export async function loginUser(body: LoginRequest): Promise<LoginResponse> {
  return apiPost<LoginResponse>(ENDPOINTS.LOGIN, body);
}

// ─── Chat ────────────────────────────────────────────────────────────────────

export async function sendChatMessage(body: ChatRequest): Promise<ChatResponse> {
  return apiPostChat<ChatResponse>(ENDPOINTS.CHAT, body);
}

// ─── Conversations ───────────────────────────────────────────────────────────

export async function listConversations(params?: {
  limit?: number;
  offset?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}): Promise<ConversationSession[]> {
  return apiGet<ConversationSession[]>(ENDPOINTS.CONVERSATIONS, params as Record<string, unknown>);
}

export async function getConversation(id: string): Promise<ConversationSession> {
  return apiGet<ConversationSession>(ENDPOINTS.CONVERSATION(id));
}

export async function updateConversation(
  id: string,
  updates: Partial<Pick<ConversationSession, "user_id" | "last_question" | "resolved_entities">>,
): Promise<ConversationSession> {
  return apiPatch<ConversationSession>(ENDPOINTS.CONVERSATION(id), updates);
}

export async function deleteConversation(id: string): Promise<{ status: string; message: string }> {
  return apiDelete<{ status: string; message: string }>(ENDPOINTS.CONVERSATION(id));
}

// ─── Dashboard ───────────────────────────────────────────────────────────────

export async function getDashboardData(): Promise<DashboardResponse> {
  return apiGet<DashboardResponse>(ENDPOINTS.DASHBOARD);
}

// ─── Cases ───────────────────────────────────────────────────────────────────

export async function listCases(params?: {
  q?: string;
  status?: string;
  district?: string;
  page?: number;
  pageSize?: number;
}): Promise<any> {
  return apiGet<any>(ENDPOINTS.CASES, params as Record<string, unknown>);
}

export async function getCase(id: string): Promise<any> {
  return apiGet<any>(ENDPOINTS.CASE(id));
}

export async function getCasesMetadata(): Promise<{
  districts: string[];
  crime_heads: string[];
  statuses: string[];
  gravity: string[];
}> {
  return apiGet<{
    districts: string[];
    crime_heads: string[];
    statuses: string[];
    gravity: string[];
  }>(ENDPOINTS.CASES_METADATA);
}

// ─── Accused ─────────────────────────────────────────────────────────────────

export async function listAccused(params?: {
  q?: string;
  page?: number;
  pageSize?: number;
}): Promise<any> {
  return apiGet<any>(ENDPOINTS.ACCUSED, params as Record<string, unknown>);
}

export async function getAccused(id: string): Promise<any> {
  return apiGet<any>(ENDPOINTS.ACCUSED_DETAIL(id));
}

// ─── Administrative Users ───────────────────────────────────────────────────

export async function listUsers(): Promise<UserResponse[]> {
  return apiGet<UserResponse[]>(ENDPOINTS.USERS);
}

export async function createUser(body: UserCreatePayload): Promise<UserResponse> {
  return apiPost<UserResponse>(ENDPOINTS.USERS, body);
}

export async function deleteUser(id: number): Promise<void> {
  return apiDelete<void>(ENDPOINTS.USER(id));
}

// ─── Network & Financial ─────────────────────────────────────────────────────

export async function getNetwork(params?: {
  district?: string;
  crimeType?: string;
  policeStation?: string;
  timePeriod?: string;
  focusId?: string;
}): Promise<any> {
  const query: Record<string, unknown> = {};
  if (params) {
    if (params.district) query.district = params.district;
    if (params.crimeType) query.crime_type = params.crimeType;
    if (params.policeStation) query.police_station = params.policeStation;
    if (params.timePeriod) query.time_period = params.timePeriod;
    if (params.focusId) query.focus_id = params.focusId;
  }
  return apiGet<any>(ENDPOINTS.NETWORK, query);
}

export async function getNetworkExpansion(nodeId: string, kind: string): Promise<any> {
  return apiGet<any>(ENDPOINTS.NETWORK_EXPAND, { node_id: nodeId, kind });
}

export async function getFinancialNetwork(params?: {
  district?: string;
  crimeType?: string;
  policeStation?: string;
  timePeriod?: string;
}): Promise<any> {
  const query: Record<string, unknown> = {};
  if (params) {
    if (params.district) query.district = params.district;
    if (params.crimeType) query.crime_type = params.crimeType;
    if (params.policeStation) query.police_station = params.policeStation;
    if (params.timePeriod) query.time_period = params.timePeriod;
  }
  return apiGet<any>(ENDPOINTS.FINANCIAL, query);
}


// ─── Audit & History ──────────────────────────────────────────────────────────

export async function getAuditLogs(): Promise<any[]> {
  return apiGet<any[]>("/audit");
}

export async function getAdminStats(): Promise<any> {
  return apiGet<any>("/audit/dashboard-stats");
}

export async function getInvestigationHistory(): Promise<any[]> {
  return apiGet<any[]>("/audit/history");
}

export async function addInvestigationHistory(body: { name: string; entity_type: string; entity_id: string }): Promise<any> {
  return apiPost<any>(`/audit/history?name=${encodeURIComponent(body.name)}&entity_type=${encodeURIComponent(body.entity_type)}&entity_id=${encodeURIComponent(body.entity_id)}`);
}

// ─── Supervisor District Assignments (Admin only) ─────────────────────────────

/** List all active assignments for investigators/supervisors */
export async function listSupervisorAssignments(): Promise<DistrictAssignmentRecord[]> {
  return apiGet<DistrictAssignmentRecord[]>("/security/district-assignments/investigators");
}

/** Assign a supervisor to a district permanently */
export async function assignSupervisorDistrict(user_id: number, district: string): Promise<any> {
  return apiPost<any>("/security/district-assignments", { user_id, district });
}

/** Deactivate / revoke a permanent district assignment by assignment ID */
export async function revokeSupervisorAssignment(assignmentId: number): Promise<any> {
  return apiDelete<any>(`/security/district-assignments/${assignmentId}`);
}

