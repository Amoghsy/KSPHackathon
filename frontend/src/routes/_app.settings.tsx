import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { PageHeader } from "@/components/app/primitives";
import { useAuthStore } from "@/stores/auth";
import { usePrefs } from "@/stores/prefs";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { useState, useEffect, useCallback } from "react";
import {
  Monitor, Smartphone, Tablet,
  Wifi, WifiOff, Trash2, LogOut,
  RefreshCw, Shield, AlertTriangle
} from "lucide-react";
import { apiGet, apiDelete, apiPost } from "@/lib/api/axios";
import { useLanguage } from "../context/LanguageContext";

export const Route = createFileRoute("/_app/settings")({
  head: () => ({ meta: [{ title: "Settings — Crime Intelligence Assistant" }] }),
  component: SettingsPage,
});

// ─── Session Types ────────────────────────────────────────────────────────────

interface ActiveSession {
  session_id: string;
  device_name: string;
  browser: string;
  os: string;
  device_type: string;
  ip_address: string;
  created_at: string;
  last_activity_at: string;
  is_current: boolean;
}

// ─── Device Icon ─────────────────────────────────────────────────────────────

function DeviceIcon({ type, className }: { type: string; className?: string }) {
  const t = type?.toLowerCase() ?? "";
  if (t.includes("mobile") || t.includes("phone")) return <Smartphone className={className} />;
  if (t.includes("tablet")) return <Tablet className={className} />;
  return <Monitor className={className} />;
}

// ─── Active Sessions Panel ───────────────────────────────────────────────────

function formatSessionDate(dateStr: string): string {
  if (!dateStr) return "Unknown";
  let cleaned = dateStr;
  if (dateStr.endsWith("Z") && (dateStr.includes("+") || dateStr.lastIndexOf("-") > 10)) {
    cleaned = dateStr.slice(0, -1);
  }
  const d = new Date(cleaned);
  if (isNaN(d.getTime())) {
    return dateStr;
  }
  return d.toLocaleString();
}

