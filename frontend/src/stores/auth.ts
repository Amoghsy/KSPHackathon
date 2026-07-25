// src/stores/auth.ts — Zustand auth store with 2FA (OTP) login support and server-side session tracking.

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { apiPost } from "@/lib/api/axios";
import { getPermissionsForRole, type Permission } from "@/lib/rbac";

export type Role =
  | "INVESTIGATOR"
  | "SENIOR_INVESTIGATOR"
  | "ANALYST"
  | "SUPERVISOR"
  | "POLICY_MAKER"
  | "ADMINISTRATOR";

export interface AuthUser {
  id: string;
  name: string;
  username: string;
  role: Role;
  permissions: Permission[];
  assignedDistricts: string[];
  assignedPoliceStations: string[];
  badgeNo: string;
  station: string;
}

export interface OTPChallenge {
  challengeId: string;
  expiresIn: number;
  /** timestamp when challenge was issued (ms) */
  issuedAt: number;
}

interface AuthState {
  user: AuthUser | null;
  token: string | null;
  refreshToken: string | null;
  sessionId: string | null;
  isLoading: boolean;
  error: string | null;
  // OTP Challenge state
  otpChallenge: OTPChallenge | null;

  /** Step 1: submit username + password → returns OTP challenge */
  initiateLogin: (credentials: { username: string; password: string }) => Promise<void>;

  /** Step 2: submit OTP → issue token + establish session */
  verifyOTP: (otp: string) => Promise<void>;

  /** Resend OTP for active challenge */
  resendOTP: () => Promise<{ expiresIn: number }>;

  /** Server-side logout */
  logout: () => Promise<void>;

  /** Clear OTP state to go back to step 1 */
  clearChallenge: () => void;

  /** Clear any error state */
  clearError: () => void;

  /** Update token (used after refresh) */
  setToken: (token: string, refreshToken?: string) => void;
}

function normalizeRole(role?: string): Role {
  if (!role) return "INVESTIGATOR";
  const r = role.toUpperCase().replace(" ", "_");
  if (r === "ADMIN" || r === "ADMINISTRATOR") return "ADMINISTRATOR";
  if (r === "POLICYMAKER" || r === "POLICY_MAKER") return "POLICY_MAKER";
  if (r === "SENIOR_INVESTIGATOR") return "SENIOR_INVESTIGATOR";
  if (r === "INVESTIGATOR") return "INVESTIGATOR";
  if (r === "ANALYST") return "ANALYST";
  if (r === "SUPERVISOR") return "SUPERVISOR";
  return "INVESTIGATOR";
}

