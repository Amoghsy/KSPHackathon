import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";
import { Sidebar } from "@/components/app/sidebar";
import { Topbar } from "@/components/app/topbar";
import { useAuthStore } from "@/stores/auth";
import { usePrefs } from "@/stores/prefs";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_app")({
  ssr: false,
  beforeLoad: () => {
    if (typeof window === "undefined") return;
    const user = useAuthStore.getState().user;
    if (!user) throw redirect({ to: "/login" });
  },
  component: AppShell,
});

function AppShell() {
  const mobileNavOpen = usePrefs((s) => s.mobileNavOpen);
  const setMobileNavOpen = usePrefs((s) => s.setMobileNavOpen);

  return (
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
            background:
              "radial-gradient(circle, oklch(0.5 0.14 220 / 0.55), transparent 70%)",
          }}
        />
        <div
          className="aurora-blob"
          style={{
            top: "20%",
            right: "-8%",
            width: "600px",
            height: "600px",
            background:
              "radial-gradient(circle, oklch(0.65 0.12 190 / 0.4), transparent 70%)",
          }}
        />
        <div
          className="aurora-blob"
          style={{
            bottom: "-15%",
            left: "30%",
            width: "500px",
            height: "500px",
            background:
              "radial-gradient(circle, oklch(0.4 0.1 262 / 0.35), transparent 70%)",
          }}
        />
      </div>

      {/* Desktop sidebar */}
      <div className="hidden md:block h-full shrink-0">
        <Sidebar />
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
          <Sidebar forceExpanded onNavigate={() => setMobileNavOpen(false)} />
        </div>
      </div>

      <div className="flex flex-1 flex-col min-w-0">
        <Topbar />
        <main className="flex-1 overflow-y-auto scrollbar-thin">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
