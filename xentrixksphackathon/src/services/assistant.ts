// src/services/assistant.ts — Real backend chat integration.
// Replaces the mock keyword-matching assistant with POST /api/v1/chat.

import { sendChatMessage } from "@/lib/api/services";
import type { ChatMessage, AgentKind } from "@/types/chat";

// ─── Context detection helpers (kept for backwards compatibility) ────────────

/** Very rough follow-up detector: pronouns/deictic phrases referencing a prior entity. */
export function detectContextRef(q: string): boolean {
  return (
    /\b(his|her|their|that|same|this)\s+(accused|case|offender|fir|network|person|guy)\b/i.test(
      q,
    ) || /\b(same case|that accused|this offender)\b/i.test(q)
  );
}

/** Extract an accused ID from a text if present. */
export function extractAccusedId(text: string): string | null {
  const m = text.match(/\bA\d{2,4}\b/);
  return m ? m[0] : null;
}

// ─── Map backend agent name to our AgentKind union ──────────────────────────

function mapAgent(agentName?: string): AgentKind | undefined {
  if (!agentName) return undefined;
  const lower = agentName.toLowerCase();
  if (lower.includes("query")) return "Query Agent";
  if (lower.includes("pattern")) return "Pattern Agent";
  if (lower.includes("network")) return "Network Agent";
  if (lower.includes("risk")) return "Risk Agent";
  if (lower.includes("decision")) return "Decision Support Agent";
  return "Query Agent";
}

// ─── Main entry point ────────────────────────────────────────────────────────

export async function askAssistant(
  question: string,
  conversationId?: string | null,
): Promise<ChatMessage & { conversationId?: string }> {
  const resp = await sendChatMessage({
    question,
    conversation_id: conversationId ?? null,
  });

  if (resp.status === "error") {
    throw new Error(resp.error ?? "Chat request failed");
  }

  // Build the message that the chat UI expects
  const message: ChatMessage & { conversationId?: string } = {
    id: crypto.randomUUID(),
    role: "assistant",
    text: resp.summary ?? resp.error ?? "No response from backend.",
    sql: resp.generated_sql,
    rows: resp.row_count,
    agent: mapAgent(resp.agent),
    ts: new Date().toISOString(),
    conversationId: resp.conversation_id,
  };

  // If there are result rows, wrap them as a table RichData
  if (resp.rows && resp.rows.length > 0 && resp.columns && resp.columns.length > 0) {
    message.data = {
      kind: "table",
      title: `Query results (${resp.row_count ?? resp.rows.length} rows)`,
      columns: resp.columns,
      rows: resp.rows.map((row) =>
        resp.columns!.map((col) => {
          const val = row[col];
          if (typeof val === "boolean") return val ? "True" : "False";
          return val ?? "";
        }),
      ),
    };
  }

  return message;
}
