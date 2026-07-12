// src/lib/api/query-keys.ts — Centralised React Query key factories.

export const queryKeys = {
  // Auth
  auth: ["auth"] as const,

  // Dashboard
  dashboard: () => ["dashboard"] as const,

  // Conversations
  conversations: () => ["conversations"] as const,
  conversation: (id: string) => ["conversations", id] as const,

  // Cases
  cases: (params?: Record<string, unknown>) => (params ? ["cases", params] : (["cases"] as const)),
  case: (id: string) => ["cases", id] as const,

  // Accused
  accused: () => ["accused"] as const,
  accusedDetail: (id: string) => ["accused", id] as const,
} as const;
