import { createFileRoute } from "@tanstack/react-router";
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
import { MockBadge } from "@/components/app/mock-badge";
import { getDashboard, getAlerts } from "@/services/api";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { format } from "date-fns";

export const Route = createFileRoute("/_app/dashboard")({
  head: () => ({ meta: [{ title: "Dashboard — Crime Intelligence Assistant" }] }),
  component: DashboardPage,
});

const CHART_COLORS = [
  "var(--color-chart-1)",
  "var(--color-chart-2)",
  "var(--color-chart-3)",
  "var(--color-chart-4)",
  "var(--color-chart-5)",
];

function DashboardPage() {
  const { data, isLoading } = useQuery({ queryKey: ["dashboard"], queryFn: getDashboard });
  const { data: alerts } = useQuery({ queryKey: ["alerts"], queryFn: getAlerts });

  return (
    <div className="p-6 max-w-[1600px] mx-auto">
      <PageHeader
        title="Analytics Dashboard"
        subtitle={`Aggregate view of statewide crime data · as of ${format(new Date(), "d MMM yyyy")}`}
        actions={<MockBadge />}
      />

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3 mb-6">
        {isLoading || !data
          ? Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-24 rounded-md" />
            ))
          : data.kpis.map((k) => (
              <StatCard key={k.label} label={k.label} value={k.value.toLocaleString()} delta={k.delta} />
            ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
        <Panel title="Crime-type trend — last 12 months" caption="Monthly FIR counts, top 4 categories">
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
                      borderRadius: 6,
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
              <Skeleton className="w-full h-full" />
            )}
          </div>
        </Panel>

        <Panel title="Case status" caption="Statewide breakdown">
          <div className="h-72">
            {data ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data.statusBreakdown}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={50}
                    outerRadius={90}
                    paddingAngle={2}
                  >
                    {data.statusBreakdown.map((_, i) => (
                      <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      fontSize: 12,
                      borderRadius: 6,
                      border: "1px solid var(--color-border)",
                      background: "var(--color-card)",
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <Skeleton className="w-full h-full" />
            )}
          </div>
        </Panel>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Panel title="Top 5 districts by case volume" caption="Rolling 30-day window">
          <div className="h-64">
            {data ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.districtCounts} layout="vertical" margin={{ left: 40 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                  <XAxis type="number" tick={{ fontSize: 11 }} stroke="var(--color-muted-foreground)" />
                  <YAxis
                    dataKey="district"
                    type="category"
                    tick={{ fontSize: 11 }}
                    stroke="var(--color-muted-foreground)"
                    width={110}
                  />
                  <Tooltip
                    contentStyle={{
                      fontSize: 12,
                      borderRadius: 6,
                      border: "1px solid var(--color-border)",
                      background: "var(--color-card)",
                    }}
                  />
                  <Bar dataKey="cases" fill="var(--color-primary)" radius={[0, 3, 3, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <Skeleton className="w-full h-full" />
            )}
          </div>
        </Panel>

        <div className="lg:col-span-2">
          <Panel title="Recent alerts" caption="Auto-generated early warnings">
            <ul className="divide-y divide-border">
              {(alerts ?? []).slice(0, 5).map((a) => {
                const sev =
                  a.severity === "Critical"
                    ? "bg-destructive/10 text-destructive border-destructive/30"
                    : a.severity === "Warning"
                      ? "bg-warning/10 text-warning-foreground border-warning/40"
                      : "bg-info/10 text-info border-info/30";
                return (
                  <li key={a.id} className="py-3 flex items-start gap-3">
                    <Badge className={cn("border font-medium", sev)}>{a.severity}</Badge>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium">{a.title}</div>
                      <div className="text-xs text-muted-foreground mt-0.5">
                        {a.area} · {format(new Date(a.ts), "d MMM · HH:mm")}
                      </div>
                      <div className="text-xs mt-1 text-foreground/80">{a.detail}</div>
                    </div>
                  </li>
                );
              })}
              {!alerts && Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-12 my-2" />)}
            </ul>
          </Panel>
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
    <div className="rounded-xl glass p-4">
      <div className="mb-3">
        <div className="text-sm font-semibold">{title}</div>
        {caption && <div className="text-[11px] text-muted-foreground">{caption}</div>}
      </div>
      {children}
    </div>
  );
}
