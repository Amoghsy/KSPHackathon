import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  ResponsiveContainer,
} from "recharts";
import { PageHeader } from "@/components/app/primitives";
import { getAlerts, getForecast, type ForecastCrime } from "@/services/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { format } from "date-fns";
import { AlertTriangle, TrendingUp } from "lucide-react";

export const Route = createFileRoute("/_app/alerts")({
  head: () => ({ meta: [{ title: "Alerts — Crime Intelligence Assistant" }] }),
  component: AlertsPage,
});

const SEV = ["All", "Critical", "Warning", "Info"] as const;
const CRIMES: ForecastCrime[] = ["Robbery", "Theft", "Cybercrime", "Assault"];

function AlertsPage() {
  const [sev, setSev] = useState<(typeof SEV)[number]>("All");
  const [crime, setCrime] = useState<ForecastCrime>("Robbery");
  const { data, isLoading } = useQuery({ queryKey: ["alerts"], queryFn: getAlerts });
  const { data: forecast } = useQuery({
    queryKey: ["forecast", crime],
    queryFn: () => getForecast(crime),
  });
  const items = (data ?? []).filter((a) => sev === "All" || a.severity === sev);

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <PageHeader
        title="Early Warning Center"
        subtitle="AI-generated alerts from anomaly detection across FIR feeds."
        actions={
          <div className="flex gap-1">
            {SEV.map((s) => (
              <Button
                key={s}
                variant={sev === s ? "default" : "outline"}
                size="sm"
                onClick={() => setSev(s)}
              >
                {s}
              </Button>
            ))}
          </div>
        }
      />

      <div className="rounded-xl glass p-4 mb-5">
        <div className="flex items-start justify-between gap-4 mb-3">
          <div>
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-primary" />
              <div className="text-sm font-semibold">Forecast — next 4 weeks</div>
            </div>
            <div className="text-[11px] text-muted-foreground">
              Actual counts plus 95% forecast confidence interval.
            </div>
          </div>
          <Select value={crime} onValueChange={(v) => setCrime(v as ForecastCrime)}>
            <SelectTrigger className="w-40 h-8">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {CRIMES.map((c) => (
                <SelectItem key={c} value={c}>
                  {c}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="h-64">
          {forecast ? (
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={forecast.points}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey="week" tick={{ fontSize: 11 }} stroke="var(--color-muted-foreground)" />
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
                <Area
                  type="monotone"
                  dataKey="band"
                  stroke="none"
                  fill="var(--color-primary)"
                  fillOpacity={0.18}
                  name="Confidence interval"
                  isAnimationActive={false}
                />
                <Line
                  type="monotone"
                  dataKey="actual"
                  stroke="var(--color-primary)"
                  strokeWidth={2.5}
                  dot={{ r: 3 }}
                  name="Actual"
                  connectNulls={false}
                />
                <Line
                  type="monotone"
                  dataKey="forecast"
                  stroke="var(--color-chart-2)"
                  strokeWidth={2}
                  strokeDasharray="4 4"
                  dot={{ r: 2 }}
                  name="Forecast"
                  connectNulls={false}
                />
              </ComposedChart>
            </ResponsiveContainer>
          ) : (
            <Skeleton className="w-full h-full" />
          )}
        </div>
        {forecast && (
          <div className="mt-3 text-xs text-muted-foreground border-t border-border pt-3">
            <span className="font-medium text-foreground">Auto-commentary:</span> {forecast.commentary}
          </div>
        )}
      </div>


      {isLoading && (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-24 rounded-md" />
          ))}
        </div>
      )}

      {!isLoading && items.length === 0 && (
        <div className="rounded-md border border-dashed border-border p-12 text-center text-muted-foreground">
          <AlertTriangle className="h-8 w-8 mx-auto mb-2 opacity-40" />
          No alerts at this time.
        </div>
      )}

      <ul className="space-y-3">
        {items.map((a) => {
          const color =
            a.severity === "Critical"
              ? "border-l-destructive"
              : a.severity === "Warning"
                ? "border-l-warning"
                : "border-l-info";
          const badge =
            a.severity === "Critical"
              ? "bg-destructive text-destructive-foreground"
              : a.severity === "Warning"
                ? "bg-warning text-warning-foreground"
                : "bg-info text-info-foreground";
          return (
            <li
              key={a.id}
              className={cn(
                "rounded-xl glass border-l-4 p-4 hover:shadow-sm transition-shadow",
                color,
              )}
            >
              <div className="flex items-start gap-3">
                <Badge className={badge}>{a.severity}</Badge>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <h3 className="text-sm font-semibold">{a.title}</h3>
                    <div className="text-xs text-muted-foreground shrink-0">
                      {format(new Date(a.ts), "d MMM yyyy · HH:mm")}
                    </div>
                  </div>
                  <div className="text-xs text-muted-foreground mt-0.5">{a.area}</div>
                  <p className="text-sm mt-2 text-foreground/90 leading-relaxed">{a.detail}</p>
                  <button className="mt-2 text-xs font-medium text-primary hover:underline">
                    View details →
                  </button>
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
