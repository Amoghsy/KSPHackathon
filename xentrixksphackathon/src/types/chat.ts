// src/types/chat.ts — Canonical chat type definitions (moved from mocks/chat.ts).

export type ChatRole = "user" | "assistant";

export interface RichData {
  kind: "table" | "stat" | "chart";
  title?: string;
  // For table
  columns?: string[];
  rows?: (string | number)[][];
  // For stat
  value?: string | number;
  delta?: number;
  unit?: string;
  // For chart
  chartKind?: "bar" | "line";
  chartData?: { label: string; value: number }[];
}

export type AgentKind =
  "Query Agent" | "Network Agent" | "Pattern Agent" | "Risk Agent" | "Decision Support Agent";

export interface ChatMessage {
  id: string;
  role: ChatRole;
  text: string;
  data?: RichData;
  sql?: string;
  rows?: number;
  agent?: AgentKind;
  ts: string;
}

export interface ChatSession {
  id: string;
  title: string;
  updatedAt: string;
  messages: ChatMessage[];
}
