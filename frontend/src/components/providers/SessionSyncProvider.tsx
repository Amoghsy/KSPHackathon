/**
 * SessionSyncProvider.tsx
 *
 * Wraps the authenticated app layout to:
 * 1. Enforce 10-minute inactivity logout with a warning.
 * 2. Sync logout events across browser tabs via BroadcastChannel.
 * 3. Handle 401 SESSION_INACTIVE responses from the backend to force logout.
 */

import { useEffect, useCallback, type ReactNode } from "react";
import { useNavigate } from "@tanstack/react-router";
import { toast } from "sonner";
import { useAuthStore } from "@/stores/auth";
import { useInactivityLogout } from "@/hooks/useInactivityLogout";

interface SessionSyncProviderProps {
  children: ReactNode;
}

export function SessionSyncProvider({ children }: SessionSyncProviderProps) {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();

  const isLoggedIn = !!user;

  // ── Inactivity logout handler ──────────────────────────────────────────────
  const handleInactivityLogout = useCallback(async () => {
    const isAdmin = user?.role === "ADMINISTRATOR";
    await logout();
    navigate({ to: isAdmin ? "/admin-login" : "/login" });
  }, [logout, navigate, user]);

  useInactivityLogout({
    timeoutMs: 10 * 60 * 1000, // 10 minutes
    warningMs: 60 * 1000,      // warn 1 minute before
    onLogout: handleInactivityLogout,
    enabled: isLoggedIn,
  });

  // ── Cross-tab logout sync ──────────────────────────────────────────────────
  useEffect(() => {
    if (!isLoggedIn) return;

    let bc: BroadcastChannel | null = null;
    try {
      bc = new BroadcastChannel("cia-auth");
      bc.onmessage = async (event: MessageEvent) => {
        const isAdmin = user?.role === "ADMINISTRATOR";
        if (event.data?.type === "LOGOUT") {
          // Another tab signed out — reflect it here
          await logout();
          navigate({ to: isAdmin ? "/admin-login" : "/login" });
          toast.info("Signed out on another tab.");
        }
        if (event.data?.type === "SESSION_REVOKED") {
          await logout();
          navigate({ to: isAdmin ? "/admin-login" : "/login" });
          toast.error("Your session was terminated by an administrator.");
        }
      };
    } catch {
      /* BroadcastChannel not supported in older browsers */
    }

    return () => {
      bc?.close();
    };
  }, [isLoggedIn, logout, navigate]);

  // ── Listen for 401 SESSION_INACTIVE from axios interceptor ────────────────
  useEffect(() => {
    if (!isLoggedIn) return;

    const handleForceLogout = async (e: CustomEvent) => {
      const reason = e.detail?.reason as string | undefined;
      const isAdmin = user?.role === "ADMINISTRATOR";
      await logout();
      navigate({ to: isAdmin ? "/admin-login" : "/login" });

      if (reason === "SESSION_INACTIVE") {
        toast.error("Signed out due to inactivity.", {
          description: "Please sign in again to continue.",
        });
      } else if (reason === "SESSION_REVOKED") {
        toast.error("Your session was revoked.", {
          description: "Contact your administrator if you believe this is an error.",
        });
      } else {
        toast.error("Session expired. Please sign in again.");
      }
    };

    window.addEventListener("auth:force-logout", handleForceLogout as unknown as EventListener);
    return () => window.removeEventListener("auth:force-logout", handleForceLogout as unknown as EventListener);
  }, [isLoggedIn, logout, navigate]);

  return <>{children}</>;
}
