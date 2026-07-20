/**
 * useInactivityLogout.ts
 *
 * Tracks user activity and auto-logs out after `timeoutMs` of inactivity.
 * Resets the timer on any mouse/keyboard/touch/scroll event.
 * Shows a 60-second warning before kicking the user out.
 */

import { useEffect, useRef, useCallback } from "react";
import { toast } from "sonner";

const ACTIVITY_EVENTS: (keyof DocumentEventMap)[] = [
  "mousemove",
  "mousedown",
  "keydown",
  "touchstart",
  "scroll",
  "click",
];

interface UseInactivityLogoutOptions {
  /** Total inactivity timeout in ms (default: 10 minutes) */
  timeoutMs?: number;
  /** Warning shown before logout, in ms (default: 60 seconds) */
  warningMs?: number;
  /** Callback to execute on final logout */
  onLogout: () => void;
  /** Whether the hook is active (e.g. only when logged in) */
  enabled?: boolean;
}

export function useInactivityLogout({
  timeoutMs = 10 * 60 * 1000,
  warningMs = 60 * 1000,
  onLogout,
  enabled = true,
}: UseInactivityLogoutOptions) {
  const logoutTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const warningTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const warningToastId = useRef<string | number>("inactivity-warning");
  const isWarningShown = useRef(false);

  const clearTimers = useCallback(() => {
    if (logoutTimerRef.current) clearTimeout(logoutTimerRef.current);
    if (warningTimerRef.current) clearTimeout(warningTimerRef.current);
    logoutTimerRef.current = null;
    warningTimerRef.current = null;
  }, []);

  const dismissWarning = useCallback(() => {
    if (isWarningShown.current) {
      toast.dismiss(warningToastId.current);
      isWarningShown.current = false;
    }
  }, []);

  const startTimers = useCallback(() => {
    clearTimers();
    dismissWarning();

    // Warning timer fires (timeoutMs - warningMs) before logout
    const warningDelay = Math.max(timeoutMs - warningMs, 0);

    warningTimerRef.current = setTimeout(() => {
      isWarningShown.current = true;
      toast.warning("Session expiring soon", {
        id: warningToastId.current,
        description:
          "You've been inactive for a while. You will be signed out in 60 seconds unless you interact.",
        duration: warningMs + 1000,
      });
    }, warningDelay);

    logoutTimerRef.current = setTimeout(() => {
      dismissWarning();
      toast.error("Session expired", {
        description: "You were signed out due to inactivity.",
        duration: 5000,
      });
      onLogout();
    }, timeoutMs);
  }, [timeoutMs, warningMs, clearTimers, dismissWarning, onLogout]);

  const resetTimer = useCallback(() => {
    dismissWarning();
    startTimers();
  }, [dismissWarning, startTimers]);

  useEffect(() => {
    if (!enabled) {
      clearTimers();
      dismissWarning();
      return;
    }

    startTimers();

    const handler = () => resetTimer();

    ACTIVITY_EVENTS.forEach((ev) => document.addEventListener(ev, handler, { passive: true }));

    return () => {
      clearTimers();
      dismissWarning();
      ACTIVITY_EVENTS.forEach((ev) => document.removeEventListener(ev, handler));
    };
  }, [enabled, startTimers, resetTimer, clearTimers, dismissWarning]);
}
