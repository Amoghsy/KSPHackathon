import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useRef, useState } from "react";
import { format } from "date-fns";
import {
  Send,
  Mic,
  ChevronDown,
  ChevronRight,
  Sparkles,
  History,
  FileDown,
  Bot,
  User as UserIcon,
  X,
} from "lucide-react";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import jsPDF from "jspdf";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tooltip as UITooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { MockBadge } from "@/components/app/mock-badge";
import { useT } from "@/lib/i18n";
import {
  SEED_SESSION,
  HISTORY_SESSIONS,
  type ChatMessage,
  type RichData,
  type AgentKind,
} from "@/mocks/chat";
import { askAssistant, detectContextRef, extractAccusedId } from "@/services/assistant";
import { toast } from "sonner";

export const Route = createFileRoute("/_app/")({
  head: () => ({
    meta: [{ title: "Chat Assistant — Crime Intelligence Assistant" }],
  }),
  component: ChatPage,
});

const AGENT_COLORS: Record<AgentKind, string> = {
  "Query Agent": "bg-info/15 text-info border-info/30",
  "Network Agent": "bg-primary/15 text-primary border-primary/30",
  "Pattern Agent": "bg-chart-2/20 text-chart-2 border-chart-2/30",
  "Risk Agent": "bg-destructive/10 text-destructive border-destructive/30",
  "Decision Support Agent": "bg-warning/15 text-warning-foreground border-warning/40",
};

