import { cn } from "@/lib/utils";
import { useAuthStore } from "@/stores/auth";
import { Lock } from "lucide-react";
import type { ReactNode } from "react";

export function Masked({ children, className }: { children: ReactNode; className?: string }) {
  const role = useAuthStore((s) => s.user?.role);
  const allowed = role === "Supervisor";
  if (allowed) return <span className={className}>{children}</span>;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded bg-muted px-1.5 py-0.5 select-none blur-[3px] hover:blur-0 transition-all",
        className,
      )}
      title="Restricted — Supervisor access required"
    >
      <Lock className="h-3 w-3 opacity-60" />
      {children}
    </span>
  );
}

export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between pb-5 mb-5 border-b border-border/60">
      <div className="min-w-0">
        <h1 className="text-xl sm:text-2xl font-semibold tracking-tight text-foreground truncate">
          {title}
        </h1>
        {subtitle && (
          <p className="text-sm text-muted-foreground mt-1">{subtitle}</p>
        )}
      </div>
      {actions && <div className="flex items-center gap-2 shrink-0 flex-wrap">{actions}</div>}
    </div>
  );
}

export function StatCard({
  label,
  value,
  delta,
  caption,
}: {
  label: string;
  value: string | number;
  delta?: number;
  caption?: string;
}) {
  const up = (delta ?? 0) >= 0;
  return (
    <div
      className={cn(
        "group relative rounded-xl p-4 transition-all duration-200",
        "glass hover:-translate-y-0.5 hover:shadow-lg",
      )}
    >
      <div className="text-[11px] uppercase tracking-wider text-muted-foreground font-medium">
        {label}
      </div>
      <div className="mt-2 flex items-baseline gap-2">
        <span className="text-2xl font-semibold tabular-nums text-foreground">{value}</span>
        {delta !== undefined && (
          <span
            className={cn(
              "text-xs font-medium tabular-nums px-1.5 py-0.5 rounded",
              up ? "text-success bg-success/10" : "text-destructive bg-destructive/10",
            )}
          >
            {up ? "▲" : "▼"} {Math.abs(delta).toFixed(1)}%
          </span>
        )}
      </div>
      {caption && <div className="text-xs text-muted-foreground mt-1">{caption}</div>}
    </div>
  );
}
