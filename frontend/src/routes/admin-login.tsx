import { createFileRoute, useNavigate } from "@tanstack/react-router";
import {
  Loader2,
  AlertCircle,
  ShieldAlert,
  Lock,
  Mail,
  ShieldCheck,
  ArrowLeft,
  RefreshCw,
} from "lucide-react";
import { useState, useEffect, useRef } from "react";
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

// OTP Input Component for Admin
interface OTPInputProps {
  value: string;
  onChange: (v: string) => void;
  disabled?: boolean;
  length?: number;
}

function OTPInput({ value, onChange, disabled, length = 6 }: OTPInputProps) {
  const inputs = useRef<(HTMLInputElement | null)[]>([]);

  function handleChange(idx: number, e: React.ChangeEvent<HTMLInputElement>) {
    const char = e.target.value.replace(/\D/g, "").slice(-1);
    const chars = value.split("");
    chars[idx] = char;
    const next = chars.join("").slice(0, length);
    onChange(next);
    if (char && idx < length - 1) {
      inputs.current[idx + 1]?.focus();
    }
  }

  function handleKeyDown(idx: number, e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Backspace" && !value[idx] && idx > 0) {
      inputs.current[idx - 1]?.focus();
    }
    if (e.key === "ArrowLeft" && idx > 0) inputs.current[idx - 1]?.focus();
    if (e.key === "ArrowRight" && idx < length - 1) inputs.current[idx + 1]?.focus();
  }

  function handlePaste(e: React.ClipboardEvent) {
    const text = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, length);
    onChange(text);
    const focusIdx = Math.min(text.length, length - 1);
    inputs.current[focusIdx]?.focus();
    e.preventDefault();
  }

  return (
    <div className="flex gap-3 justify-center" onPaste={handlePaste}>
      {Array.from({ length }).map((_, i) => (
        <input
          key={i}
          ref={(el) => { inputs.current[i] = el; }}
          type="text"
          inputMode="numeric"
          maxLength={1}
          value={value[i] ?? ""}
          onChange={(e) => handleChange(i, e)}
          onKeyDown={(e) => handleKeyDown(i, e)}
          disabled={disabled}
          className="
            h-14 w-12 rounded-xl border border-red-500/30 bg-white/5 text-center text-xl font-bold
            text-white placeholder-white/20 outline-none transition-all duration-200
            focus:border-red-400/60 focus:bg-white/10 focus:ring-2 focus:ring-red-400/20
            disabled:opacity-40 disabled:cursor-not-allowed
          "
          aria-label={`OTP digit ${i + 1}`}
        />
      ))}
    </div>
  );
}

function useCountdown(seconds: number, running: boolean) {
  const [remaining, setRemaining] = useState(seconds);

  useEffect(() => {
    setRemaining(seconds);
  }, [seconds]);

  useEffect(() => {
    if (!running || remaining <= 0) return;
    const t = setInterval(() => setRemaining((r) => Math.max(0, r - 1)), 1000);
    return () => clearInterval(t);
  }, [running, remaining]);

  return remaining;
}

// ─── Animated Admin Background ─────────────────────────────────────────────

function AdminLoginBackground() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden select-none">
      {/* Base animated moving background color gradient */}
      <div className="admin-animated-bg absolute inset-0" />

      {/* Animated Glow 1: Primary Crimson (Upper-left / Left-center) */}
      <div
        className="admin-glow-1 absolute rounded-full blur-[95px] pointer-events-none"
        style={{
          width: "75vw",
          height: "75vw",
          maxWidth: "950px",
          maxHeight: "950px",
          top: "-20%",
          left: "-15%",
          background:
            "radial-gradient(circle at center, oklch(0.51 0.16 355 / 0.85), oklch(0.38 0.11 10 / 0.35) 55%, transparent 80%)",
        }}
      />

      {/* Animated Glow 2: Secondary Indigo/Navy (Right-center / Lower-right) */}
      <div
        className="admin-glow-2 absolute rounded-full blur-[100px] pointer-events-none"
        style={{
          width: "70vw",
          height: "70vw",
          maxWidth: "900px",
          maxHeight: "900px",
          top: "15%",
          right: "-15%",
          background:
            "radial-gradient(circle at center, oklch(0.48 0.13 235 / 0.80), oklch(0.35 0.09 245 / 0.30) 55%, transparent 80%)",
        }}
      />

      {/* Animated Glow 3: Deep Burgundy (Center-bottom / Ambient) */}
      <div
        className="admin-glow-3 absolute rounded-full blur-[110px] pointer-events-none"
        style={{
          width: "65vw",
          height: "65vw",
          maxWidth: "850px",
          maxHeight: "850px",
          bottom: "-20%",
          left: "20%",
          background:
            "radial-gradient(circle at center, oklch(0.43 0.13 15 / 0.70), oklch(0.30 0.07 262 / 0.25) 55%, transparent 80%)",
        }}
      />

      {/* Shimmer Light Sweep Layer */}
      <div className="admin-shimmer-sweep absolute -inset-y-1/2 w-1/3 pointer-events-none bg-gradient-to-r from-transparent via-red-400/18 to-transparent" />

      {/* Subtle grid overlay */}
      <div
        className="login-grid-drift absolute inset-0 opacity-[0.075]"
        style={{
          backgroundImage:
            "linear-gradient(oklch(1 0 0 / 0.4) 1px, transparent 1px), linear-gradient(90deg, oklch(1 0 0 / 0.4) 1px, transparent 1px)",
          backgroundSize: "48px 48px",
        }}
      />

      {/* Dark vignette & contrast protection layer for center UI - Medium balanced depth */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse at 50% 50%, transparent 25%, oklch(0.14 0.03 262 / 0.48) 70%, oklch(0.11 0.02 262 / 0.75) 100%)",
        }}
      />
    </div>
  );
}

