import { useQuery } from "@tanstack/react-query";
import {
  Line,
  LineChart,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from "recharts";
import { PageHeader, StatCard } from "@/components/app/primitives";
import { getDashboard, getAlerts } from "@/services/api";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { format } from "date-fns";
import { useRBAC } from "@/hooks/useRBAC";
import { PermissionCard } from "@/components/rbac/permission";
import { PERMISSIONS } from "@/lib/rbac";

const ROLE_DASHBOARDS: Record<string, { title: string; subtitle: string; cards: string[] }> = {
  Investigator: {
    title: "Investigator Command Center",
    subtitle: "Active cases, local incident feeds, repeat offenders, and precinct map intelligence.",
    cards: ["My Cases", "Assigned District", "Recent FIRs", "My Investigations", "Repeat Offenders", "Crime Map"],
  },
  "Senior Investigator": {
    title: "Senior Investigator Command Center",
    subtitle: "Cross-district tracking, gang networks, financial crime patterns, and tactical analytics.",
    cards: ["Cross District Cases", "Gang Detection", "Financial Crime", "Repeat Offenders", "Pattern Intelligence", "Crime Map"],
  },
  Analyst: {
    title: "Crime Intelligence Analyst Hub",
    subtitle: "Spatial intelligence, predictive trends, hot-spot clusters, and demographic distributions.",
    cards: ["Crime Trends", "Forecasts", "Heatmaps", "District Ranking", "Crime Statistics", "Pattern Intelligence"],
  },
  Supervisor: {
    title: "Precinct supervisor Dashboard",
    subtitle: "Resource allocation, personnel performance, compliance audit logs, and regional alerts.",
    cards: ["All Investigations", "Officer Performance", "Audit Dashboard", "Crime Map", "Network", "Reports"],
  },
  Policymaker: {
    title: "State Policy & Analytics Executive Dashboard",
    subtitle: "State-wide statistics, growth comparisons, year-over-year forecasting, and budget analytics.",
    cards: ["State Trends", "Heatmaps", "Forecasts", "District Comparison", "Crime Growth", "Budget Analytics"],
  },
  Admin: {
    title: "System Administration & Health Console",
    subtitle: "Full-spectrum visibility over users, roles, system health diagnostics, and audit logs.",
    cards: ["Everything", "Users", "Roles", "Permissions", "Audit", "System Health"],
  },
};

const CHART_COLORS = [
  "var(--color-chart-1)",
  "var(--color-chart-2)",
  "var(--color-chart-3)",
  "var(--color-chart-4)",
  "var(--color-chart-5)",
];

// Normalize uppercase role strings (e.g. "SUPERVISOR") to the title-case keys in ROLE_DASHBOARDS
function normalizeRoleKey(role: string | undefined): string {
  if (!role) return "Investigator";
  const map: Record<string, string> = {
    INVESTIGATOR: "Investigator",
    SENIOR_INVESTIGATOR: "Senior Investigator",
    ANALYST: "Analyst",
    SUPERVISOR: "Supervisor",
    POLICY_MAKER: "Policymaker",
    ADMINISTRATOR: "Admin",
  };
  return map[role.toUpperCase()] ?? "Investigator";
}

export function DynamicDashboard() {
  const rbac = useRBAC();
  const currentRole = normalizeRoleKey(rbac.role);
  const config = ROLE_DASHBOARDS[currentRole] ?? ROLE_DASHBOARDS.Investigator;

  const { data, isLoading } = useQuery({
    queryKey: ["dashboard", currentRole],
    queryFn: getDashboard,
  });

  const { data: alerts } = useQuery({
    queryKey: ["alerts"],
    queryFn: getAlerts,
  });

  // Decide layout visibility based on capabilities (permissions) instead of hardcoding roles
  const canViewMap = rbac.canViewCrimeMap;
  const canViewNetwork = rbac.canViewCriminalNetwork;
  const canViewFinancial = rbac.canViewFinancialCrime;
  const canViewPattern = rbac.canViewPatternAnalysis;
  const canViewAudit = rbac.canViewAuditLogs;

  return (
    <div className="p-6 max-w-[1600px] mx-auto animate-in fade-in duration-300">
      <PageHeader
        title={config.title}
        subtitle={`${config.subtitle} - logged in as ${rbac.user?.name || "Officer"}`}
      />

      {/* Role Workspace Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
        {config.cards.map((card) => (
          <div
            key={card}
            className="rounded-xl border border-white/5 bg-card/60 backdrop-blur-md p-3.5 text-card-foreground shadow-sm hover:border-primary/20 hover:translate-y-[-1px] transition-all duration-200"
          >
            <div className="text-[10px] uppercase tracking-wider text-muted-foreground/80 font-semibold">
              Workspace module
            </div>
            <div className="mt-1 text-sm font-bold text-foreground">{card}</div>
          </div>
        ))}
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3 mb-6">
        {isLoading || !data
          ? Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-24 rounded-xl" />)
          : data.kpis.map((k) => (
              <StatCard key={k.label} label={k.label} value={k.value.toLocaleString()} delta={k.delta} />
            ))}
      </div>

      {/* Primary Analytics Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Crime Trend (Analyst, Supervisor, Senior Investigator, Policymaker, Admin) */}
        {canViewPattern ? (
          <Panel title="Crime-type trend — last 12 months" caption="Monthly FIR counts by major crime categories">
            <div className="h-72">
              {data ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={data.monthlyTrend}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis dataKey="month" tick={{ fontSize: 11 }} stroke="var(--color-muted-foreground)" />
                    <YAxis tick={{ fontSize: 11 }} stroke="var(--color-muted-foreground)" />
                    <Tooltip
                      contentStyle={{
                        fontSize: 12,
                        borderRadius: 8,
                        border: "1px solid var(--color-border)",
                        background: "var(--color-card)",
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                    <Line dataKey="Theft" stroke={CHART_COLORS[0]} strokeWidth={2} dot={false} />
                    <Line dataKey="Robbery" stroke={CHART_COLORS[1]} strokeWidth={2} dot={false} />
                    <Line dataKey="Cybercrime" stroke={CHART_COLORS[2]} strokeWidth={2} dot={false} />
                    <Line dataKey="Assault" stroke={CHART_COLORS[3]} strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <Skeleton className="w-full h-full rounded-xl" />
              )}
            </div>
          </Panel>
        ) : (
          <PermissionCard
            moduleName="Trend Analytics"
            permissions={[PERMISSIONS.PATTERN_ANALYSIS]}
            reason="Operational trend charts require pattern intelligence clearance."
          />
        )}

        {/* Case Status Breakdown */}
        <Panel title="Operational case status" caption="Active state-wide status distribution">
          <div className="h-72">
            {data ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data.statusBreakdown}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={55}
                    outerRadius={90}
                    paddingAngle={3}
                  >
                    {data.statusBreakdown.map((_, i) => (
                      <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      fontSize: 12,
                      borderRadius: 8,
                      border: "1px solid var(--color-border)",
                      background: "var(--color-card)",
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <Skeleton className="w-full h-full rounded-xl" />
            )}
          </div>
        </Panel>

        {/* District Rankings */}
        {canViewMap ? (
          <Panel title="Top districts by case volume" caption="Active case volume comparison">
            <div className="h-72">
              {data ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.districtCounts} layout="vertical" margin={{ left: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis type="number" tick={{ fontSize: 11 }} stroke="var(--color-muted-foreground)" />
                    <YAxis
                      dataKey="district"
                      type="category"
                      tick={{ fontSize: 11 }}
                      stroke="var(--color-muted-foreground)"
                      width={100}
                    />
                    <Tooltip
                      contentStyle={{
                        fontSize: 12,
                        borderRadius: 8,
                        border: "1px solid var(--color-border)",
                        background: "var(--color-card)",
                      }}
                    />
                    <Bar dataKey="cases" fill="var(--color-primary)" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <Skeleton className="w-full h-full rounded-xl" />
              )}
            </div>
          </Panel>
        ) : (
          <PermissionCard
            moduleName="District Rankings"
            permissions={[PERMISSIONS.CRIME_MAP]}
            reason="GIS analytics and district comparison profiles require Crime Map authorization."
          />
        )}
      </div>

      {/* Secondary Row: Alerts & Audits */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Alerts (Hides for Policymaker based on capabilities/lack of operational triggers) */}
        {canViewPattern ? (
          <div className="lg:col-span-2">
            <Panel title="Intelligence anomalies & alerts" caption="Early warnings generated by ML pattern models">
              <ul className="divide-y divide-border">
                {alerts
                  ? alerts.slice(0, 4).map((a) => {
                      const sev =
                        a.severity === "Critical"
                          ? "bg-destructive/10 text-destructive border-destructive/30"
                          : "bg-warning/10 text-warning-foreground border-warning/30";
                      return (
                        <li key={a.id} className="py-3.5 flex items-start gap-3">
                          <Badge className={cn("border font-semibold", sev)}>{a.severity}</Badge>
                          <div className="flex-1 min-w-0">
                            <div className="text-sm font-semibold">{a.title}</div>
                            <div className="text-xs text-muted-foreground mt-0.5">
                              {a.area} · {format(new Date(a.ts), "d MMM · HH:mm")}
                            </div>
                            <div className="text-xs mt-1 text-foreground/80 leading-relaxed">{a.detail}</div>
                          </div>
                        </li>
                      );
                    })
                  : Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-14 my-2 rounded-lg" />)}
              </ul>
            </Panel>
          </div>
        ) : (
          <div className="lg:col-span-2">
            <PermissionCard
              moduleName="Pattern Intelligence Alerts"
              permissions={[PERMISSIONS.PATTERN_ANALYSIS]}
              reason="Detailed operational alerts and anomaly detection outputs require Pattern Analysis privileges."
            />
          </div>
        )}

        {/* Audit Dashboard Card or Guard */}
        <div>
          {canViewAudit ? (
            <Panel title="System compliance audit logs" caption="Recent administrative action audits">
              <div className="text-xs text-muted-foreground leading-relaxed space-y-3">
                <p>System audit trail is active and monitoring platform interactions.</p>
                <div className="bg-muted/40 rounded-xl p-3 border border-border/40">
                  <div className="font-semibold text-foreground">Audit Compliance Level 1</div>
                  <div className="mt-1 text-[11px]">All data exports, role modifications, and PII views are registered.</div>
                </div>
                <Badge variant="secondary" className="font-semibold">
                  SECURE AUDIT CHANNEL
                </Badge>
              </div>
            </Panel>
          ) : (
            <PermissionCard
              moduleName="Compliance Audit Dashboard"
              permissions={[PERMISSIONS.VIEW_AUDIT_LOGS]}
              reason="Audit controls and compliance registries are restricted to Supervisors and Administrators."
            />
          )}
        </div>
      </div>
    </div>
  );
}

function Panel({
  title,
  caption,
  children,
}: {
  title: string;
  caption?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-white/5 bg-card/45 backdrop-blur-lg p-5 shadow-sm">
      <div className="mb-4">
        <div className="text-sm font-bold text-foreground">{title}</div>
        {caption && <div className="text-[11px] text-muted-foreground mt-0.5">{caption}</div>}
      </div>
      {children}
    </div>
  );
}
