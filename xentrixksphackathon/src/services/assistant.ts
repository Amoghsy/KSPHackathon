// MOCK NL→SQL assistant. Returns a rich response based on lightweight keyword matching.
import type { ChatMessage, RichData, AgentKind } from "@/mocks/chat";
import { latency } from "@/mocks/rng";

interface Reply {
  text: string;
  data?: RichData;
  sql?: string;
  rows?: number;
  agent: AgentKind;
}

function reply(q: string): Reply {
  const s = q.toLowerCase();
  if (s.includes("robbery") || s.includes("theft")) {
    const kind = s.includes("robbery") ? "Robbery" : "Theft";
    return {
      agent: "Query Agent",
      text: `${kind} FIRs across Karnataka show a rising trend in the last 6 months. Bengaluru Urban and Mysuru lead in volume; Whitefield sub-zone is the top hotspot.`,
      data: {
        kind: "chart",
        title: `${kind} FIRs — last 6 months`,
        chartKind: "line",
        chartData: [
          { label: "Jan", value: 42 },
          { label: "Feb", value: 51 },
          { label: "Mar", value: 48 },
          { label: "Apr", value: 55 },
          { label: "May", value: 62 },
          { label: "Jun", value: 71 },
        ],
      },
      sql: `SELECT DATE_TRUNC('month', fir_date) AS month, COUNT(*) AS cases\nFROM firs\nWHERE crime_head = '${kind}'\n  AND fir_date >= CURRENT_DATE - INTERVAL '6 months'\nGROUP BY 1 ORDER BY 1;`,
      rows: 6,
    };
  }
  if (s.includes("repeat") || s.includes("3+") || s.includes("accused")) {
    return {
      agent: "Pattern Agent",
      text: "42 accused persons have 3 or more linked FIRs. Below are the top 5 by case count.",
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
      sql: "SELECT accused_id, name, COUNT(*) AS fir_count\nFROM fir_accused JOIN accused USING (accused_id)\nGROUP BY 1, 2 HAVING COUNT(*) >= 3\nORDER BY fir_count DESC;",
      rows: 42,
    };
  }
  if (s.includes("network") || s.includes("cluster")) {
    return {
      agent: "Network Agent",
      text: "Accused A12 is central to a cluster of 6 co-accused across 4 FIRs, primarily around Whitefield. Open the Criminal Network view for interactive exploration.",
      data: {
        kind: "stat",
        title: "Cluster size around A12",
        value: 6,
        delta: 2,
        unit: "co-accused",
      },
      sql: "WITH neighbors AS (\n  SELECT a2.accused_id FROM fir_accused a1\n  JOIN fir_accused a2 USING (fir_id)\n  WHERE a1.accused_id = 'A12' AND a2.accused_id <> 'A12'\n) SELECT COUNT(DISTINCT accused_id) FROM neighbors;",
      rows: 1,
    };
  }
  if (s.includes("risk") || s.includes("forecast") || s.includes("predict")) {
    return {
      agent: "Risk Agent",
      text: "Risk score for Accused A12 is 0.87 (High). Model factors: 7 prior FIRs, 2 open cases, network centrality 0.71.",
      data: { kind: "stat", title: "Risk score", value: 0.87, delta: 12.4, unit: "of 1.00" },
      sql: "SELECT risk_score FROM offender_risk WHERE accused_id = 'A12';",
      rows: 1,
    };
  }
  if (s.includes("open") || s.includes("month")) {
    return {
      agent: "Decision Support Agent",
      text: "187 open cases were registered this month — a 4.1% increase over the previous month.",
      data: { kind: "stat", title: "Open cases — this month", value: 187, delta: 4.1, unit: "cases" },
      sql: "SELECT COUNT(*) FROM firs\nWHERE status IN ('Under Investigation','Charge Sheeted')\n  AND DATE_TRUNC('month', fir_date) = DATE_TRUNC('month', CURRENT_DATE);",
      rows: 1,
    };
  }
  if (s.includes("cyber")) {
    return {
      agent: "Pattern Agent",
      text: "Cybercrime FIRs have grown 38% year-over-year, concentrated in Bengaluru Urban and Mangaluru.",
      data: {
        kind: "chart",
        title: "Cybercrime FIRs — last 6 months",
        chartKind: "line",
        chartData: [
          { label: "Jan", value: 22 },
          { label: "Feb", value: 28 },
          { label: "Mar", value: 34 },
          { label: "Apr", value: 40 },
          { label: "May", value: 47 },
          { label: "Jun", value: 55 },
        ],
      },
      sql: "SELECT DATE_TRUNC('month', fir_date), COUNT(*) FROM firs\nWHERE crime_head = 'Cybercrime'\n  AND fir_date >= CURRENT_DATE - INTERVAL '6 months' GROUP BY 1 ORDER BY 1;",
      rows: 6,
    };
  }
  return {
    agent: "Query Agent",
    text: "I've parsed the query but need slightly more specificity (crime type, district, or time window). Try one of the suggested prompts below.",
    sql: `-- No structured intent matched\n-- Raw query: "${q}"`,
    rows: 0,
  };
}

// Very rough follow-up detector: pronouns/deictic phrases referencing a prior entity.
export function detectContextRef(q: string): boolean {
  return /\b(his|her|their|that|same|this)\s+(accused|case|offender|fir|network|person|guy)\b/i.test(
    q,
  ) || /\b(same case|that accused|this offender)\b/i.test(q);
}

// Extract an accused ID from a text if present.
export function extractAccusedId(text: string): string | null {
  const m = text.match(/\bA\d{2,4}\b/);
  return m ? m[0] : null;
}

export async function askAssistant(q: string): Promise<ChatMessage> {
  await latency();
  const r = reply(q);
  return {
    id: crypto.randomUUID(),
    role: "assistant",
    text: r.text,
    data: r.data,
    sql: r.sql,
    rows: r.rows,
    agent: r.agent,
    ts: new Date().toISOString(),
  };
}
