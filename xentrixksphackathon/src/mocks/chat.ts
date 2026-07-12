import type { ReactNode } from "react";

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
  | "Query Agent"
  | "Network Agent"
  | "Pattern Agent"
  | "Risk Agent"
  | "Decision Support Agent";

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

const now = (offMin: number) => {
  const d = new Date();
  d.setMinutes(d.getMinutes() - offMin);
  return d.toISOString();
};

export const SEED_SESSION: ChatSession = {
  id: "session-1",
  title: "Robbery trend — Bengaluru",
  updatedAt: now(0),
  messages: [
    {
      id: "m1",
      role: "user",
      text: "Show robbery cases in Bengaluru Urban in the last 6 months",
      ts: now(45),
    },
    {
      id: "m2",
      role: "assistant",
      text: "There were 87 robbery FIRs in Bengaluru Urban in the last 6 months, a 12% increase over the prior period. The Whitefield and KR Puram zones account for 41% of these.",
      data: {
        kind: "chart",
        title: "Robbery FIRs — Bengaluru Urban (last 6 mo.)",
        chartKind: "bar",
        chartData: [
          { label: "Jan", value: 11 },
          { label: "Feb", value: 13 },
          { label: "Mar", value: 12 },
          { label: "Apr", value: 15 },
          { label: "May", value: 17 },
          { label: "Jun", value: 19 },
        ],
      },
      sql: "SELECT DATE_TRUNC('month', fir_date) AS month, COUNT(*) AS cases\nFROM firs\nWHERE crime_head = 'Robbery'\n  AND district = 'Bengaluru Urban'\n  AND fir_date >= CURRENT_DATE - INTERVAL '6 months'\nGROUP BY 1 ORDER BY 1;",
      rows: 6,
      ts: now(44),
    },
    {
      id: "m3",
      role: "user",
      text: "Which accused have 3 or more FIRs?",
      ts: now(20),
    },
    {
      id: "m4",
      role: "assistant",
      text: "42 accused persons have 3 or more linked FIRs. Top 5 shown below — all currently flagged as repeat offenders.",
      data: {
        kind: "table",
        title: "Top repeat accused",
        columns: ["Accused ID", "Name", "Linked FIRs", "Risk"],
        rows: [
          ["A12", "Suresh Naik", 7, "High"],
          ["A19", "Ravi Kumar", 6, "High"],
          ["A22", "Karthik Rao", 5, "High"],
          ["A31", "Manoj Patil", 5, "Medium"],
          ["A44", "Vikram Shetty", 4, "Medium"],
        ],
      },
      sql: "SELECT a.accused_id, a.name, COUNT(*) AS fir_count\nFROM fir_accused fa JOIN accused a USING (accused_id)\nGROUP BY a.accused_id, a.name\nHAVING COUNT(*) >= 3\nORDER BY fir_count DESC;",
      rows: 42,
      ts: now(19),
    },
    {
      id: "m5",
      role: "user",
      text: "Total open cases this month?",
      ts: now(5),
    },
    {
      id: "m6",
      role: "assistant",
      text: "There are 187 open cases registered this month — a 4.1% increase over the previous month.",
      data: {
        kind: "stat",
        title: "Open cases — this month",
        value: 187,
        delta: 4.1,
        unit: "cases",
      },
      sql: "SELECT COUNT(*) FROM firs\nWHERE status IN ('Under Investigation','Charge Sheeted')\n  AND DATE_TRUNC('month', fir_date) = DATE_TRUNC('month', CURRENT_DATE);",
      rows: 1,
      ts: now(4),
    },
  ],
};

export const HISTORY_SESSIONS: { id: string; title: string; updatedAt: string }[] = [
  { id: "session-1", title: "Robbery trend — Bengaluru", updatedAt: now(0) },
  { id: "session-2", title: "Repeat offenders (3+ FIRs)", updatedAt: now(60 * 22) },
  { id: "session-3", title: "Network around Accused A12", updatedAt: now(60 * 26) },
  { id: "session-4", title: "Cybercrime cluster — Mangaluru", updatedAt: now(60 * 48) },
  { id: "session-5", title: "Vehicle theft — Whitefield", updatedAt: now(60 * 96) },
];

// intentional unused import guard
export type _R = ReactNode;
