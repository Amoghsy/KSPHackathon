import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { Loader2, AlertCircle, ShieldAlert, Lock } from "lucide-react";
import { useState, useEffect } from "react";
import { useAuthStore } from "@/stores/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

export const Route = createFileRoute("/admin-login")({
  head: () => ({
    meta: [{ title: "Administrator Gateway — Crime Intelligence Assistant" }],
  }),
  component: AdminLoginPage,
});

function AdminLoginPage() {
  const login = useAuthStore((s) => s.login);
  const isLoading = useAuthStore((s) => s.isLoading);
  const authError = useAuthStore((s) => s.error);
  const clearError = useAuthStore((s) => s.clearError);
  const user = useAuthStore((s) => s.user);
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  useEffect(() => {
    if (user && user.role === "Admin") {
      navigate({ to: "/admin" });
    }
  }, [user, navigate]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    clearError();
    try {
      await login({ username, password, role: "Admin" });
      toast.success("Administrator session verified");
      navigate({ to: "/admin" });
    } catch {
      toast.error("Authentication failed", {
        description: authError ?? "Invalid administrator credentials.",
      });
    }
  }

  return (
    <div
      className="relative min-h-screen w-full flex flex-col text-slate-100 overflow-hidden"
      style={{
        background:
          "radial-gradient(1000px 700px at 15% 10%, oklch(0.35 0.1 360 / 0.9), transparent 60%), radial-gradient(900px 600px at 90% 90%, oklch(0.4 0.08 240 / 0.7), transparent 60%), linear-gradient(180deg, oklch(0.18 0.04 262), oklch(0.1 0.02 262))",
      }}
    >
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.06]"
        style={{
          backgroundImage:
            "linear-gradient(oklch(1 0 0 / 0.4) 1px, transparent 1px), linear-gradient(90deg, oklch(1 0 0 / 0.4) 1px, transparent 1px)",
          backgroundSize: "48px 48px",
        }}
      />
      <div className="flex-1 flex items-center justify-center px-4 py-10 relative">
        <div className="w-full max-w-md">
          <div className="flex flex-col items-center text-center mb-8">
            <div
              className="h-20 w-20 rounded-2xl flex items-center justify-center bg-destructive/10 border border-destructive/30 overflow-hidden"
              style={{
                boxShadow:
                  "0 12px 40px -8px oklch(0.55 0.15 360 / 0.4), inset 0 1px 0 oklch(1 0 0 / 0.1)",
              }}
            >
              <ShieldAlert className="h-10 w-10 text-destructive animate-pulse" />
            </div>
            <div className="mt-5 text-[11px] uppercase tracking-[0.24em] text-destructive font-semibold">
              SECURE ADMIN GATEWAY
            </div>
            <h1 className="mt-1.5 text-2xl sm:text-3xl font-semibold tracking-tight text-white">
              SCRB Intelligence Console
            </h1>
            <p className="mt-2 text-sm text-slate-300">
              Administrative credentials required. Active monitoring enabled.
            </p>
          </div>

          <form
            onSubmit={handleSubmit}
            className="rounded-2xl text-card-foreground p-6 space-y-4 glass-strong"
            style={{
              border: "1px solid rgba(239, 68, 68, 0.15)"
            }}
          >
            {authError && (
              <div className="flex items-start gap-2 rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                <span>{authError}</span>
              </div>
            )}

            <div className="space-y-1.5">
              <Label htmlFor="u">Admin Username</Label>
              <Input
                id="u"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="administrator"
                autoComplete="username"
                disabled={isLoading}
                className="bg-background/40 border-border/80 focus-visible:border-destructive/60"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="p">Security Key / Password</Label>
              <Input
                id="p"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                autoComplete="current-password"
                disabled={isLoading}
                className="bg-background/40 border-border/80 focus-visible:border-destructive/60"
              />
            </div>

            <Button 
              type="submit" 
              className="w-full bg-destructive hover:bg-destructive/90 text-destructive-foreground mt-2" 
              disabled={isLoading || !username.trim()}
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Verifying Gateway…
                </>
              ) : (
                <>
                  <Lock className="h-4 w-4 mr-2" />
                  Authenticate
                </>
              )}
            </Button>
          </form>
        </div>
      </div>
      <footer className="border-t border-white/10 py-3 text-center text-[11px] text-slate-400">
        CONFIDENTIAL SECURITY SYSTEMS — INCIDENTS LOGGED TO AUDIT LOGS.
      </footer>
    </div>
  );
}
