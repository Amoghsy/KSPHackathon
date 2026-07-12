// src/stores/auth.ts — Zustand auth store with real API login support.

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { loginUser } from "@/lib/api/services";
import type { LoginRequest } from "@/lib/api/types";

export type Role = "Investigator" | "Analyst" | "Supervisor" | "Policymaker";

export interface AuthUser {
  id: string;
  name: string;
  username: string;
  role: Role;
  badgeNo: string;
  station: string;
}

interface AuthState {
  user: AuthUser | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;
  /** Real API login — POSTs to /api/v1/auth/login and stores JWT */
  login: (credentials: LoginRequest) => Promise<void>;
  /** Clear session */
  logout: () => void;
  /** Clear any error state */
  clearError: () => void;
}

const DISPLAY_NAMES: Record<string, string> = {
  Investigator: "Insp. Arjun Rao",
  Analyst: "Priya Kulkarni",
  Supervisor: "SP Ramesh Iyer",
  Policymaker: "Dr. Anitha Menon",
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isLoading: false,
      error: null,

      login: async (credentials: LoginRequest) => {
        set({ isLoading: true, error: null });
        try {
          const resp = await loginUser(credentials);

          const role = (credentials.role ?? "Investigator") as Role;
          const displayName = DISPLAY_NAMES[role] ?? credentials.username;

          set({
            user: {
              id: crypto.randomUUID(),
              name: displayName,
              username: resp.username ?? credentials.username,
              role: (resp.role as Role) ?? role,
              badgeNo: "KSP-" + Math.floor(10000 + Math.random() * 89999),
              station: "SCRB HQ, Bengaluru",
            },
            token: resp.access_token,
            isLoading: false,
            error: null,
          });
        } catch (err: unknown) {
          const message =
            (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
            (err as { message?: string })?.message ??
            "Login failed. Check credentials.";
          set({ isLoading: false, error: message, user: null, token: null });
          throw err;
        }
      },

      logout: () => set({ user: null, token: null, isLoading: false, error: null }),
      clearError: () => set({ error: null }),
    }),
    { name: "cia-auth", partialize: (s) => ({ user: s.user, token: s.token }) },
  ),
);