// Feature-detect SpeechRecognition
function getSpeechRecognition(): any | null {
  if (typeof window === "undefined") return null;
  return (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition || null;
}

function ChatPage() {
  const t = useT();
  const [messages, setMessages] = useState<ChatMessage[]>(SEED_SESSION.messages);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [listening, setListening] = useState(false);
  const [contextEntity, setContextEntity] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const recognitionRef = useRef<any>(null);

  const SR = useMemo(() => getSpeechRecognition(), []);
  const speechSupported = !!SR;

  const SUGGESTIONS = [t("s1"), t("s2"), t("s3"), t("s4"), t("s5")];

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Detect if the input references a prior entity → show context chip
  useEffect(() => {
    if (!input.trim()) return;
    if (!detectContextRef(input)) return;
    // find last assistant message that mentions an accused id
    for (let i = messages.length - 1; i >= 0; i--) {
      const m = messages[i];
      if (m.role !== "assistant") continue;
      const id = extractAccusedId(m.text) || (m.sql && extractAccusedId(m.sql));
      if (id) {
        setContextEntity(`Accused ${id}`);
        break;
      }
    }
  }, [input, messages]);

  function stopListening() {
    try {
      recognitionRef.current?.stop();
    } catch {}
    setListening(false);
  }

  function startListening() {
    if (!SR) return;
    const rec = new SR();
    rec.lang = "en-US";
    rec.interimResults = true;
    rec.continuous = false;
    rec.onresult = (ev: any) => {
      let finalText = "";
      for (let i = ev.resultIndex; i < ev.results.length; i++) {
        finalText += ev.results[i][0].transcript;
      }
      setInput((prev) => (prev ? prev.trimEnd() + " " : "") + finalText.trim());
    };
    rec.onerror = (ev: any) => {
      toast.error("Voice input error", { description: ev.error ?? "Unknown error" });
      setListening(false);
    };
    rec.onend = () => setListening(false);
    recognitionRef.current = rec;
    setListening(true);
    try {
      rec.start();
    } catch (e) {
      setListening(false);
    }
  }

  async function send(text: string) {
    const q = text.trim();
    if (!q || loading) return;
    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      text: q,
      ts: new Date().toISOString(),
    };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setLoading(true);
    try {
      const reply = await askAssistant(q);
      setMessages((m) => [...m, reply]);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }

  function exportPdf() {
    const doc = new jsPDF({ unit: "pt", format: "a4" });
    const marginX = 40;
    let y = 50;
    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    const usable = pageWidth - marginX * 2;

    const addLine = (text: string, opts?: { size?: number; bold?: boolean; color?: [number, number, number] }) => {
      const size = opts?.size ?? 10;
      doc.setFont("helvetica", opts?.bold ? "bold" : "normal");
      doc.setFontSize(size);
      const [r, g, b] = opts?.color ?? [30, 30, 30];
      doc.setTextColor(r, g, b);
      const lines = doc.splitTextToSize(text, usable);
      for (const line of lines) {
        if (y > pageHeight - 50) {
          doc.addPage();
          y = 50;
        }
        doc.text(line, marginX, y);
        y += size + 3;
      }
    };

    addLine(SEED_SESSION.title, { size: 16, bold: true });
    addLine(`Exported ${format(new Date(), "d MMM yyyy · HH:mm")}`, {
      size: 9,
      color: [110, 110, 110],
    });
    y += 8;
    doc.setDrawColor(200);
    doc.line(marginX, y, pageWidth - marginX, y);
    y += 14;

    for (const m of messages) {
      const who = m.role === "user" ? "User" : `Assistant${m.agent ? " · " + m.agent : ""}`;
      addLine(`${who}  ·  ${format(new Date(m.ts), "d MMM · HH:mm")}`, {
        size: 9,
        bold: true,
        color: m.role === "user" ? [40, 60, 120] : [70, 90, 60],
      });
      addLine(m.text, { size: 11 });
      if (m.sql) {
        y += 4;
        addLine("SQL:", { size: 9, bold: true, color: [90, 90, 90] });
        doc.setFont("courier", "normal");
        doc.setFontSize(9);
        doc.setTextColor(60, 60, 60);
        const sqlLines = doc.splitTextToSize(m.sql, usable);
        for (const line of sqlLines) {
          if (y > pageHeight - 50) {
            doc.addPage();
            y = 50;
          }
          doc.text(line, marginX, y);
          y += 11;
        }
        if (m.rows !== undefined) {
          addLine(`(${m.rows} row${m.rows === 1 ? "" : "s"})`, {
            size: 9,
            color: [130, 130, 130],
          });
        }
      }
      y += 10;
    }

    const filename = `chat-${format(new Date(), "yyyyMMdd-HHmm")}.pdf`;
    doc.save(filename);
    toast.success("PDF downloaded", { description: filename });
  }

  return (
    <div className="flex h-full">
      {/* Main chat column */}
      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex items-center justify-between border-b border-border bg-card px-5 py-3">
          <div>
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              <h1 className="text-sm font-semibold">{t("chatTitle")}</h1>
              <Badge variant="secondary" className="text-[10px] font-medium">
                {t("chatBadge")}
              </Badge>
              <MockBadge />
            </div>
            <div className="text-xs text-muted-foreground mt-0.5">{t("chatSubtitle")}</div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setHistoryOpen((v) => !v)}
              className="gap-1.5"
            >
              <History className="h-3.5 w-3.5" /> {t("history")}
            </Button>
            <Button variant="outline" size="sm" onClick={exportPdf} className="gap-1.5">
              <FileDown className="h-3.5 w-3.5" /> {t("exportPdf")}
            </Button>
          </div>
        </div>

        <div ref={scrollRef} className="flex-1 overflow-y-auto scrollbar-thin px-5 py-6 space-y-5">
          {messages.map((m) => (
            <MessageRow key={m.id} m={m} />
          ))}
          {loading && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground animate-pulse">
              <Bot className="h-4 w-4" /> {t("analysing")}
            </div>
          )}
        </div>

        <div className="border-t border-border bg-card px-5 py-3">
          {contextEntity && (
            <div className="mb-2 flex items-center gap-2">
              <div className="inline-flex items-center gap-1.5 rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs text-primary">
                <span className="font-medium">Context:</span>
                <span>{contextEntity}</span>
                <button
                  onClick={() => setContextEntity(null)}
                  className="ml-1 rounded-full hover:bg-primary/20 p-0.5"
                  aria-label="Clear context"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
              <span className="text-[11px] text-muted-foreground">Click × to clear</span>
            </div>
          )}
          <div className="flex flex-wrap gap-1.5 mb-2.5">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => send(s)}
                className="text-xs rounded-full border border-border bg-background px-3 py-1 hover:border-primary hover:text-primary transition-colors"
              >
                {s}
              </button>
            ))}
          </div>
          <div className="flex items-end gap-2">
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    send(input);
                  }
                }}
                rows={2}
                placeholder={t("askPlaceholder")}
                className="w-full resize-none rounded-md border border-input bg-background px-3 py-2 pr-24 text-sm focus:outline-none focus:ring-2 focus:ring-ring/40"
              />
              <div className="absolute right-2 bottom-2 flex items-center gap-1">
                <TooltipProvider delayDuration={200}>
                  <UITooltip>
                    <TooltipTrigger asChild>
                      <button
                        onClick={() => {
                          if (!speechSupported) return;
                          listening ? stopListening() : startListening();
                        }}
                        disabled={!speechSupported}
                        className={cn(
                          "h-8 w-8 rounded flex items-center justify-center hover:bg-accent relative",
                          !speechSupported && "opacity-40 cursor-not-allowed",
                          listening && "bg-destructive/10 text-destructive",
                        )}
                      >
                        <Mic className="h-4 w-4" />
                        {listening && (
                          <span className="absolute -top-0.5 -right-0.5 h-2 w-2 rounded-full bg-destructive animate-pulse ring-2 ring-card" />
                        )}
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="top" className="text-xs">
                      {speechSupported
                        ? listening
                          ? "Stop listening"
                          : "Start voice input"
                        : t("voiceUnsupported")}
                    </TooltipContent>
                  </UITooltip>
                </TooltipProvider>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground uppercase tracking-wider">
                  EN
                </span>
              </div>
            </div>
            <Button onClick={() => send(input)} disabled={loading || !input.trim()} className="h-11 px-4">
              <Send className="h-4 w-4 mr-1.5" /> {t("send")}
            </Button>
          </div>
          <div className="text-[11px] text-muted-foreground mt-2">
            {t("explainabilityNote")}
          </div>
          <div className="text-[11px] text-muted-foreground/80 italic mt-1">
            {t("translationNote")}
          </div>
        </div>
      </div>

      {historyOpen && (
        <aside className="w-72 border-l border-border bg-card overflow-y-auto scrollbar-thin animate-in slide-in-from-right duration-200">
          <div className="px-4 py-3 border-b border-border">
            <div className="text-xs uppercase tracking-wider text-muted-foreground font-medium">
              {t("historyTitle")}
            </div>
          </div>
          <ul className="p-2 space-y-1">
            {HISTORY_SESSIONS.map((s) => (
              <li key={s.id}>
                <button className="w-full text-left rounded px-3 py-2 hover:bg-accent">
                  <div className="text-sm font-medium truncate">{s.title}</div>
                  <div className="text-[11px] text-muted-foreground">
                    {format(new Date(s.updatedAt), "d MMM · HH:mm")}
                  </div>
                </button>
              </li>
            ))}
          </ul>
        </aside>
      )}
    </div>
  );
}