function buildDisplayName(apiName: string, username: string, role: Role): string {
  // Prefer server-provided name
  let rawName = apiName || username;
  if (!apiName) {
    // Derive from username
    rawName = username
      .split(/[._-]/)
      .filter(Boolean)
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(" ");
  }
  // Strip any existing prefix
  const l = rawName.toLowerCase();
  if (l.startsWith("sp ")) rawName = rawName.slice(3);
  else if (l.startsWith("insp. ")) rawName = rawName.slice(6);
  else if (l.startsWith("insp ")) rawName = rawName.slice(5);
  else if (l.startsWith("dr. ")) rawName = rawName.slice(4);
  else if (l.startsWith("dysp ")) rawName = rawName.slice(5);
  else if (l.startsWith("admin ")) rawName = rawName.slice(6);

  switch (role) {
    case "SUPERVISOR":
      return `SP ${rawName}`;
    case "SENIOR_INVESTIGATOR":
      return `DySP ${rawName}`;
    case "INVESTIGATOR":
      return `Insp. ${rawName}`;
    case "POLICY_MAKER":
      return `Dr. ${rawName}`;
    case "ADMINISTRATOR":
      return `Admin ${rawName}`;
    default:
      return rawName;
  }
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      refreshToken: null,
      sessionId: null,
      isLoading: false,
      error: null,
      otpChallenge: null,

      initiateLogin: async ({ username, password }) => {
        set({ isLoading: true, error: null, otpChallenge: null });
        try {
          const resp = await apiPost<{
            otp_required: boolean;
            challenge_id?: string;
            expires_in?: number;
            message?: string;
            access_token?: string;
            token_type?: string;
            session_id?: string;
            role?: string;
            refresh_token?: string;
            user?: any;
          }>("/auth/login", { username, password });

          if (resp.otp_required === false && resp.access_token) {
            set({
              isLoading: false,
              token: resp.access_token,
              refreshToken: resp.refresh_token ?? null,
              sessionId: resp.session_id ?? null,
              user: resp.user ?? null,
              otpChallenge: null,
            });
            return;
          }

          set({
            isLoading: false,
            otpChallenge: {
              challengeId: resp.challenge_id!,
              expiresIn: resp.expires_in!,
              issuedAt: Date.now(),
            },
          });
        } catch (err: unknown) {
          const message =
            (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
            (err as { message?: string })?.message ??
            "Login failed. Check credentials.";
          set({ isLoading: false, error: message });
          throw err;
        }
      },

      verifyOTP: async (otp: string) => {
        const challenge = get().otpChallenge;
        if (!challenge) {
          set({ error: "No active OTP challenge. Please start login again." });
          throw new Error("No active OTP challenge.");
        }
        set({ isLoading: true, error: null });
        try {
          const resp = await apiPost<{
            access_token: string;
            token_type: string;
            session_id: string;
            username: string;
            role: string;
            refresh_token: string;
            user: {
              id: string;
              name: string;
              username: string;
              role: string;
              badgeNo: string;
              station: string;
            };
          }>("/auth/verify-otp", { challenge_id: challenge.challengeId, otp });

          const role = normalizeRole(resp.role);
          const displayName = buildDisplayName(resp.user?.name ?? "", resp.username, role);

          set({
            isLoading: false,
            otpChallenge: null,
            token: resp.access_token,
            refreshToken: resp.refresh_token,
            sessionId: resp.session_id,
            user: {
              id: resp.user?.id ?? String(Date.now()),
              name: displayName,
              username: resp.username,
              role,
              permissions: getPermissionsForRole(role),
              assignedDistricts: (resp.user as any)?.assignedDistricts ?? [],
              assignedPoliceStations: (resp.user as any)?.assignedPoliceStations ?? [],
              badgeNo: resp.user?.badgeNo ?? `KSP-10001`,
              station: resp.user?.station ?? "SCRB HQ, Bengaluru",
            },
          });
        } catch (err: unknown) {
          const message =
            (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
            (err as { message?: string })?.message ??
            "Invalid verification code.";
          set({ isLoading: false, error: message });
          throw err;
        }
      },

      resendOTP: async () => {
        const challenge = get().otpChallenge;
        if (!challenge) throw new Error("No active challenge.");
        set({ isLoading: true, error: null });
        try {
          const resp = await apiPost<{ status: string; expires_in: number; message: string }>(
            "/auth/resend-otp",
            { challenge_id: challenge.challengeId }
          );
          set({
            isLoading: false,
            otpChallenge: {
              ...challenge,
              expiresIn: resp.expires_in,
              issuedAt: Date.now(),
            },
          });
          return { expiresIn: resp.expires_in };
        } catch (err: unknown) {
          const message =
            (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
            "Could not resend code. Please wait.";
          set({ isLoading: false, error: message });
          throw err;
        }
      },

      logout: async () => {
        try {
          const token = get().token;
          if (token) {
            await apiPost("/auth/logout", {});
          }
        } catch {
          // Best-effort: clear local state regardless
        } finally {
          set({
            user: null,
            token: null,
            refreshToken: null,
            sessionId: null,
            isLoading: false,
            error: null,
            otpChallenge: null,
          });
          // Broadcast logout to other tabs
          try {
            const bc = new BroadcastChannel("cia-auth");
            bc.postMessage({ type: "LOGOUT" });
            bc.close();
          } catch {
            /* BroadcastChannel may not be supported */
          }
        }
      },

      clearChallenge: () => set({ otpChallenge: null, error: null }),
      clearError: () => set({ error: null }),
      setToken: (token: string, refreshToken?: string) =>
        set({ token, ...(refreshToken ? { refreshToken } : {}) }),
    }),
    {
      name: "cia-auth",
      partialize: (s) => ({
        user: s.user,
        token: s.token,
        refreshToken: s.refreshToken,
        sessionId: s.sessionId,
      }),
    },
  ),
);
