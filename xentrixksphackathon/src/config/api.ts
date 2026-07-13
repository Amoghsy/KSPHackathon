// src/config/api.ts — Centralised API endpoint definitions.

import { ENV } from "./environment";

export const API_BASE = ENV.API_BASE_URL;

export const ENDPOINTS = {
  // Auth
  LOGIN: "/auth/login",

  // Administrative Users
  USERS: "/users/",
  USER: (id: number) => `/users/${id}`,

  // Chat / Orchestrator
  CHAT: "/chat/",

  // Conversations
  CONVERSATIONS: "/conversations/",
  CONVERSATION: (id: string) => `/conversations/${id}`,

  // Dashboard
  DASHBOARD: "/dashboard/",

  // Cases / FIRs
  CASES: "/cases/",
  CASE: (id: string) => `/cases/${id}`,

  // Accused / Offenders
  ACCUSED: "/accused/",
  ACCUSED_DETAIL: (id: string) => `/accused/${id}`,

  // Network
  NETWORK: "/network/",
  NETWORK_ACCUSED: (id: string) => `/network/accused/${id}`,
  NETWORK_CASE: (id: string) => `/network/case/${id}`,
  NETWORK_COMMUNITY: "/network/community",
  NETWORK_REPEAT_OFFENDERS: "/network/repeat-offenders",
  NETWORK_ANALYTICS: "/network/analytics",

  // Financial
  FINANCIAL: "/financial/",

  // Health
  HEALTH: "/health",

} as const;
