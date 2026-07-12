// src/config/api.ts — Centralised API endpoint definitions.

import { ENV } from "./environment";

export const API_BASE = ENV.API_BASE_URL;

export const ENDPOINTS = {
  // Auth
  LOGIN: "/auth/login",

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

  // Health
  HEALTH: "/health",
} as const;