function ActiveSessionsPanel() {
  const [sessions, setSessions] = useState<ActiveSession[]>([]);
  const [loading, setLoading] = useState(false);
  const [revoking, setRevoking] = useState<string | null>(null);
  const logout = useAuthStore((s) => s.logout);
  const user = useAuthStore((s) => s.user);
  const navigate = useNavigate();

  const fetchSessions = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiGet<ActiveSession[]>("/auth/sessions");
      setSessions(data);
    } catch {
      toast.error("Could not load active sessions.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchSessions(); }, [fetchSessions]);

  async function handleRevoke(sessionId: string, isCurrent: boolean) {
    setRevoking(sessionId);
    try {
      await apiDelete(`/auth/sessions/${sessionId}`);
      if (isCurrent) {
        toast.success("Current session terminated.");
        await logout();
        const isAdmin = user?.role === "ADMINISTRATOR";
        navigate({ to: isAdmin ? "/admin-login" : "/login" });
      } else {
        toast.success("Session terminated successfully.");
        setSessions((prev) => prev.filter((s) => s.session_id !== sessionId));
      }
    } catch {
      toast.error("Could not revoke session. Please try again.");
    } finally {
      setRevoking(null);
    }
  }

  async function handleRevokeOthers() {
    setLoading(true);
    try {
      await apiPost("/auth/sessions/logout-others", {});
      toast.success("All other sessions terminated.");
      await fetchSessions();
    } catch {
      toast.error("Could not terminate other sessions.");
    } finally {
      setLoading(false);
    }
  }

  const otherCount = sessions.filter((s) => !s.is_current).length;

  return (
    <section className="rounded-xl glass p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold flex items-center gap-2">
            <Shield className="h-4 w-4 text-sky-400" />
            Active Sessions
          </h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            Devices currently signed in to your account.
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={fetchSessions}
            disabled={loading}
            className="h-7 px-2 text-xs"
          >
            <RefreshCw className={`h-3 w-3 mr-1 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          {otherCount > 0 && (
            <Button
              variant="destructive"
              size="sm"
              onClick={handleRevokeOthers}
              disabled={loading}
              className="h-7 px-2 text-xs"
            >
              <LogOut className="h-3 w-3 mr-1" />
              Sign out others ({otherCount})
            </Button>
          )}
        </div>
      </div>

      {loading && sessions.length === 0 ? (
        <div className="text-center py-6 text-sm text-muted-foreground">
          Loading sessions…
        </div>
      ) : sessions.length === 0 ? (
        <div className="text-center py-6 text-sm text-muted-foreground">
          No active sessions found.
        </div>
      ) : (
        <div className="space-y-2.5">
          {sessions.map((s) => (
            <div
              key={s.session_id}
              className={`flex items-center gap-3 rounded-lg p-3 transition-colors ${
                s.is_current ? "bg-sky-500/10 border border-sky-400/20" : "bg-white/5"
              }`}
            >
              <div className="flex-shrink-0 h-9 w-9 rounded-lg bg-white/5 flex items-center justify-center">
                <DeviceIcon type={s.device_type} className="h-4 w-4 text-muted-foreground" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm font-medium truncate">
                    {s.device_name || `${s.os} · ${s.browser}`}
                  </span>
                  {s.is_current && (
                    <Badge variant="default" className="text-[10px] px-1.5 py-0 h-4 bg-sky-500/20 text-sky-400 border-sky-400/30">
                      This device
                    </Badge>
                  )}
                </div>
                <div className="flex items-center gap-3 mt-0.5 flex-wrap">
                  <span className="text-[11px] text-muted-foreground">{s.browser} · {s.os}</span>
                  <span className="text-[11px] text-muted-foreground flex items-center gap-1">
                    <Wifi className="h-2.5 w-2.5" />
                    {s.ip_address}
                  </span>
                  <span className="text-[11px] text-muted-foreground">
                    Active {formatSessionDate(s.last_activity_at)}
                  </span>
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 flex-shrink-0 text-muted-foreground hover:text-destructive"
                onClick={() => handleRevoke(s.session_id, s.is_current)}
                disabled={revoking === s.session_id}
                title={s.is_current ? "Sign out this device" : "Revoke this session"}
              >
                {revoking === s.session_id ? (
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Trash2 className="h-3.5 w-3.5" />
                )}
              </Button>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

// ─── Settings Page ────────────────────────────────────────────────────────────

function SettingsPage() {
  const user = useAuthStore((s) => s.user);
  const { language, setLanguage } = useLanguage();
  const { lang, setLang, theme, toggleTheme } = usePrefs();

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <PageHeader title="Settings" subtitle="Profile, security and notification preferences." />
      <div className="space-y-6">
        {/* Profile Section */}
        <section className="rounded-xl glass p-5">
          <h2 className="text-sm font-semibold mb-4">Profile</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label>Name</Label>
              <Input readOnly value={user?.name ?? ""} />
            </div>
            <div className="space-y-1.5">
              <Label>Role</Label>
              <Input readOnly value={user?.role ?? ""} />
            </div>
            <div className="space-y-1.5">
              <Label>Badge No.</Label>
              <Input readOnly value={user?.badgeNo ?? ""} />
            </div>
            <div className="space-y-1.5">
              <Label>Station</Label>
              <Input readOnly value={user?.station ?? ""} />
            </div>
          </div>
        </section>

        {/* Security & Active Sessions */}
        <ActiveSessionsPanel />

        {/* Preferences */}
        <section className="rounded-xl glass p-5">
          <h2 className="text-sm font-semibold mb-4">Preferences</h2>
          <div className="space-y-4">
            {/* Display Language */}
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium">Display Language</div>
                <div className="text-xs text-muted-foreground">Language of the application interface, menus, and labels.</div>
              </div>
              <div className="flex rounded-md border border-input overflow-hidden text-xs">
                <button
                  onClick={() => setLang("en")}
                  className={"px-3 py-1.5 font-medium " + (lang === "en" ? "bg-primary text-primary-foreground" : "hover:bg-accent")}
                >
                  English
                </button>
                <button
                  onClick={() => setLang("kn")}
                  className={"px-3 py-1.5 font-medium " + (lang === "kn" ? "bg-primary text-primary-foreground" : "hover:bg-accent")}
                >
                  ಕನ್ನಡ
                </button>
              </div>
            </div>

            {/* Chatbot Language */}
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium">Chatbot Language</div>
                <div className="text-xs text-muted-foreground">Preferred language for query responses and spoken voice greeting.</div>
              </div>
              <div className="flex rounded-md border border-input overflow-hidden text-xs">
                <button
                  onClick={() => setLanguage("auto")}
                  className={"px-3 py-1.5 font-medium " + (language === "auto" ? "bg-primary text-primary-foreground" : "hover:bg-accent")}
                >
                  Auto Detect
                </button>
                <button
                  onClick={() => setLanguage("en")}
                  className={"px-3 py-1.5 font-medium " + (language === "en" ? "bg-primary text-primary-foreground" : "hover:bg-accent")}
                >
                  English
                </button>
                <button
                  onClick={() => setLanguage("kn")}
                  className={"px-3 py-1.5 font-medium " + (language === "kn" ? "bg-primary text-primary-foreground" : "hover:bg-accent")}
                >
                  ಕನ್ನಡ
                </button>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium">Dark mode</div>
                <div className="text-xs text-muted-foreground">Best for low-light control rooms.</div>
              </div>
              <Switch checked={theme === "dark"} onCheckedChange={toggleTheme} />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium">Critical alert notifications</div>
                <div className="text-xs text-muted-foreground">Push critical alerts to this session.</div>
              </div>
              <Switch defaultChecked />
            </div>
          </div>
        </section>

        <div className="rounded-lg border border-amber-500/25 bg-amber-500/10 p-4 flex gap-3">
          <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
          <div className="text-xs text-amber-800 dark:text-amber-200">
            <span className="font-semibold text-amber-900 dark:text-amber-400">Security notice:</span>{" "}
            Sessions automatically expire after 10 minutes of inactivity.
            All sign-in events and actions are logged and audited.
          </div>
        </div>

        <div>
          <Button
            onClick={() =>
              toast.success("Preferences saved", {
                description: "Language, theme and notification settings updated.",
              })
            }
          >
            Save changes
          </Button>
          <span className="text-xs text-muted-foreground ml-3">
            Profile changes require Supervisor approval.
          </span>
        </div>
      </div>
    </div>
  );
}
