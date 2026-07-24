import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";
import { useEffect } from "react";
import { DynamicSidebar } from "@/components/app/sidebar";
import { Topbar } from "@/components/app/topbar";
import { AccessRequestModal } from "@/components/app/AccessRequestModal";
import { useAuthStore } from "@/stores/auth";
import { usePrefs } from "@/stores/prefs";
import { cn } from "@/lib/utils";
import { canAccessRoute, findRouteAccess, requiredRoleLabel, ROLE_DEFAULT_LANDING } from "@/lib/rbac";
import { SessionSyncProvider } from "@/components/providers/SessionSyncProvider";
import { DOMTranslateProvider } from "@/components/providers/DOMTranslateProvider";

export const Route = createFileRoute("/_app")({
  ssr: false,
  beforeLoad: ({ location }) => {
    if (typeof window === "undefined") return;
    const user = useAuthStore.getState().user;
    if (!user) throw redirect({ to: "/login" });

    const routeAccess = findRouteAccess(location.pathname);
    if (routeAccess && !canAccessRoute(user, routeAccess)) {
      // Redirect to role-appropriate landing page rather than generic /access-restricted
      // when the user is at the root. This handles ADMINISTRATOR hitting "/" (Chat).
      const landing = ROLE_DEFAULT_LANDING[user.role] ?? "/access-restricted";
      const isRootOrDefault = location.pathname === "/" || location.pathname === "/dashboard";
      if (isRootOrDefault && landing !== location.pathname) {
        throw redirect({ to: landing as string });
      }
      throw redirect({
        to: "/access-restricted",
        search: {
          module: routeAccess.moduleName,
          required: requiredRoleLabel(routeAccess.permissions),
          from: location.pathname,
        },
      });
    }
  },
  component: AppShell,
});

function AppShell() {
  const lang = usePrefs((s) => s.lang);
  const mobileNavOpen = usePrefs((s) => s.mobileNavOpen);
  const setMobileNavOpen = usePrefs((s) => s.setMobileNavOpen);

  useEffect(() => {
    if (lang === "kn") {
      document.documentElement.classList.add("lang-kn");
    } else {
      document.documentElement.classList.remove("lang-kn");
    }
  }, [lang]);

  return (
    <SessionSyncProvider>
    <div className="relative flex h-screen w-full overflow-hidden">
      {/* Ambient aurora background */}
      <div className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
        <div
          className="aurora-blob"
          style={{
            top: "-10%",
            left: "-5%",
            width: "520px",
            height: "520px",
            background: "radial-gradient(circle, oklch(0.5 0.14 220 / 0.55), transparent 70%)",
          }}
        />
        <div
          className="aurora-blob"
          style={{
            top: "20%",
            right: "-8%",
            width: "600px",
            height: "600px",
            background: "radial-gradient(circle, oklch(0.65 0.12 190 / 0.4), transparent 70%)",
          }}
        />
        <div
          className="aurora-blob"
          style={{
            bottom: "-15%",
            left: "30%",
            width: "500px",
            height: "500px",
            background: "radial-gradient(circle, oklch(0.4 0.1 262 / 0.35), transparent 70%)",
          }}
        />
      </div>

      {/* Desktop sidebar */}
      <div className="hidden md:block h-full shrink-0">
        <DynamicSidebar />
      </div>

      {/* Mobile drawer */}
      <div
        className={cn(
          "md:hidden fixed inset-0 z-50 transition-opacity duration-200",
          mobileNavOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none",
        )}
      >
        <div
          className="absolute inset-0 bg-black/50 backdrop-blur-sm"
          onClick={() => setMobileNavOpen(false)}
        />
        <div
          className={cn(
            "absolute inset-y-0 left-0 transition-transform duration-300",
            mobileNavOpen ? "translate-x-0" : "-translate-x-full",
          )}
        >
          <DynamicSidebar forceExpanded onNavigate={() => setMobileNavOpen(false)} />
        </div>
      </div>

      <div className="flex flex-1 flex-col min-w-0">
        <Topbar />
        <main className="flex-1 overflow-y-auto scrollbar-thin">
          <DOMTranslateProvider>
            <Outlet />
          </DOMTranslateProvider>
        </main>
        <AccessRequestModal />
      </div>
    </div>
    </SessionSyncProvider>
  );
}
