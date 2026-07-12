import { create } from "zustand";
import { persist } from "zustand/middleware";

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
  login: (username: string, role: Role) => void;
  logout: () => void;
}

const NAMES: Record<Role, string> = {
  Investigator: "Insp. Arjun Rao",
  Analyst: "Priya Kulkarni",
  Supervisor: "SP Ramesh Iyer",
  Policymaker: "Dr. Anitha Menon",
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      login: (username, role) =>
        set({
          user: {
            id: crypto.randomUUID(),
            name: NAMES[role],
            username: username || NAMES[role].toLowerCase().replace(/[^a-z]/g, ""),
            role,
            badgeNo: "KSP-" + Math.floor(10000 + Math.random() * 89999),
            station: "SCRB HQ, Bengaluru",
          },
        }),
      logout: () => set({ user: null }),
    }),
    { name: "cia-auth" },
  ),
);
