import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import { useLanguage } from "../context/LanguageContext";
import { format } from "date-fns";
import {
  Send,
  Mic,
  MicOff,
  ChevronDown,
  ChevronRight,
  Sparkles,
  History,
  FileDown,
  Bot,
  User as UserIcon,
  X,
  Trash2,
  Loader2,
  AlertCircle,
  Plus,
  Headphones,
  Play,
  Pause,
  Square,
  RotateCcw,
  Volume2,
  VolumeX,
  Globe,
  Check,
  CheckCheck,
} from "lucide-react";
import { useSpeechSynthesis } from "../hooks/useSpeechSynthesis";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
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
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip as UITooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { useT } from "@/lib/i18n";
import type { ChatMessage, RichData, AgentKind } from "@/types/chat";
import { askAssistant, detectContextRef, extractAccusedId } from "@/services/assistant";
import { listConversations, deleteConversation } from "@/lib/api/services";
import { queryKeys } from "@/lib/api/query-keys";
import { toast } from "sonner";
import { useAuthStore } from "@/stores/auth";
import { hasPermission, PERMISSIONS } from "@/lib/rbac";
import type { Language } from "@/context/LanguageContext";

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

const LANG_OPTIONS: { value: Language; label: string; native: string; flag: string }[] = [
  { value: "auto", label: "Auto Detect", native: "Auto", flag: "🌐" },
  { value: "en", label: "English", native: "English", flag: "🇮🇳" },
  { value: "kn", label: "Kannada", native: "ಕನ್ನಡ", flag: "🏔️" },
];

// Feature-detect SpeechRecognition
function getSpeechRecognition(): unknown | null {
  if (typeof window === "undefined") return null;
  return (
    (window as unknown as Record<string, unknown>).SpeechRecognition ||
    (window as unknown as Record<string, unknown>).webkitSpeechRecognition ||
    null
  );
}

// ─── Speaking Waveform Animation ────────────────────────────────────────────
function SpeakingWaveform({ active, className }: { active: boolean; className?: string }) {
  return (
    <span
      className={cn("inline-flex items-end gap-[2px] h-3.5", className)}
      aria-label={active ? "Speaking" : ""}
      role="img"
    >
      {[0, 1, 2, 3, 4].map((i) => (
        <span
          key={i}
          className={cn(
            "w-[2px] rounded-full bg-current transition-all",
            active
              ? "animate-bounce"
              : "h-1",
          )}
          style={
            active
              ? {
                  animationDelay: `${i * 80}ms`,
                  animationDuration: "600ms",
                  height: `${6 + (i % 3) * 4}px`,
                }
              : { height: "4px" }
          }
        />
      ))}
    </span>
  );
}

// ─── Recording Pulse Indicator ───────────────────────────────────────────────
function RecordingIndicator({ active }: { active: boolean }) {
  if (!active) return null;
  return (
    <span className="inline-flex items-center gap-1.5" aria-live="polite" aria-label="Recording active">
      <span className="relative flex h-2.5 w-2.5">
        <span className="absolute inline-flex h-full w-full rounded-full bg-destructive opacity-75 animate-ping" />
        <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-destructive" />
      </span>
      <span className="text-destructive text-[10px] font-semibold uppercase tracking-widest">REC</span>
    </span>
  );
}

// ─── Typing Animation ────────────────────────────────────────────────────────
function TypingDots() {
  return (
    <span className="inline-flex items-center gap-1" aria-label="Assistant is typing" role="status">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="h-1.5 w-1.5 rounded-full bg-muted-foreground animate-bounce"
          style={{ animationDelay: `${i * 150}ms`, animationDuration: "900ms" }}
        />
      ))}
    </span>
  );
}

// ─── Message Status Icon ─────────────────────────────────────────────────────
function MessageStatus({ role, speaking }: { role: "user" | "assistant"; speaking?: boolean }) {
  if (role === "assistant") {
    if (speaking) {
      return (
        <span className="inline-flex items-center gap-1 text-primary text-[10px]">
          <SpeakingWaveform active={true} />
          <span>Speaking</span>
        </span>
      );
    }
    return null;
  }
  return (
    <CheckCheck className="h-3 w-3 text-primary/60" aria-label="Delivered" />
  );
}

// ─── Voice Status Bar ────────────────────────────────────────────────────────
function VoiceStatusBar({
  detectedLang,
  preferredLang,
  currentVoice,
  isPlaying,
  isPaused,
  listening,
  onStop,
  onReplay,
  onPause,
  onResume,
}: {
  detectedLang: string;
  preferredLang: string;
  currentVoice: string;
  isPlaying: boolean;
  isPaused: boolean;
  listening: boolean;
  onStop: () => void;
  onReplay: () => void;
  onPause: () => void;
  onResume: () => void;
}) {
  const hasActivity = isPlaying || isPaused || listening;

  return (
    <div
      className={cn(
        "flex flex-wrap items-center justify-between gap-x-4 gap-y-1.5 px-5 py-1.5 text-[11px] border-b border-border transition-all duration-300",
        hasActivity
          ? "bg-primary/5 border-primary/20"
          : "bg-muted/20",
      )}
      aria-label="Voice and language status bar"
      role="status"
    >
      {/* Left: Status info */}
      <div className="flex items-center flex-wrap gap-x-3 gap-y-1">
        <RecordingIndicator active={listening} />

        {isPlaying && !isPaused && (
          <span className="inline-flex items-center gap-1.5 text-primary font-medium">
            <SpeakingWaveform active={true} className="text-primary" />
            <span>Speaking…</span>
          </span>
        )}
        {isPaused && (
          <span className="text-warning font-medium">⏸ Paused</span>
        )}
        {!listening && !isPlaying && !isPaused && (
          <span className="text-muted-foreground">Ready</span>
        )}

        <span className="text-muted-foreground/60">|</span>

        <span className="text-muted-foreground">
          <span className="font-medium text-foreground">Detected:</span>{" "}
          {detectedLang}
        </span>
        <span className="text-muted-foreground">
          <span className="font-medium text-foreground">Preferred:</span>{" "}
          {preferredLang}
        </span>
        <span className="text-muted-foreground">
          <span className="font-medium text-foreground">Voice:</span>{" "}
          <span className="font-mono truncate max-w-[120px] inline-block align-bottom">{currentVoice || "—"}</span>
        </span>
      </div>

      {/* Right: Quick controls */}
      {(isPlaying || isPaused) && (
        <div className="flex items-center gap-1" role="group" aria-label="Playback controls">
          <TooltipProvider delayDuration={200}>
            <UITooltip>
              <TooltipTrigger asChild>
                <button
                  onClick={isPaused ? onResume : onPause}
                  className="h-6 w-6 rounded flex items-center justify-center hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
                  aria-label={isPaused ? "Resume speaking" : "Pause speaking"}
                >
                  {isPaused ? <Play className="h-3 w-3 fill-current" /> : <Pause className="h-3 w-3" />}
                </button>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="text-xs">{isPaused ? "Resume" : "Pause"}</TooltipContent>
            </UITooltip>

            <UITooltip>
              <TooltipTrigger asChild>
                <button
                  onClick={onStop}
                  className="h-6 w-6 rounded flex items-center justify-center hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors"
                  aria-label="Stop speaking"
                >
                  <Square className="h-3 w-3 fill-current" />
                </button>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="text-xs">Stop</TooltipContent>
            </UITooltip>

            <UITooltip>
              <TooltipTrigger asChild>
                <button
                  onClick={onReplay}
                  className="h-6 w-6 rounded flex items-center justify-center hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
                  aria-label="Replay last speech"
                >
                  <RotateCcw className="h-3 w-3" />
                </button>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="text-xs">Replay</TooltipContent>
            </UITooltip>
          </TooltipProvider>
        </div>
      )}
    </div>
  );
}