function AdminLoginPage() {
  const initiateLogin = useAuthStore((s) => s.initiateLogin);
  const verifyOTP = useAuthStore((s) => s.verifyOTP);
  const resendOTP = useAuthStore((s) => s.resendOTP);
  const clearChallenge = useAuthStore((s) => s.clearChallenge);
  const isLoading = useAuthStore((s) => s.isLoading);
  const authError = useAuthStore((s) => s.error);
  const clearError = useAuthStore((s) => s.clearError);
  const otpChallenge = useAuthStore((s) => s.otpChallenge);
  const user = useAuthStore((s) => s.user);
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [otp, setOtp] = useState("");

  const [resendCooldown, setResendCooldown] = useState(60);
  const [resendRunning, setResendRunning] = useState(false);
  const countdown = useCountdown(resendCooldown, resendRunning);

  const isOTPStep = !!otpChallenge;

  useEffect(() => {
    if (user && user.role === "ADMINISTRATOR") {
      navigate({ to: "/admin" });
    }
  }, [user, navigate]);

  useEffect(() => {
    if (otpChallenge) {
      setResendCooldown(60);
      setResendRunning(true);
      setOtp("");
    }
  }, [otpChallenge?.challengeId]);

  useEffect(() => {
    if (countdown === 0) setResendRunning(false);
  }, [countdown]);

  async function handlePasswordSubmit(e: React.FormEvent) {
    e.preventDefault();
    clearError();
    try {
      await initiateLogin({ username: username.trim(), password });
      const currentUser = useAuthStore.getState().user;
      if (!currentUser) {
        toast.info("Verification code sent to your admin email.");
      } else {
        toast.success("Administrator session verified");
      }
    } catch {
      toast.error("Authentication failed", {
        description: authError ?? "Invalid administrator credentials.",
      });
    }
  }

  async function handleOTPSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (otp.length < 6) return;
    clearError();
    try {
      await verifyOTP(otp);
      const updatedUser = useAuthStore.getState().user;
      if (updatedUser?.role !== "ADMINISTRATOR") {
        toast.error("Access denied", {
          description: "This gateway is for administrators only.",
        });
        useAuthStore.getState().logout();
        return;
      }
      toast.success("Administrator session verified");
      navigate({ to: "/admin" });
    } catch {
      setOtp("");
      toast.error("Verification failed", {
        description: authError ?? "Invalid code. Please try again.",
      });
    }
  }

  async function handleResend() {
    if (countdown > 0) return;
    clearError();
    try {
      const { expiresIn } = await resendOTP();
      setResendCooldown(Math.min(expiresIn, 60));
      setResendRunning(true);
      toast.success("New verification code sent.");
    } catch {
      toast.error("Could not resend code. Please wait and try again.");
    }
  }

  function handleBack() {
    clearChallenge();
    setOtp("");
    setPassword("");
  }

  return (
    <div className="dark relative min-h-screen w-full flex flex-col text-slate-100 overflow-hidden">
      <AdminLoginBackground />
      <div className="flex-1 flex items-center justify-center px-4 py-10 relative z-10">
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

          <div
            className="rounded-2xl p-6 space-y-4 transition-all duration-500"
            style={{
              background: "rgba(20, 15, 30, 0.65)",
              backdropFilter: "blur(24px) saturate(160%)",
              border: "1px solid rgba(239, 68, 68, 0.2)",
              boxShadow: "0 8px 32px -8px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.06)",
            }}
          >
            {authError && (
              <div className="flex items-start gap-2 rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                <span>{authError}</span>
              </div>
            )}

            {!isOTPStep ? (
              <form onSubmit={handlePasswordSubmit} className="space-y-4">
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
                  disabled={isLoading || !username.trim() || !password.trim()}
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
            ) : (
              <form onSubmit={handleOTPSubmit} className="space-y-5">
                <div className="flex flex-col items-center gap-2 text-center py-1">
                  <div className="h-10 w-10 rounded-full bg-destructive/15 flex items-center justify-center">
                    <Mail className="h-5 w-5 text-destructive" />
                  </div>
                  <p className="text-sm text-slate-300">
                    A 6-digit verification code was sent to your email.
                  </p>
                </div>

                <OTPInput value={otp} onChange={setOtp} disabled={isLoading} />

                <Button
                  type="submit"
                  className="w-full bg-destructive hover:bg-destructive/90 text-destructive-foreground"
                  disabled={isLoading || otp.length < 6}
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Authenticating…
                    </>
                  ) : (
                    <>
                      <ShieldCheck className="h-4 w-4 mr-2" />
                      Verify Admin Session
                    </>
                  )}
                </Button>

                <div className="flex items-center justify-between pt-1">
                  <button
                    type="button"
                    onClick={handleBack}
                    className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200 transition-colors"
                  >
                    <ArrowLeft className="h-3 w-3" />
                    Back
                  </button>

                  <button
                    type="button"
                    onClick={handleResend}
                    disabled={countdown > 0 || isLoading}
                    className={`flex items-center gap-1 text-xs transition-colors ${
                      countdown > 0
                        ? "text-slate-500 cursor-not-allowed"
                        : "text-red-400 hover:text-red-300"
                    }`}
                  >
                    <RefreshCw className="h-3 w-3" />
                    {countdown > 0 ? `Resend in ${countdown}s` : "Resend code"}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      </div>
      <footer className="relative z-10 border-t border-white/10 py-3 text-center text-[11px] text-slate-400">
        CONFIDENTIAL SECURITY SYSTEMS — INCIDENTS LOGGED TO AUDIT LOGS.
      </footer>
    </div>
  );
}
