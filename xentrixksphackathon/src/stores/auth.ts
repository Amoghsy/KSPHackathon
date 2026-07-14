// src/stores/auth.ts — Zustand auth store with real API login support.

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { loginUser } from "@/lib/api/services";
import type { LoginRequest } from "@/lib/api/types";

export type Role = "Investigator" | "Senior Investigator" | "Analyst" | "Supervisor" | "Policymaker" | "Admin";

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
          
          // Formulate name from username by replacing separators and capitalizing
          let rawName = credentials.username
            .split(/[._-]/)
            .filter(Boolean)
            .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
            .join(" ");

          // Avoid duplicate prefixes if already entered in username
          const lowercaseName = rawName.toLowerCase();
          if (lowercaseName.startsWith("sp ")) {
            rawName = rawName.slice(3);
          } else if (lowercaseName.startsWith("insp ")) {
            rawName = rawName.slice(5);
          } else if (lowercaseName.startsWith("dr ")) {
            rawName = rawName.slice(3);
          } else if (lowercaseName.startsWith("insp. ")) {
            rawName = rawName.slice(6);
          } else if (lowercaseName.startsWith("dr. ")) {
            rawName = rawName.slice(4);
          }

          // Prepend correct role prefix
          let displayName = rawName;
          if (role === "Supervisor") {
            displayName = `SP ${rawName}`;
          } else if (role === "Senior Investigator") {
            displayName = `DySP ${rawName}`;
          } else if (role === "Investigator") {
            displayName = `Insp. ${rawName}`;
          } else if (role === "Policymaker") {
            displayName = `Dr. ${rawName}`;
          } else if (role === "Admin") {
            displayName = `Admin ${rawName}`;
          }

          // Generate stable badge number based on username hash
          let hash = 0;
          const cleanUsername = credentials.username.toLowerCase();
          for (let i = 0; i < cleanUsername.length; i++) {
            hash = cleanUsername.charCodeAt(i) + ((hash << 5) - hash);
          }
          const badgeCode = Math.abs(hash % 90000) + 10000;
          const badgeNo = credentials.username.toUpperCase().startsWith("KSP-")
            ? credentials.username.toUpperCase()
            : `KSP-${badgeCode}`;

          set({
            user: {
              id: crypto.randomUUID(),
              name: displayName,
              username: resp.username ?? credentials.username,
              role: (resp.role as Role) ?? role,
              badgeNo: badgeNo,
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