function ChatPage() {
  const t = useT();
  const user = useAuthStore((s) => s.user);
  const queryClient = useQueryClient();
  const { language, setLanguage, recognitionLanguage, resolvedLanguage } = useLanguage();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [listening, setListening] = useState(false);
  const [contextEntity, setContextEntity] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [speakingMsgId, setSpeakingMsgId] = useState<string | null>(null);
  const [introShown, setIntroShown] = useState(false);
  const [introText, setIntroText] = useState("");
  const introSpokenRef = useRef(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const recognitionRef = useRef<any>(null);
  const silenceTimerRef = useRef<any>(null);
  const initialInputRef = useRef("");
  const accumulatedInputRef = useRef("");

  const [voicePanelOpen, setVoicePanelOpen] = useState(false);
  const {
    isPlaying,
    isPaused,
    rate,
    pitch,
    volume,
    language: ttsLanguage,
    autoSpeak,
    filteredVoices,
    selectedVoice,
    speak,
    pause,
    resume,
    stop,
    replay,
    setRate,
    setPitch,
    setVolume,
    setLanguage: setTtsLanguage,
    setAutoSpeak,
    setSelectedVoice,
  } = useSpeechSynthesis();

  const SR = useMemo(() => getSpeechRecognition(), []);
  const speechSupported = !!SR;

  const stopListening = useCallback(() => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
    try {
      (recognitionRef.current as any)?.stop();
    } catch (e) {
      console.warn("Speech recognition stop failed:", e);
    }
    setListening(false);
  }, []);

  const handleSpeak = useCallback(
    (text: string, msgId?: string) => {
      speak(text);
      if (msgId) setSpeakingMsgId(msgId);
    },
    [speak],
  );

  const send = useCallback(
    async (text: string) => {
      const q = text.trim();
      if (!q || loading) return;
      setChatError(null);

      const asksForSensitiveData = /\b(victim address|victim phone|phone number|bank account|account number|address)\b/i.test(q);
      if (asksForSensitiveData && !hasPermission(user, PERMISSIONS.SENSITIVE_CASE_ACCESS)) {
        const denied: ChatMessage = {
          id: crypto.randomUUID(),
          role: "assistant",
          text: "You do not have permission to access victim addresses, phone numbers, or financial account details. I can still help with permitted case summaries, trends, maps, and pattern analysis for your role.",
          ts: new Date().toISOString(),
        };
        setMessages((m) => [
          ...m,
          { id: crypto.randomUUID(), role: "user", text: q, ts: new Date().toISOString() },
          denied,
        ]);
        setInput("");
        return;
      }

      if (listening) {
        stopListening();
      }

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
        const reply = await askAssistant(q, conversationId, language);
        const replyWithId = reply as ChatMessage & { conversationId?: string };
        if (replyWithId.conversationId && !conversationId) {
          setConversationId(replyWithId.conversationId);
          queryClient.invalidateQueries({ queryKey: queryKeys.conversations() });
        }
        setMessages((m) => [...m, { ...reply, id: reply.id }]);
        if (autoSpeak) {
          handleSpeak(reply.text, reply.id);
        }
      } catch (err: unknown) {
        const message =
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
          (err as { message?: string })?.message ??
          "The assistant encountered an error. Please try again.";
        setChatError(message);
        toast.error("Chat failed", { description: message });
      } finally {
        setLoading(false);
        setTimeout(() => inputRef.current?.focus(), 50);
      }
    },
    [loading, conversationId, queryClient, autoSpeak, handleSpeak, language, listening, stopListening, user],
  );

  const startListening = useCallback(() => {
    if (!SR) return;

    // Abort any existing instance first to prevent concurrent instances conflict
    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort();
      } catch (e) {
        console.warn("Failed to abort existing speech recognition:", e);
      }
    }

    initialInputRef.current = input;
    accumulatedInputRef.current = "";

    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
    }

    const resetSilenceTimer = () => {
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
      }
      silenceTimerRef.current = setTimeout(() => {
        stopListening();
        toast.info("Voice input stopped", {
          description: "Listening timed out due to inactivity.",
        });
      }, 8000);
    };

    const SRClass = SR as new () => any;
    const rec = new SRClass();
    rec.lang = recognitionLanguage;
    rec.interimResults = true;
    rec.continuous = false;

    rec.onresult = (ev: any) => {
      resetSilenceTimer();
      let finalTranscript = "";
      let interimTranscript = "";

      for (let i = 0; i < ev.results.length; ++i) {
        if (ev.results[i].isFinal) {
          finalTranscript += ev.results[i][0].transcript;
        } else {
          interimTranscript += ev.results[i][0].transcript;
        }
      }

      const fullTranscript = (finalTranscript + interimTranscript).trim();
      const base = initialInputRef.current ? initialInputRef.current.trim() : "";
      const textToSubmit = base ? base + " " + fullTranscript : fullTranscript;
      setInput(textToSubmit);
      accumulatedInputRef.current = textToSubmit;
    };

    rec.onerror = (ev: any) => {
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
        silenceTimerRef.current = null;
      }
      const err = ev.error;
      if (err === "not-allowed") {
        toast.error("Microphone access denied", {
          description: "Please allow microphone access in your browser settings to use voice input.",
        });
      } else if (err === "no-speech") {
        toast.warning("No speech detected", {
          description: "Speak clearly into your microphone.",
        });
      } else if (err === "aborted") {
        // Normal stop/abort — do not show error toast
        console.log("Speech recognition aborted normally.");
      } else {
        toast.error("Voice input error", {
          description: err ?? "Unknown error occurred",
        });
      }
      setListening(false);
    };

    rec.onend = () => {
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
        silenceTimerRef.current = null;
      }
      setListening(false);

      // Auto-send if there is accumulated content
      const text = accumulatedInputRef.current?.trim();
      if (text) {
        accumulatedInputRef.current = "";
        send(text);
      }
    };

    recognitionRef.current = rec;
    setListening(true);
    resetSilenceTimer();

    try {
      rec.start();
    } catch {
      setListening(false);
    }
  }, [SR, recognitionLanguage, stopListening, input, send]);

  function startNewConversation() {
    setConversationId(null);
    setMessages([]);
    setChatError(null);
    setContextEntity(null);
    inputRef.current?.focus();
  }

  function exportPdf() {
    // Check if iframe already exists, if so remove it
    const existingFrame = document.getElementById("print-iframe");
    if (existingFrame) {
      existingFrame.remove();
    }

    // Create a new invisible iframe
    const iframe = document.createElement("iframe");
    iframe.id = "print-iframe";
    iframe.style.position = "fixed";
    iframe.style.right = "0";
    iframe.style.bottom = "0";
    iframe.style.width = "0";
    iframe.style.height = "0";
    iframe.style.border = "none";
    document.body.appendChild(iframe);

    const doc = iframe.contentWindow?.document || iframe.contentDocument;
    if (!doc) {
      toast.error("Could not export PDF");
      return;
    }

    const title = `Chat Session${conversationId ? ` — ${conversationId.slice(0, 8)}` : ""}`;
    const formattedDate = format(new Date(), "d MMM yyyy HH:mm");

    const messagesHtml = messages
      .map((m) => {
        const who = m.role === "user" ? "User" : `Assistant${m.agent ? " · " + m.agent : ""}`;
        const color = m.role === "user" ? "#1e3a8a" : "#15803d";
        
        return `
          <div style="margin-bottom: 20px; border-bottom: 1px solid #f1f5f9; padding-bottom: 15px; page-break-inside: avoid;">
            <div style="font-size: 11px; font-weight: bold; color: ${color}; margin-bottom: 5px; font-family: 'Inter', sans-serif;">
              ${who} &middot; ${format(new Date(m.ts), "d MMM HH:mm")}
            </div>
            <div style="font-size: 13px; color: #0f172a; line-height: 1.6; white-space: pre-wrap; font-family: 'Inter', 'Noto Sans Kannada', sans-serif;">
              ${m.text}
            </div>
            ${
              m.sql
                ? `
              <div style="margin-top: 10px; background: #f8fafc; padding: 10px; border-radius: 6px; border: 1px solid #e2e8f0; font-family: 'Courier New', Courier, monospace; font-size: 11px; color: #334155; page-break-inside: avoid;">
                <div style="font-weight: bold; color: #64748b; margin-bottom: 4px;">SQL:</div>
                <div style="white-space: pre-wrap; word-break: break-all;">${m.sql}</div>
                ${m.rows !== undefined ? `<div style="margin-top: 4px; color: #94a3b8;">(${m.rows} rows)</div>` : ""}
              </div>
            `
                : ""
            }
          </div>
        `;
      })
      .join("");

    doc.write(`
      <html>
        <head>
          <title>${title}</title>
          <link rel="preconnect" href="https://fonts.googleapis.com">
          <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
          <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Noto+Sans+Kannada:wght@400;600;700&display=swap" rel="stylesheet">
          <style>
            body {
              font-family: 'Inter', 'Noto Sans Kannada', sans-serif;
              padding: 20px;
              color: #0f172a;
              margin: 0;
            }
            .header {
              border-bottom: 2px solid #e2e8f0;
              padding-bottom: 15px;
              margin-bottom: 25px;
            }
            h1 {
              font-size: 20px;
              margin: 0 0 5px 0;
              color: #1e293b;
            }
            .meta {
              font-size: 11px;
              color: #64748b;
            }
            @media print {
              body {
                padding: 0;
              }
            }
          </style>
        </head>
        <body>
          <div class="header">
            <h1>${title}</h1>
            <div class="meta">Exported on ${formattedDate}</div>
          </div>
          <div class="content">
            ${messagesHtml}
          </div>
        </body>
      </html>
    `);
    doc.close();

    // Wait for content and Noto Sans Kannada font to load in the frame before printing
    setTimeout(() => {
      iframe.contentWindow?.focus();
      iframe.contentWindow?.print();
      // Remove the temporary iframe after printing is done/dismissed
      setTimeout(() => {
        iframe.remove();
      }, 5000);
    }, 1000);

    toast.success("PDF export initiated");
  }

  const SUGGESTIONS = [t("s1"), t("s2"), t("s3"), t("s4"), t("s5")];

  // ─── Conversation History ─────────────────────────────────────────────────
  const { data: conversations, isLoading: conversationsLoading } = useQuery({
    queryKey: queryKeys.conversations(),
    queryFn: () => listConversations({ limit: 30, sort_by: "updated_at", sort_order: "desc" }),
    enabled: historyOpen,
    staleTime: 60_000,
  });

  const deleteMutation = useMutation({
    mutationFn: deleteConversation,
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.conversations() });
      if (conversationId === id) {
        setConversationId(null);
        setMessages([]);
      }
      toast.success("Conversation deleted");
    },
    onError: () => {
      toast.error("Failed to delete conversation");
    },
  });

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // ─── Auto intro on first page open ───────────────────────────────────────
  useEffect(() => {
    if (introSpokenRef.current) return;
    introSpokenRef.current = true;
    const text = t("introGreeting");
    setIntroText(text);
    // Short delay so audio context is ready
    const tid = setTimeout(() => {
      setIntroShown(true);
      speak(text);
    }, 800);
    return () => clearTimeout(tid);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Context entity detection
  useEffect(() => {
    if (!input.trim()) return;
    if (!detectContextRef(input)) return;
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

  // ─── Keyboard Shortcuts ───────────────────────────────────────────────────
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      // Ctrl/Cmd + M → toggle mic
      if ((e.ctrlKey || e.metaKey) && e.key === "m") {
        e.preventDefault();
        if (!speechSupported) return;
        if (listening) stopListening();
        else startListening();
      }
      // Escape → stop playback or listening
      if (e.key === "Escape") {
        if (isPlaying || isPaused) stop();
        if (listening) stopListening();
      }
      // Ctrl/Cmd + H → toggle history
      if ((e.ctrlKey || e.metaKey) && e.key === "h") {
        e.preventDefault();
        setHistoryOpen((v) => !v);
      }
      // Ctrl/Cmd + Shift + N → new chat
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === "N") {
        e.preventDefault();
        startNewConversation();
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [speechSupported, listening, isPlaying, isPaused]);



  // Detected language label derived from TTS detection
  const detectedLangLabel = ttsLanguage === "kn-IN" ? "Kannada (kn)" : "English (en)";
  const preferredLangLabel =
    language === "auto"
      ? `Auto (${resolvedLanguage === "kn" ? "Kannada" : "English"})`
      : language === "kn"
        ? "Kannada"
        : "English";
  const currentVoiceName = selectedVoice?.name ?? "—";

  return (
    <TooltipProvider delayDuration={200}>
      <div className="flex h-full" role="main">
        {/* Main chat column */}
        <div className="flex-1 flex flex-col min-w-0">

          {/* ── Header ──────────────────────────────────────────────────────── */}
          <header
            className="flex flex-wrap items-center justify-between gap-2 border-b border-border bg-card px-3 sm:px-5 py-2.5"
            aria-label="Chat assistant header"
          >
            <div className="flex items-center gap-2 min-w-0">
              <Sparkles className="h-4 w-4 text-primary shrink-0" aria-hidden="true" />
              <h1 className="text-sm font-semibold truncate">{t("chatTitle")}</h1>
              <Badge variant="secondary" className="text-[10px] font-medium hidden sm:flex">
                {t("chatBadge")}
              </Badge>
              {conversationId && (
                <Badge variant="outline" className="text-[10px] font-mono text-muted-foreground hidden sm:flex">
                  {conversationId.slice(0, 8)}…
                </Badge>
              )}
            </div>

            {/* Header actions */}
            <div className="flex items-center gap-1.5 flex-wrap">
              {/* Language Selector */}
              <DropdownMenu>
                <UITooltip>
                  <TooltipTrigger asChild>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-8 px-2.5 gap-1.5 text-xs"
                        aria-label={`Language: ${preferredLangLabel}. Press to change.`}
                        id="language-selector"
                      >
                        <Globe className="h-3.5 w-3.5" aria-hidden="true" />
                        <span className="hidden sm:inline">{preferredLangLabel}</span>
                        <span className="sm:hidden text-[10px] uppercase">
                          {language === "auto" ? "AUTO" : language.toUpperCase()}
                        </span>
                      </Button>
                    </DropdownMenuTrigger>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="text-xs">
                    Select response language
                  </TooltipContent>
                </UITooltip>
                <DropdownMenuContent align="end" className="w-44">
                  {LANG_OPTIONS.map((opt) => (
                    <DropdownMenuItem
                      key={opt.value}
                      onClick={() => setLanguage(opt.value)}
                      className="flex items-center justify-between text-xs cursor-pointer"
                      aria-checked={language === opt.value}
                      role="menuitemradio"
                    >
                      <span className="flex items-center gap-2">
                        <span>{opt.flag}</span>
                        <span>{opt.label}</span>
                        {opt.value !== "auto" && (
                          <span className="text-muted-foreground">({opt.native})</span>
                        )}
                      </span>
                      {language === opt.value && <Check className="h-3.5 w-3.5 text-primary" />}
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>

              {/* Voice Controls Button */}
              <UITooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setVoicePanelOpen((v) => !v)}
                    className={cn(
                      "h-8 gap-1.5 px-2.5",
                      (isPlaying || voicePanelOpen) && "border-primary text-primary bg-primary/5",
                    )}
                    aria-label={voicePanelOpen ? "Close voice controls" : "Open voice controls"}
                    aria-expanded={voicePanelOpen}
                    aria-controls="voice-panel"
                  >
                    <Headphones
                      className={cn("h-3.5 w-3.5", isPlaying && !isPaused && "animate-pulse")}
                      aria-hidden="true"
                    />
                    <span className="hidden sm:inline">
                      {isPlaying && !isPaused ? "Speaking…" : "Voice"}
                    </span>
                    {isPlaying && !isPaused && (
                      <SpeakingWaveform active={true} className="text-primary hidden sm:inline-flex" />
                    )}
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">
                  Voice controls (speaker settings)
                </TooltipContent>
              </UITooltip>

              <UITooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={startNewConversation}
                    className="h-8 gap-1.5 px-2.5"
                    aria-label="Start new conversation (Ctrl+Shift+N)"
                    title="Ctrl+Shift+N"
                  >
                    <Plus className="h-3.5 w-3.5" aria-hidden="true" />
                    <span className="hidden sm:inline">New</span>
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">
                  New chat <kbd className="ml-1 rounded bg-muted px-1 py-0.5 text-[9px] font-mono">Ctrl+Shift+N</kbd>
                </TooltipContent>
              </UITooltip>

              <UITooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setHistoryOpen((v) => !v)}
                    className={cn("h-8 gap-1.5 px-2.5", historyOpen && "border-primary text-primary bg-primary/5")}
                    aria-label="Toggle conversation history (Ctrl+H)"
                    aria-expanded={historyOpen}
                    aria-controls="history-panel"
                    title="Ctrl+H"
                  >
                    <History className="h-3.5 w-3.5" aria-hidden="true" />
                    <span className="hidden sm:inline">{t("history")}</span>
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">
                  History <kbd className="ml-1 rounded bg-muted px-1 py-0.5 text-[9px] font-mono">Ctrl+H</kbd>
                </TooltipContent>
              </UITooltip>

              <UITooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={exportPdf}
                    className="h-8 gap-1.5 px-2.5"
                    aria-label="Export chat as PDF"
                    disabled={messages.length === 0}
                  >
                    <FileDown className="h-3.5 w-3.5" aria-hidden="true" />
                    <span className="hidden sm:inline">{t("exportPdf")}</span>
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">Export as PDF</TooltipContent>
              </UITooltip>
            </div>
          </header>

          {/* ── Voice Status Bar ─────────────────────────────────────────────── */}
          <VoiceStatusBar
            detectedLang={detectedLangLabel}
            preferredLang={preferredLangLabel}
            currentVoice={currentVoiceName}
            isPlaying={isPlaying}
            isPaused={isPaused}
            listening={listening}
            onStop={stop}
            onReplay={replay}
            onPause={pause}
            onResume={resume}
          />

          {/* ── Voice Control Panel ──────────────────────────────────────────── */}
          {voicePanelOpen && (
            <section
              id="voice-panel"
              className="border-b border-border bg-muted/30 p-4 space-y-4 animate-in slide-in-from-top duration-250"
              aria-label="Voice assistant controls"
            >
              {/* Row 1: Player Controls */}
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div
                    className={cn(
                      "flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary transition-all",
                      isPlaying && !isPaused && "ring-2 ring-primary/30 ring-offset-1",
                    )}
                    aria-hidden="true"
                  >
                    {isPlaying && !isPaused ? (
                      <SpeakingWaveform active={true} className="text-primary" />
                    ) : (
                      <Headphones className="h-4 w-4" />
                    )}
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-foreground">Voice Assistant</div>
                    <div className="text-[10px] text-muted-foreground">
                      {isPlaying ? (isPaused ? "Paused" : "Speaking response…") : "Idle"}
                    </div>
                  </div>
                </div>

                {/* Playback Controls */}
                <div className="flex items-center gap-1.5" role="group" aria-label="Playback controls">
                  <UITooltip>
                    <TooltipTrigger asChild>
                      <Button
                        variant="outline"
                        size="icon"
                        className="h-8 w-8 rounded-full"
                        onClick={() => {
                          if (isPaused) {
                            resume();
                          } else if (isPlaying) {
                            pause();
                          } else {
                            const lastAssistantMsg = [...messages].reverse().find((m) => m.role === "assistant");
                            if (lastAssistantMsg) handleSpeak(lastAssistantMsg.text, lastAssistantMsg.id);
                          }
                        }}
                        aria-label={isPlaying && !isPaused ? "Pause speaking" : "Play / Resume"}
                      >
                        {isPlaying && !isPaused ? (
                          <Pause className="h-3.5 w-3.5" />
                        ) : (
                          <Play className="h-3.5 w-3.5 fill-foreground ml-0.5" />
                        )}
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent className="text-xs">
                      {isPlaying && !isPaused ? "Pause" : "Play / Resume"}
                    </TooltipContent>
                  </UITooltip>

                  <UITooltip>
                    <TooltipTrigger asChild>
                      <Button
                        variant="outline"
                        size="icon"
                        className="h-8 w-8 rounded-full"
                        onClick={stop}
                        disabled={!isPlaying && !isPaused}
                        aria-label="Stop speaking"
                      >
                        <Square className="h-3.5 w-3.5 fill-foreground" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent className="text-xs">Stop</TooltipContent>
                  </UITooltip>

                  <UITooltip>
                    <TooltipTrigger asChild>
                      <Button
                        variant="outline"
                        size="icon"
                        className="h-8 w-8 rounded-full"
                        onClick={replay}
                        disabled={!isPlaying && !isPaused}
                        aria-label="Replay last response"
                      >
                        <RotateCcw className="h-3.5 w-3.5" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent className="text-xs">Replay</TooltipContent>
                  </UITooltip>

                  {/* Mute / Unmute volume quick toggle */}
                  <UITooltip>
                    <TooltipTrigger asChild>
                      <Button
                        variant="outline"
                        size="icon"
                        className="h-8 w-8 rounded-full"
                        onClick={() => setVolume(volume > 0 ? 0 : 1)}
                        aria-label={volume > 0 ? "Mute speaker" : "Unmute speaker"}
                      >
                        {volume > 0 ? (
                          <Volume2 className="h-3.5 w-3.5" />
                        ) : (
                          <VolumeX className="h-3.5 w-3.5" />
                        )}
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent className="text-xs">{volume > 0 ? "Mute" : "Unmute"}</TooltipContent>
                  </UITooltip>
                </div>

                {/* Auto Speak Switch */}
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground" id="auto-speak-label">
                    Auto-speak
                  </span>
                  <Switch
                    checked={autoSpeak}
                    onCheckedChange={setAutoSpeak}
                    id="auto-speak-toggle"
                    aria-labelledby="auto-speak-label"
                  />
                </div>
              </div>

              {/* Row 2: Voice Settings */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 pt-3 border-t border-border/60">
                {/* TTS Language Selector */}
                <div className="space-y-1.5">
                  <label
                    className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider"
                    id="tts-lang-label"
                  >
                    Speaker Language
                  </label>
                  <div
                    className="flex rounded-md border border-input overflow-hidden text-xs bg-background h-8"
                    role="group"
                    aria-labelledby="tts-lang-label"
                  >
                    <button
                      type="button"
                      onClick={() => setTtsLanguage("en-IN")}
                      className={cn(
                        "flex-1 font-medium transition-colors",
                        ttsLanguage === "en-IN" ? "bg-primary text-primary-foreground" : "hover:bg-accent",
                      )}
                      aria-pressed={ttsLanguage === "en-IN"}
                      aria-label="English speaker"
                    >
                      English
                    </button>
                    <button
                      type="button"
                      onClick={() => setTtsLanguage("kn-IN")}
                      className={cn(
                        "flex-1 font-medium transition-colors",
                        ttsLanguage === "kn-IN" ? "bg-primary text-primary-foreground" : "hover:bg-accent",
                      )}
                      aria-pressed={ttsLanguage === "kn-IN"}
                      aria-label="Kannada speaker"
                    >
                      ಕನ್ನಡ
                    </button>
                  </div>
                </div>

                {/* Voice Selector */}
                <div className="space-y-1.5">
                  <label
                    htmlFor="voice-select"
                    className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider"
                  >
                    Voice
                  </label>
                  <select
                    id="voice-select"
                    value={selectedVoice?.name || ""}
                    onChange={(e) => {
                      const voice = filteredVoices.find((v) => v.name === e.target.value);
                      if (voice) setSelectedVoice(voice);
                    }}
                    className="w-full text-xs rounded-md border border-input bg-background px-2.5 h-8 focus:outline-none focus:ring-1 focus:ring-ring"
                    aria-label="Select voice"
                  >
                    {filteredVoices.length === 0 ? (
                      <option value="">No voices available</option>
                    ) : (
                      filteredVoices.map((v) => {
                        const isFallback = !v.lang.toLowerCase().startsWith(ttsLanguage.split("-")[0].toLowerCase());
                        return (
                          <option key={v.name} value={v.name}>
                            {isFallback ? "[Fallback] " : ""}{v.name} ({v.lang})
                          </option>
                        );
                      })
                    )}
                  </select>
                </div>

                {/* Volume */}
                <div className="space-y-1.5">
                  <div className="flex justify-between items-center">
                    <label
                      htmlFor="volume-slider"
                      className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider"
                    >
                      Volume
                    </label>
                    <span className="text-[10px] font-mono" aria-live="polite">{Math.round(volume * 100)}%</span>
                  </div>
                  <div className="flex items-center h-8">
                    <Slider
                      id="volume-slider"
                      value={[volume]}
                      min={0}
                      max={1}
                      step={0.05}
                      onValueChange={(val) => setVolume(val[0])}
                      aria-label="Volume"
                    />
                  </div>
                </div>

                {/* Rate */}
                <div className="space-y-1.5">
                  <div className="flex justify-between items-center">
                    <label
                      htmlFor="rate-slider"
                      className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider"
                    >
                      Speed
                    </label>
                    <span className="text-[10px] font-mono" aria-live="polite">{rate.toFixed(1)}x</span>
                  </div>
                  <div className="flex items-center h-8">
                    <Slider
                      id="rate-slider"
                      value={[rate]}
                      min={0.5}
                      max={2.0}
                      step={0.1}
                      onValueChange={(val) => setRate(val[0])}
                      aria-label="Playback speed"
                    />
                  </div>
                </div>

                {/* Pitch */}
                <div className="space-y-1.5">
                  <div className="flex justify-between items-center">
                    <label
                      htmlFor="pitch-slider"
                      className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider"
                    >
                      Pitch
                    </label>
                    <span className="text-[10px] font-mono" aria-live="polite">{pitch.toFixed(1)}</span>
                  </div>
                  <div className="flex items-center h-8">
                    <Slider
                      id="pitch-slider"
                      value={[pitch]}
                      min={0.5}
                      max={2.0}
                      step={0.1}
                      onValueChange={(val) => setPitch(val[0])}
                      aria-label="Voice pitch"
                    />
                  </div>
                </div>
              </div>
            </section>
          )}

          {/* ── Message List ─────────────────────────────────────────────────── */}
          <div
            ref={scrollRef}
            className="flex-1 overflow-y-auto scrollbar-thin px-3 sm:px-5 py-6 space-y-5 chat-aurora-bg"
            role="log"
            aria-label="Conversation messages"
            aria-live="polite"
          >
            {/* Aurora background blobs — always visible, animate continuously */}
            <div className="chat-aurora-blob-1" aria-hidden="true" />
            <div className="chat-aurora-blob-2" aria-hidden="true" />
            <div className="chat-aurora-blob-3" aria-hidden="true" />
            <div className="chat-aurora-shimmer" aria-hidden="true" />
            {/* Empty state + intro */}
            {messages.length === 0 && !loading && !chatError && (
              <div className="flex flex-col items-center justify-center h-full py-16 text-center text-muted-foreground animate-in fade-in duration-500 relative z-10">
                {/* Logo with animated glow ring */}
                <div className="relative mb-5">
                  <div
                    className={cn(
                      "absolute inset-0 rounded-2xl blur-2xl transition-all duration-1000",
                      isPlaying
                        ? "bg-primary/30 scale-125 animate-pulse"
                        : "bg-primary/10 scale-100",
                    )}
                    aria-hidden="true"
                  />
                  <div
                    className={cn(
                      "absolute -inset-3 rounded-3xl opacity-0 transition-opacity duration-500",
                      isPlaying && "opacity-100 animate-pulse",
                    )}
                    style={{
                      background:
                        "radial-gradient(ellipse, oklch(0.65 0.12 220 / 0.35) 0%, transparent 70%)",
                    }}
                    aria-hidden="true"
                  />
                  <img
                    src="/logo.png"
                    alt="KSP Logo"
                    className={cn(
                      "relative h-24 w-24 object-contain rounded-2xl shadow-xl border-2 transition-all duration-500",
                      isPlaying
                        ? "border-primary/60 scale-105 shadow-primary/25"
                        : "border-border/60 scale-100",
                    )}
                  />
                </div>

                <p className="text-base font-bold text-foreground tracking-tight">
                  KSP Crime Intelligence Assistant
                </p>
                <p className="text-xs mt-1.5 text-muted-foreground max-w-sm">
                  Ask a question to query police databases, analyze suspect networks, or view crime trends.
                </p>

                {/* Intro greeting bubble — appears after 800 ms */}
                {introShown && introText && (
                  <div
                    className="mt-6 max-w-md w-full text-left"
                    style={{ animation: "intro-badge-in 0.5s ease both" }}
                  >
                    <div
                      className={cn(
                        "rounded-xl px-5 py-4 text-sm leading-relaxed border shadow-sm transition-all duration-500",
                        isPlaying
                          ? "bg-primary/8 border-primary/30 shadow-primary/10"
                          : "bg-card/80 border-border/60 backdrop-blur-sm",
                      )}
                    >
                      {/* Speaking header */}
                      <div className="flex items-center gap-2 mb-2.5">
                        <div
                          className={cn(
                            "h-7 w-7 rounded-full flex items-center justify-center shrink-0 transition-all",
                            isPlaying
                              ? "bg-primary text-primary-foreground ring-4 ring-primary/20"
                              : "bg-primary/10 text-primary",
                          )}
                        >
                          {isPlaying ? (
                            <SpeakingWaveform active={true} className="text-primary-foreground" />
                          ) : (
                            <Bot className="h-3.5 w-3.5" />
                          )}
                        </div>
                        <div>
                          <div className="text-xs font-semibold text-foreground">SCRB Assistant</div>
                          {isPlaying && (
                            <div className="text-[10px] text-primary font-medium">Speaking introduction…</div>
                          )}
                        </div>
                        {/* Stop / Replay intro button */}
                        {isPlaying || isPaused ? (
                          <button
                            onClick={() => stop()}
                            className="ml-auto h-6 w-6 rounded-full flex items-center justify-center text-primary hover:text-destructive hover:bg-destructive/10 transition-colors"
                            aria-label="Stop introduction speech"
                            title="Stop speaking"
                          >
                            <VolumeX className="h-3 w-3" />
                          </button>
                        ) : (
                          <button
                            onClick={() => speak(introText)}
                            className="ml-auto h-6 w-6 rounded-full flex items-center justify-center text-muted-foreground hover:text-primary hover:bg-primary/10 transition-colors"
                            aria-label="Replay introduction"
                            title="Replay introduction"
                          >
                            <RotateCcw className="h-3 w-3" />
                          </button>
                        )}
                      </div>
                      <p className="text-foreground/90 whitespace-pre-wrap">{introText}</p>
                    </div>
                  </div>
                )}

                <p className="text-[10px] mt-5 text-muted-foreground/50">
                  Press{" "}
                  <kbd className="rounded bg-muted px-1 py-0.5 font-mono">Ctrl+M</kbd>{" "}
                  for voice input
                </p>
              </div>
            )}

            {messages.map((m) => (
              <MessageRow
                key={m.id}
                m={m}
                onSpeak={(text) => handleSpeak(text, m.id)}
                isSpeaking={speakingMsgId === m.id}
              />
            ))}

            {/* Typing animation */}
            {loading && (
              <div
                className="flex items-center gap-2.5 text-sm text-muted-foreground"
                role="status"
                aria-label="Assistant is thinking"
              >
                <div className="h-8 w-8 rounded flex items-center justify-center bg-primary/10 text-primary shrink-0">
                  <Bot className="h-4 w-4" aria-hidden="true" />
                </div>
                <div className="rounded-md px-4 py-3 bg-card border-l-2 border-l-primary border border-border shadow-xs">
                  <div className="flex items-center gap-2">
                    <TypingDots />
                    <span className="text-xs text-muted-foreground">{t("analysing")}</span>
                  </div>
                </div>
              </div>
            )}

            {chatError && (
              <div
                className="flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive"
                role="alert"
              >
                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" aria-hidden="true" />
                <div>
                  <div className="font-medium">Query failed</div>
                  <div className="text-xs mt-0.5 text-destructive/80">{chatError}</div>
                </div>
              </div>
            )}
          </div>

          {/* ── Input Bar ────────────────────────────────────────────────────── */}
          <div className="border-t border-border bg-card px-3 sm:px-5 py-3">
            {contextEntity && (
              <div className="mb-2 flex items-center gap-2">
                <div className="inline-flex items-center gap-1.5 rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs text-primary">
                  <span className="font-medium">Context:</span>
                  <span>{contextEntity}</span>
                  <button
                    onClick={() => setContextEntity(null)}
                    className="ml-1 rounded-full hover:bg-primary/20 p-0.5"
                    aria-label="Clear context entity"
                  >
                    <X className="h-3 w-3" aria-hidden="true" />
                  </button>
                </div>
                <span className="text-[11px] text-muted-foreground">Click × to clear</span>
              </div>
            )}

            {/* Suggestion chips */}
            <div className="flex flex-wrap gap-1.5 mb-2.5" role="list" aria-label="Suggested queries">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  role="listitem"
                  onClick={() => send(s)}
                  className="text-xs rounded-full border border-border bg-background px-3 py-1 hover:border-primary hover:text-primary transition-colors"
                  aria-label={`Suggested query: ${s}`}
                >
                  {s}
                </button>
              ))}
            </div>

            {/* Input row */}
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
                  className="w-full resize-none rounded-md border border-input bg-background px-3 py-2 pr-28 text-sm focus:outline-none focus:ring-2 focus:ring-ring/40"
                  aria-label="Type your message. Press Enter to send, Shift+Enter for new line."
                  aria-multiline="true"
                  id="chat-input"
                />

                {/* Inline controls inside textarea */}
                <div className="absolute right-2 bottom-2 flex items-center gap-1">
                  {/* Mic button */}
                  <UITooltip>
                    <TooltipTrigger asChild>
                      <button
                        onClick={() => {
                          if (!speechSupported) return;
                          if (listening) {
                            stopListening();
                          } else {
                            startListening();
                          }
                        }}
                        disabled={!speechSupported}
                        className={cn(
                          "h-8 w-8 rounded flex items-center justify-center hover:bg-accent relative transition-all focus-visible:ring-2 focus-visible:ring-ring",
                          !speechSupported && "opacity-40 cursor-not-allowed",
                          listening && "bg-destructive/20 text-destructive scale-105",
                        )}
                        aria-label={
                          !speechSupported
                            ? t("voiceUnsupported")
                            : listening
                              ? "Stop voice recording (Ctrl+M)"
                              : "Start voice recording (Ctrl+M)"
                        }
                        aria-pressed={listening}
                        title={listening ? "Stop listening (Esc)" : "Start voice input (Ctrl+M)"}
                      >
                        {listening ? (
                          <MicOff className="h-4 w-4" aria-hidden="true" />
                        ) : (
                          <Mic className={cn("h-4 w-4", !speechSupported && "opacity-60")} aria-hidden="true" />
                        )}
                        {listening && (
                          <>
                            <span className="absolute inset-0 rounded bg-destructive/30 animate-ping" aria-hidden="true" />
                            <span className="absolute -top-0.5 -right-0.5 h-2 w-2 rounded-full bg-destructive ring-2 ring-card animate-bounce" aria-hidden="true" />
                          </>
                        )}
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="top" className="text-xs">
                      {speechSupported
                        ? listening
                          ? "Stop listening (Esc)"
                          : "Voice input (Ctrl+M)"
                        : t("voiceUnsupported")}
                    </TooltipContent>
                  </UITooltip>

                  {/* Speaker button — quick speak last response */}
                  <UITooltip>
                    <TooltipTrigger asChild>
                      <button
                        onClick={() => {
                          if (isPlaying || isPaused) {
                            stop();
                          } else {
                            const last = [...messages].reverse().find((m) => m.role === "assistant");
                            if (last) handleSpeak(last.text, last.id);
                          }
                        }}
                        disabled={messages.filter((m) => m.role === "assistant").length === 0}
                        className={cn(
                          "h-8 w-8 rounded flex items-center justify-center hover:bg-accent transition-all focus-visible:ring-2 focus-visible:ring-ring",
                          (isPlaying || isPaused) && "bg-primary/10 text-primary",
                          messages.filter((m) => m.role === "assistant").length === 0 && "opacity-30 cursor-not-allowed",
                        )}
                        aria-label={isPlaying || isPaused ? "Stop speaking (Esc)" : "Speak last response"}
                        aria-pressed={isPlaying || isPaused}
                      >
                        {isPlaying && !isPaused ? (
                          <SpeakingWaveform active={true} className="text-primary" />
                        ) : (
                          <Volume2 className="h-4 w-4" aria-hidden="true" />
                        )}
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="top" className="text-xs">
                      {isPlaying || isPaused ? "Stop speaking (Esc)" : "Speak last response"}
                    </TooltipContent>
                  </UITooltip>

                  {/* Recognition language tag */}
                  <UITooltip>
                    <TooltipTrigger asChild>
                      <span
                        className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground uppercase tracking-wider font-mono cursor-default select-none"
                        aria-label={`Voice recognition language: ${recognitionLanguage}`}
                      >
                        {recognitionLanguage.split("-")[0]}
                      </span>
                    </TooltipTrigger>
                    <TooltipContent side="top" className="text-xs">
                      Mic language: {recognitionLanguage}
                    </TooltipContent>
                  </UITooltip>
                </div>
              </div>

              {/* Send button */}
              <Button
                onClick={() => send(input)}
                disabled={loading || !input.trim()}
                className="h-11 px-4 shrink-0"
                aria-label="Send message (Enter)"
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                ) : (
                  <>
                    <Send className="h-4 w-4 mr-1.5" aria-hidden="true" />
                    {t("send")}
                  </>
                )}
              </Button>
            </div>

          </div>
        </div>

        {/* ── History Sidebar ──────────────────────────────────────────────── */}
        {historyOpen && (
          <aside
            id="history-panel"
            className="w-64 sm:w-72 border-l border-border bg-card overflow-y-auto scrollbar-thin animate-in slide-in-from-right duration-200 shrink-0"
            aria-label="Conversation history"
          >
            <div className="px-4 py-3 border-b border-border flex items-center justify-between sticky top-0 bg-card z-10">
              <div className="text-xs uppercase tracking-wider text-muted-foreground font-medium">
                {t("historyTitle")}
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                onClick={() => setHistoryOpen(false)}
                aria-label="Close history panel"
              >
                <X className="h-3.5 w-3.5" aria-hidden="true" />
              </Button>
            </div>

            {conversationsLoading ? (
              <div className="p-3 space-y-2">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} className="h-14 rounded" />
                ))}
              </div>
            ) : !conversations || conversations.length === 0 ? (
              <div className="px-4 py-8 text-center text-xs text-muted-foreground">
                No past conversations yet.
              </div>
            ) : (
              <ul className="p-2 space-y-1" role="list" aria-label="Past conversations">
                {conversations.map((s) => (
                  <li key={s.conversation_id} role="listitem">
                    <div
                      className={cn(
                        "w-full text-left rounded px-3 py-2 hover:bg-accent group flex items-start gap-2 cursor-pointer",
                        conversationId === s.conversation_id && "bg-accent",
                      )}
                      onClick={() => {
                        setConversationId(s.conversation_id);
                        setMessages([]);
                        setChatError(null);
                        if (s.preferred_language) {
                          setLanguage(s.preferred_language as any);
                        }
                        if (s.conversation_history?.length > 0) {
                          const hydratedMessages: ChatMessage[] = s.conversation_history.map(
                            (h, i) => ({
                              id: `${s.conversation_id}-${i}`,
                              role: h.role,
                              text: h.content,
                              ts: new Date(h.timestamp * 1000).toISOString(),
                              sql: h.generated_sql ?? undefined,
                            }),
                          );
                          setMessages(hydratedMessages);
                        }
                      }}
                      role="button"
                      tabIndex={0}
                      aria-label={`Load conversation: ${s.last_question?.slice(0, 40) || s.conversation_id.slice(0, 16)}`}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.currentTarget.click();
                        }
                      }}
                    >
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium truncate">
                          {s.last_question
                            ? s.last_question.slice(0, 40) + (s.last_question.length > 40 ? "…" : "")
                            : s.conversation_id.slice(0, 16) + "…"}
                        </div>
                        <div className="text-[11px] text-muted-foreground">
                          {format(new Date(s.updated_at * 1000), "d MMM · HH:mm")}
                        </div>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteMutation.mutate(s.conversation_id);
                        }}
                        className="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded hover:bg-destructive/10 hover:text-destructive focus-visible:opacity-100"
                        aria-label={`Delete conversation`}
                      >
                        <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </aside>
        )}
      </div>
    </TooltipProvider>
  );
}