function MessageRow({ m }: { m: ChatMessage }) {
  const t = useT();
  const [showSql, setShowSql] = useState(false);
  const isUser = m.role === "user";

  return (
    <div className={cn("flex gap-3 animate-in fade-in duration-300", isUser && "justify-end")}>
      {!isUser && (
        <div className="h-8 w-8 rounded flex items-center justify-center bg-primary/10 text-primary shrink-0">
          <Bot className="h-4 w-4" />
        </div>
      )}
      <div className={cn("max-w-[80%] min-w-0", isUser && "order-1")}>
        {!isUser && m.agent && (
          <div className="mb-1">
            <Badge
              variant="outline"
              className={cn("text-[10px] font-medium border", AGENT_COLORS[m.agent])}
            >
              {m.agent}
            </Badge>
          </div>
        )}
        <div
          className={cn(
            "rounded-md px-4 py-3 text-sm",
            isUser
              ? "bg-primary text-primary-foreground"
              : "bg-card border-l-2 border-l-primary border border-border shadow-xs",
          )}
        >
          <div className="whitespace-pre-wrap leading-relaxed">{m.text}</div>
          {m.data && (
            <div className="mt-3">
              <RichCard data={m.data} />
            </div>
          )}
        </div>

        <div
          className={cn(
            "flex items-center gap-2 mt-1.5 text-[11px] text-muted-foreground",
            isUser && "justify-end",
          )}
        >
          <span>{format(new Date(m.ts), "d MMM · HH:mm")}</span>
          {!isUser && m.sql && (
            <button
              onClick={() => setShowSql((v) => !v)}
              className="inline-flex items-center gap-0.5 hover:text-foreground"
            >
              {showSql ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
              {t("showReasoning")} · {m.rows} row{m.rows === 1 ? "" : "s"}
            </button>
          )}
        </div>

        {!isUser && showSql && m.sql && (
          <pre className="mt-2 rounded border border-border bg-muted/60 p-3 text-[11px] font-mono leading-relaxed overflow-x-auto text-foreground">
{m.sql}
          </pre>
        )}
      </div>
      {isUser && (
        <div className="h-8 w-8 rounded bg-muted flex items-center justify-center shrink-0">
          <UserIcon className="h-4 w-4 text-muted-foreground" />
        </div>
      )}
    </div>
  );
}

function RichCard({ data }: { data: RichData }) {
  if (data.kind === "stat") {
    const up = (data.delta ?? 0) >= 0;
    return (
      <div className="rounded border border-border bg-background p-3 text-foreground">
        <div className="text-[11px] uppercase tracking-wider text-muted-foreground">{data.title}</div>
        <div className="mt-1 flex items-baseline gap-2">
          <span className="text-2xl font-semibold tabular-nums">{data.value}</span>
          {data.unit && <span className="text-xs text-muted-foreground">{data.unit}</span>}
          {data.delta !== undefined && (
            <span className={cn("text-xs font-medium", up ? "text-success" : "text-destructive")}>
              {up ? "▲" : "▼"} {Math.abs(data.delta).toFixed(1)}%
            </span>
          )}
        </div>
      </div>
    );
  }

  if (data.kind === "table") {
    return (
      <div className="rounded border border-border bg-background text-foreground overflow-hidden">
        <div className="px-3 py-2 border-b border-border text-[11px] uppercase tracking-wider text-muted-foreground">
          {data.title}
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-muted/50">
                {data.columns?.map((c) => (
                  <th key={c} className="text-left px-3 py-2 font-medium">
                    {c}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.rows?.map((r, i) => (
                <tr key={i} className="border-t border-border">
                  {r.map((cell, j) => (
                    <td key={j} className="px-3 py-2 tabular-nums">
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  const Comp = data.chartKind === "line" ? LineChart : BarChart;
  return (
    <div className="rounded border border-border bg-background p-3 text-foreground">
      <div className="text-[11px] uppercase tracking-wider text-muted-foreground mb-2">
        {data.title}
      </div>
      <div className="h-40">
        <ResponsiveContainer width="100%" height="100%">
          <Comp data={data.chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
            <XAxis dataKey="label" tick={{ fontSize: 11 }} stroke="var(--color-muted-foreground)" />
            <YAxis tick={{ fontSize: 11 }} stroke="var(--color-muted-foreground)" />
            <Tooltip
              contentStyle={{
                fontSize: 12,
                borderRadius: 6,
                border: "1px solid var(--color-border)",
                background: "var(--color-card)",
              }}
            />
            {data.chartKind === "line" ? (
              <Line dataKey="value" stroke="var(--color-primary)" strokeWidth={2} dot={{ r: 3 }} />
            ) : (
              <Bar dataKey="value" fill="var(--color-primary)" radius={[3, 3, 0, 0]} />
            )}
          </Comp>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
