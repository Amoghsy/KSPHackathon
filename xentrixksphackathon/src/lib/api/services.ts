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
}): Promise<CasesResponse> {
  const limit = params?.pageSize ?? 100;
  const offset = ((params?.page ?? 1) - 1) * limit;
  return apiGet<CasesResponse>(ENDPOINTS.CASES, { limit, offset });
}

export async function getCase(id: string): Promise<Case> {
  return apiGet<Case>(ENDPOINTS.CASE(id));
}

// ─── Accused ─────────────────────────────────────────────────────────────────

export async function listAccused(): Promise<AccusedResponse> {
  return apiGet<AccusedResponse>(ENDPOINTS.ACCUSED);
}

export async function getAccused(id: string): Promise<Accused> {
  return apiGet<Accused>(ENDPOINTS.ACCUSED_DETAIL(id));
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