// ─── MessageRow ──────────────────────────────────────────────────────────────
function MessageRow({
  m,
  onSpeak,
  isSpeaking,
}: {
  m: ChatMessage;
  onSpeak?: (text: string) => void;
  isSpeaking?: boolean;
}) {
  const t = useT();
 const [showSql, setShowSql] = useState(false);
  const isUser = m.role === "user";

  return (
    <article
      className={cn("flex gap-3 animate-in fade-in duration-300", isUser && "justify-end")}
      aria-label={`${isUser ? "Your" : "Assistant"} message`}
    >
      {!isUser && (
        <div
          className={cn(
            "h-8 w-8 rounded flex items-center justify-center bg-primary/10 text-primary shrink-0 transition-all",
            isSpeaking && "ring-2 ring-primary/40 ring-offset-1",
          )}
          aria-hidden="true"
        >
          {isSpeaking ? (
            <SpeakingWaveform active={true} className="text-primary" />
          ) : (
            <Bot className="h-4 w-4" />
          )}
        </div>
      )}

      <div className={cn("max-w-[85%] sm:max-w-[80%] min-w-0", isUser && "order-1")}>
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

        {/* Message metadata row */}
        <div
          className={cn(
            "flex items-center gap-2 mt-1.5 text-[11px] text-muted-foreground flex-wrap",
            isUser && "justify-end",
          )}
        >
          <span aria-label={`Sent at ${format(new Date(m.ts), "d MMM, HH:mm")}`}>
            {format(new Date(m.ts), "d MMM · HH:mm")}
          </span>

          {/* Message status */}
          <MessageStatus role={m.role} speaking={isSpeaking} />

          {!isUser && (m.sql || m.explain) && (
            <button
              onClick={() => setShowSql((v) => !v)}
              className="inline-flex items-center gap-0.5 hover:text-foreground focus-visible:ring-1 focus-visible:ring-ring rounded"
              aria-label={showSql ? "Hide SQL reasoning" : "Show SQL reasoning"}
              aria-expanded={showSql}
            >
              {showSql ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
              Explain Analysis · {m.rows ?? 0} row{m.rows === 1 ? "" : "s"}
            </button>
          )}

          {!isUser && onSpeak && (
            <TooltipProvider delayDuration={200}>
              <UITooltip>
                <TooltipTrigger asChild>
                  <button
                    onClick={() => onSpeak(m.text)}
                    className={cn(
                      "inline-flex items-center gap-1 hover:text-foreground ml-1 cursor-pointer focus-visible:ring-1 focus-visible:ring-ring rounded transition-colors",
                      isSpeaking && "text-primary",
                    )}
                    aria-label={isSpeaking ? "Currently speaking this message" : "Speak this response"}
                    aria-pressed={isSpeaking}
                  >
                    {isSpeaking ? (
                      <SpeakingWaveform active={true} className="text-primary" />
                    ) : (
                      <Volume2 className="h-3.5 w-3.5" />
                    )}
                    {isSpeaking ? "Speaking" : "Speak"}
                  </button>
                </TooltipTrigger>
                <TooltipContent side="top" className="text-xs">
                  {isSpeaking ? "Currently speaking" : "Read response aloud"}
                </TooltipContent>
              </UITooltip>
            </TooltipProvider>
          )}
        </div>

        {!isUser && showSql && (m.sql || m.explain) && (
          <div className="mt-3 p-4 rounded-xl border border-border/80 bg-muted/40 text-xs space-y-3">
            <h4 className="font-semibold text-foreground flex items-center gap-1.5 border-b border-border/60 pb-1.5">
              <Sparkles className="h-3.5 w-3.5 text-primary animate-pulse" />
              AI Reasoning & Execution Plan
            </h4>
            
            {m.explain ? (
              <div className="space-y-2">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider block">Data Sources</span>
                    <span className="text-foreground">{m.explain.sources || "N/A"}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider block">Algorithms Used</span>
                    <span className="text-foreground">{m.explain.algorithms || "N/A"}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider block">Confidence Score</span>
                    <Badge 
                      className={cn(
                        "mt-0.5 text-[10px] font-bold py-0.5 px-2",
                        (m.explain.confidence ?? 0) >= 85 ? "bg-green-500/10 text-green-500 border-green-500/20" :
                        (m.explain.confidence ?? 0) >= 65 ? "bg-amber-500/10 text-amber-500 border-amber-500/20" :
                        "bg-red-500/10 text-red-500 border-red-500/20"
                      )}
                      variant="outline"
                    >
                      {m.explain.confidence ?? 0}%
                    </Badge>
                  </div>
                  <div>
                    <span className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider block">Execution Time</span>
                    <span className="text-foreground font-mono">{m.explain.execution_time || "N/A"}</span>
                  </div>
                </div>
                
                {m.explain.sql && (
                  <div className="pt-2">
                    <span className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider block mb-1">Generated SQL Query</span>
                    <pre className="p-3 bg-muted/85 rounded border border-border/50 text-[10px] font-mono overflow-x-auto text-sky-400">
                      {m.explain.sql}
                    </pre>
                  </div>
                )}
              </div>
            ) : (
              <pre className="p-3 bg-muted/85 rounded border border-border/50 text-[10px] font-mono overflow-x-auto text-sky-400">
                {m.sql}
              </pre>
            )}
          </div>
        )}
      </div>

      {isUser && (
        <div
          className="h-8 w-8 rounded bg-muted flex items-center justify-center shrink-0"
          aria-hidden="true"
        >
          <UserIcon className="h-4 w-4 text-muted-foreground" />
        </div>
      )}
    </article>
  );
}

// ─── RichCard ────────────────────────────────────────────────────────────────
function RichCard({ data }: { data: RichData }) {
  if (data.kind === "stat") {
    const up = (data.delta ?? 0) >= 0;
    return (
      <div className="rounded border border-border bg-background p-3 text-foreground">
        <div className="text-[11px] uppercase tracking-wider text-muted-foreground">
          {data.title}
        </div>
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
          <table className="w-full text-xs" aria-label={data.title}>
            <thead>
              <tr className="bg-muted/50">
                {data.columns?.map((c) => (
                  <th key={c} className="text-left px-3 py-2 font-medium" scope="col">
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
      <div className="h-40" aria-label={`Chart: ${data.title}`}>
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
