import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { Loader2, AlertCircle, ShieldCheck, KeyRound } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { apiPost } from "@/lib/api/axios";

interface SearchParams {
  token?: string;
}

export const Route = createFileRoute("/setup-password")({
  validateSearch: (search: Record<string, unknown>): SearchParams => {
    return {
      token: search.token as string | undefined,
    };
  },
  head: () => ({
    meta: [{ title: "Setup Password — Crime Intelligence Assistant" }],
  }),
  component: SetupPasswordPage,
});

function SetupPasswordPage() {
  const { token } = Route.useSearch();
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (!token) {
      setError("Activation token is missing. Please check your email link.");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setIsLoading(true);
    try {
      await apiPost("/users/activate", {
        token: token,
        password: password,
      });
      toast.success("Account activated successfully! Please sign in.");
      navigate({ to: "/login" });
    } catch (err: any) {
      const msg = err?.response?.data?.detail ?? "Failed to activate account. The link may have expired.";
      setError(msg);
    } finally {
      setIsLoading(false);
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
              Activate Account
            </h1>
            <p className="mt-2 text-sm text-slate-300">
              Set up your secure password to complete your account provisioning.
            </p>
          </div>

          <form
            onSubmit={handleSubmit}
            className="rounded-2xl text-card-foreground p-6 space-y-4 glass-strong"
          >
            {error && (
              <div className="flex items-start gap-2 rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            {!token ? (
              <div className="text-center py-4 space-y-2">
                <AlertCircle className="h-10 w-10 text-destructive mx-auto" />
                <h3 className="text-sm font-semibold">Invalid Activation Link</h3>
                <p className="text-xs text-slate-400">
                  This activation link is missing its security token or has expired. Please contact your administrator.
                </p>
                <Button onClick={() => navigate({ to: "/login" })} className="w-full mt-4" variant="outline">
                  Go to Login
                </Button>
              </div>
            ) : (
              <>
                <div className="space-y-1.5">
                  <Label htmlFor="p">New Password</Label>
                  <Input
                    id="p"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    autoComplete="new-password"
                    disabled={isLoading}
                  />
                  <p className="text-[10px] text-slate-400">
                    Must be at least 8 characters long and contain numbers/special characters.
                  </p>
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="cp">Confirm Password</Label>
                  <Input
                    id="cp"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="••••••••"
                    autoComplete="new-password"
                    disabled={isLoading}
                  />
                </div>

                <Button
                  type="submit"
                  className="w-full"
                  disabled={isLoading || !password || !confirmPassword}
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Activating…
                    </>
                  ) : (
                    <>
                      <KeyRound className="h-4 w-4 mr-2" />
                      Set Password & Activate
                    </>
                  )}
                </Button>
              </>
            )}
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
