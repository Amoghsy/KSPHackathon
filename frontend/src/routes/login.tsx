import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { Loader2, AlertCircle } from "lucide-react";
import { useState, useEffect } from "react";
import { useAuthStore, type Role } from "@/stores/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import { ROLE_DEFAULT_LANDING } from "@/lib/rbac";

export const Route = createFileRoute("/login")({
  head: () => ({
    meta: [{ title: " KSP Crime Intelligence Assistant" }],
  }),
  component: LoginPage,
});


// Canonical role identifiers and their human-readable display labels for the login form
const ROLES: { value: Role; label: string }[] = [
  { value: "INVESTIGATOR", label: "Investigator" },
  { value: "SENIOR_INVESTIGATOR", label: "Senior Investigator" },
  { value: "ANALYST", label: "Analyst" },
  { value: "SUPERVISOR", label: "Supervisor" },
  { value: "POLICY_MAKER", label: "Policy Maker" },
];

function LoginPage() {
  const login = useAuthStore((s) => s.login);
  const isLoading = useAuthStore((s) => s.isLoading);
  const authError = useAuthStore((s) => s.error);
  const clearError = useAuthStore((s) => s.clearError);
  const user = useAuthStore((s) => s.user);
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<Role>("INVESTIGATOR");

  useEffect(() => {
    if (user) navigate({ to: "/" });
  }, [user, navigate]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    clearError();
    try {
      await login({ username, password, role });
      toast.success("Signed in successfully");
      // Navigate to role-appropriate landing page
      const landing = ROLE_DEFAULT_LANDING[role] ?? "/";
      navigate({ to: landing as string });
    } catch {
      // error is already set in the store; toast for visibility
      toast.error("Sign in failed", {
        description: authError ?? "Check your credentials and try again.",
      });
    }
  }

  return (
    <div
      className="relative min-h-screen w-full flex flex-col text-slate-100 overflow-hidden"
      style={{
        background:
          "radial-gradient(1000px 700px at 15% 10%, oklch(0.4 0.1 220 / 0.9), transparent 60%), radial-gradient(900px 600px at 90% 90%, oklch(0.45 0.1 190 / 0.7), transparent 60%), linear-gradient(180deg, oklch(0.22 0.06 262), oklch(0.14 0.04 262))",
      }}
    >
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.07]"
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
              className="h-20 w-20 rounded-2xl flex items-center justify-center overflow-hidden"
              style={{
                boxShadow:
                  "0 12px 40px -8px oklch(0.65 0.12 190 / 0.4), inset 0 1px 0 oklch(1 0 0 / 0.1)",
              }}
            >
              <img src="/logo.png" alt="KSP Logo" className="h-full w-full object-cover" />
            </div>
            <div className="mt-5 text-[11px] uppercase tracking-[0.24em] text-slate-300 font-medium">
              Karnataka State Police · SCRB
            </div>
            <h1 className="mt-1.5 text-2xl sm:text-3xl font-semibold tracking-tight">
              Crime Intelligence Assistant
            </h1>
            <p className="mt-2 text-sm text-slate-300">
              Authorised personnel only. All actions are audited.
            </p>
          </div>

          <form
            onSubmit={handleSubmit}
            className="rounded-2xl text-card-foreground p-6 space-y-4 glass-strong"
          >
            {authError && (
              <div className="flex items-start gap-2 rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                <span>{authError}</span>
              </div>
            )}

            <div className="space-y-1.5">
              <Label htmlFor="u">Username / Badge No.</Label>
              <Input
                id="u"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="username"
                autoComplete="username"
                disabled={isLoading}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="p">Password</Label>
              <Input
                id="p"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                autoComplete="current-password"
                disabled={isLoading}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="r">Role</Label>
              <Select value={role} onValueChange={(v) => setRole(v as Role)} disabled={isLoading}>
                <SelectTrigger id="r">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {ROLES.map((r) => (
                    <SelectItem key={r.value} value={r.value}>
                      {r.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button type="submit" className="w-full" disabled={isLoading || !username.trim()}>
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Signing in…
                </>
              ) : (
                "Sign In"
              )}
            </Button>
          </form>
        </div>
      </div>
      <footer className="border-t border-white/10 py-3 text-center text-[11px] text-slate-400">
        Confidential Government System — Unauthorised access is a punishable offence under IT Act,
        2000.
      </footer>
    </div>
  );
}
