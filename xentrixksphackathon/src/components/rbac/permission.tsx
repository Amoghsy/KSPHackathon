import { Lock, ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useAuthStore, type Role } from "@/stores/auth";
import { cn } from "@/lib/utils";
import {
  hasAnyPermission,
  hasPermission,
  maskAccount,
  maskName,
  maskPhone,
  requiredRoleLabel,
  type Permission,
} from "@/lib/rbac";

export function PermissionGuard({
  permissions,
  fallback = null,
  children,
}: {
  permissions: Permission[];
  fallback?: React.ReactNode;
  children: React.ReactNode;
}) {
  const user = useAuthStore((s) => s.user);
  return hasAnyPermission(user, permissions) ? <>{children}</> : <>{fallback}</>;
}

export function RoleGuard({
  roles,
  fallback = null,
  children,
}: {
  roles: Role[];
  fallback?: React.ReactNode;
  children: React.ReactNode;
}) {
  const user = useAuthStore((s) => s.user);
  const allowed = user?.role && roles.includes(user.role);
  return allowed ? <>{children}</> : <>{fallback}</>;
}

export function PermissionCard({
  title = "Permission required",
  moduleName,
  reason,
  permissions,
  className,
}: {
  title?: string;
  moduleName: string;
  reason?: string;
  permissions?: Permission[];
  className?: string;
}) {
  const user = useAuthStore((s) => s.user);
  return (
    <div className={cn("rounded-xl border border-border bg-card p-5 text-card-foreground", className)}>
      <div className="flex gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-warning/15 text-warning-foreground">
          <ShieldAlert className="h-5 w-5" />
        </div>
        <div className="min-w-0">
          <h2 className="text-sm font-semibold">{title}</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {reason ?? `You do not have permission to access ${moduleName}.`}
          </p>
          <dl className="mt-4 grid gap-2 text-xs sm:grid-cols-2">
            <div>
              <dt className="text-muted-foreground">Current role</dt>
              <dd className="font-medium">{user?.role ?? "Unauthenticated"}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Required role</dt>
              <dd className="font-medium">{requiredRoleLabel(permissions)}</dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  );
}

export function PermissionTooltip({
  permissions,
  children,
}: {
  permissions: Permission[];
  children: React.ReactElement;
}) {
  const user = useAuthStore((s) => s.user);
  const allowed = hasAnyPermission(user, permissions);
  if (allowed) return children;
  return (
    <TooltipProvider delayDuration={150}>
      <Tooltip>
        <TooltipTrigger asChild>{children}</TooltipTrigger>
        <TooltipContent>
          Requires {requiredRoleLabel(permissions)}.
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

export function RestrictedButton({
  permissions,
  children,
  className,
  ...props
}: React.ComponentProps<typeof Button> & { permissions: Permission[] }) {
  const user = useAuthStore((s) => s.user);
  const allowed = hasAnyPermission(user, permissions);
  return (
    <PermissionTooltip permissions={permissions}>
      <Button
        {...props}
        disabled={!allowed || props.disabled}
        className={cn(!allowed && "cursor-not-allowed opacity-60", className)}
      >
        {!allowed && <Lock className="mr-2 h-3.5 w-3.5" />}
        {children}
      </Button>
    </PermissionTooltip>
  );
}

export function MaskField({
  value,
  permission,
  kind = "name",
  hiddenText = "Hidden",
}: {
  value?: string | null;
  permission: Permission;
  kind?: "name" | "phone" | "account" | "address";
  hiddenText?: string;
}) {
  const user = useAuthStore((s) => s.user);
  if (hasPermission(user, permission)) return <>{value ?? ""}</>;
  
  // Policymaker hides sensitive fields entirely.
  if (user?.role === "Policymaker" || user?.role === "Policy Maker") {
    return <span className="text-muted-foreground/60 italic" title="Hidden for Policy Maker">{hiddenText}</span>;
  }

  // Standard masking for other roles.
  if (kind === "phone") return <span title="Masked by role">{maskPhone(value)}</span>;
  if (kind === "account") return <span title="Masked by role">{maskAccount(value)}</span>;
  if (kind === "address") return <span title="Masked by role">{hiddenText}</span>;
  return <span title="Masked by role">{maskName(value)}</span>;
}
