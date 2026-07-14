import { ShieldAlert } from "lucide-react";
import { useAuthStore } from "@/stores/auth";

export function AccessDenied({
  moduleName,
  reason,
  requiredRole,
  actions,
}: {
  moduleName: string;
  reason?: string;
  requiredRole?: string;
  actions?: React.ReactNode;
}) {
  const user = useAuthStore((s) => s.user);
  return (
    <section className="w-full max-w-2xl rounded-xl border border-border bg-card p-6 shadow-sm text-card-foreground">
      <div className="flex gap-4">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-destructive/10 text-destructive">
          <ShieldAlert className="h-6 w-6" />
        </div>
        <div className="min-w-0">
          <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Access Restricted
          </div>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">{moduleName}</h1>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
            {reason ?? `You do not have permission to access ${moduleName}.`}
          </p>
          <dl className="mt-5 grid gap-3 text-sm sm:grid-cols-2">
            <div className="rounded-lg bg-muted/50 p-3">
              <dt className="text-xs text-muted-foreground">Current role</dt>
              <dd className="mt-1 font-medium">{user?.role ?? "Unauthenticated"}</dd>
            </div>
            <div className="rounded-lg bg-muted/50 p-3">
              <dt className="text-xs text-muted-foreground">Required role</dt>
              <dd className="mt-1 font-medium">{requiredRole ?? "Authorized SCRB personnel"}</dd>
            </div>
          </dl>
          {actions && <div className="mt-5">{actions}</div>}
        </div>
      </div>
    </section>
  );
}
