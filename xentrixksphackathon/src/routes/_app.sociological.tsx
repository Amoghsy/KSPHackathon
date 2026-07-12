import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  ResponsiveContainer,
} from "recharts";
import { PageHeader } from "@/components/app/primitives";
import { MockBadge } from "@/components/app/mock-badge";
import { getSociologicalInsights } from "@/services/api";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { ShieldAlert } from "lucide-react";

export const Route = createFileRoute("/_app/sociological")({
  head: () => ({
    meta: [{ title: "Sociological Insights — Crime Intelligence Assistant" }],
  }),
  component: SociologicalPage,
});

const CHART_COLORS = [
  "var(--color-chart-1)",
  "var(--color-chart-2)",
  "var(--color-chart-3)",
  "var(--color-chart-4)",
  "var(--color-chart-5)",
];

function Panel({ title, caption, children }: { title: string; caption?: string; children: React.ReactNode }) {
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

function SociologicalPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["sociological"],
    queryFn: getSociologicalInsights,
  });

  return (
    <div className="p-6 max-w-[1600px] mx-auto">
      <PageHeader
        title="Sociological Crime Insights"
        subtitle="Demographic and socio-economic patterns across Karnataka crime records."
        actions={<MockBadge />}
      />

      <div className="mb-4">
        <Badge variant="outline" className="gap-1.5 border-warning/40 bg-warning/10 text-warning-foreground">
          <ShieldAlert className="h-3.5 w-3.5" />
          Illustrative data — demographic fields are role-masked in production
        </Badge>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        <Panel title="Crime count by age band" caption="Accused age bands, rolling 12-month window">
          <div className="h-72">
            {data ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.byAge}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                  <XAxis dataKey="band" tick={{ fontSize: 11 }} stroke="var(--color-muted-foreground)" />
                  <YAxis tick={{ fontSize: 11 }} stroke="var(--color-muted-foreground)" />
                  <Tooltip
                    contentStyle={{
                      fontSize: 12,
                      borderRadius: 6,
                      border: "1px solid var(--color-border)",
                      background: "var(--color-card)",
                    }}
                  />
                  <Bar dataKey="count" fill="var(--color-primary)" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <Skeleton className="w-full h-full" />
            )}
          </div>
        </Panel>

        <Panel title="Crime count by gender" caption="Accused gender distribution">
          <div className="h-72">
            {data ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data.byGender}
                    dataKey="count"
                    nameKey="gender"
                    innerRadius={50}
                    outerRadius={95}
                    paddingAngle={2}
                  >
                    {data.byGender.map((_, i) => (
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

      <Panel
        title="Crime rate vs. socio-economic index"
        caption="Each point is a district; higher SEI ≈ better socio-economic conditions"
      >
        <div className="h-80">
          {data ? (
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 10, right: 20, bottom: 20, left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis
                  type="number"
                  dataKey="sei"
                  name="Socio-economic index"
                  domain={[20, 100]}
                  tick={{ fontSize: 11 }}
                  stroke="var(--color-muted-foreground)"
                  label={{ value: "Socio-economic index", position: "insideBottom", offset: -8, fontSize: 11 }}
                />
                <YAxis
                  type="number"
                  dataKey="crimeRate"
                  name="Crime rate"
                  tick={{ fontSize: 11 }}
                  stroke="var(--color-muted-foreground)"
                  label={{ value: "Crime rate", angle: -90, position: "insideLeft", fontSize: 11 }}
                />
                <Tooltip
                  cursor={{ strokeDasharray: "3 3" }}
                  contentStyle={{
                    fontSize: 12,
                    borderRadius: 6,
                    border: "1px solid var(--color-border)",
                    background: "var(--color-card)",
                  }}
                  labelFormatter={(_: unknown, payload) =>
                    payload?.[0]?.payload?.district ?? ""
                  }
                />
                <Scatter data={data.bySocioEconomic} fill="var(--color-primary)" />
              </ScatterChart>
            </ResponsiveContainer>
          ) : (
            <Skeleton className="w-full h-full" />
          )}
        </div>
      </Panel>

      <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
        {isLoading || !data
          ? Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-24 rounded-md" />)
          : data.callouts.map((c) => (
              <div
                key={c.title}
                className="rounded-xl glass p-4 border-l-2 border-l-primary"
              >
                <div className="text-sm font-semibold">{c.title}</div>
                <div className="text-xs text-muted-foreground mt-1 leading-relaxed">{c.detail}</div>
              </div>
            ))}
      </div>
    </div>
  );
}
