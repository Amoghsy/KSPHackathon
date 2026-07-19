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
import { getAlerts, getForecast, getAdvancedForecast, type ForecastCrime } from "@/services/api";
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

function AdvancedMonthlyForecastCard() {
  const [selectedCrime, setSelectedCrime] = useState<string>("All");
  const [selectedDistrict, setSelectedDistrict] = useState<string>("All");
  const [selectedPeriods, setSelectedPeriods] = useState<number>(3);

  const { data: advancedForecast, isLoading: isAdvLoading } = useQuery({
    queryKey: ["advanced-forecast", selectedDistrict, selectedCrime, selectedPeriods],
    queryFn: () =>
      getAdvancedForecast({
        district: selectedDistrict,
        crimeType: selectedCrime,
        periods: selectedPeriods,
      }),
  });

  const chartData = advancedForecast
    ? [
        ...advancedForecast.history.map((h: any) => ({
          month: h.month,
          actual: h.count,
          forecast: null,
          lower: null,
          upper: null,
        })),
        ...advancedForecast.forecast.map((f: any) => {
          const count = f.count;
          const conf = advancedForecast.confidence || 0.70;
          const variance = count * (1.0 - conf) * 0.5;
          return {
            month: f.month,
            actual: null,
            forecast: count,
            lower: Math.max(0, count - variance),
            upper: count + variance,
          };
        }),
      ]
    : [];

  // Connect the last actual point to the first forecast point
  if (chartData.length > 0 && advancedForecast?.history?.length > 0 && advancedForecast?.forecast?.length > 0) {
    const lastHistoryIdx = advancedForecast.history.length - 1;
    const firstForecastIdx = advancedForecast.history.length;
    if (chartData[lastHistoryIdx] && chartData[firstForecastIdx]) {
      chartData[firstForecastIdx].actual = chartData[lastHistoryIdx].actual;
    }
  }

  const DISTRICTS = ["All", "Mysuru", "Mandya", "Bengaluru", "Dharwad", "Mangaluru"];
  const CRIME_TYPES = ["All", "Theft", "Robbery", "Cybercrime", "Assault"];
  const PERIODS_OPTIONS = [3, 6, 12];

  return (
    <div className="rounded-xl glass p-4 mb-5 border border-primary/20 bg-background/50">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
        <div>
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-primary animate-pulse" />
            <div className="text-sm font-semibold">Advanced Monthly Crime Forecasting (ARIMA)</div>
          </div>
          <div className="text-[11px] text-muted-foreground">
            Multi-period monthly projection using AutoRegressive Integrated Moving Average (ARIMA) models.
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {/* District Select */}
          <div className="flex flex-col gap-1">
            <span className="text-[10px] font-medium text-muted-foreground">District</span>
            <Select value={selectedDistrict} onValueChange={setSelectedDistrict}>
              <SelectTrigger className="w-28 h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {DISTRICTS.map((d) => (
                  <SelectItem key={d} value={d} className="text-xs">
                    {d}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Crime Select */}
          <div className="flex flex-col gap-1">
            <span className="text-[10px] font-medium text-muted-foreground">Crime Type</span>
            <Select value={selectedCrime} onValueChange={setSelectedCrime}>
              <SelectTrigger className="w-32 h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {CRIME_TYPES.map((c) => (
                  <SelectItem key={c} value={c} className="text-xs">
                    {c}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Horizon Select */}
          <div className="flex flex-col gap-1">
            <span className="text-[10px] font-medium text-muted-foreground">Horizon</span>
            <Select value={String(selectedPeriods)} onValueChange={(v) => setSelectedPeriods(Number(v))}>
              <SelectTrigger className="w-24 h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {PERIODS_OPTIONS.map((p) => (
                  <SelectItem key={p} value={String(p)} className="text-xs">
                    {p} Months
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      <div className="h-64">
        {isAdvLoading ? (
          <Skeleton className="w-full h-full" />
        ) : chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis dataKey="month" tick={{ fontSize: 10 }} stroke="var(--color-muted-foreground)" />
              <YAxis tick={{ fontSize: 10 }} stroke="var(--color-muted-foreground)" />
              <Tooltip
                contentStyle={{
                  fontSize: 11,
                  borderRadius: 6,
                  border: "1px solid var(--color-border)",
                  background: "var(--color-card)",
                }}
              />
              <Legend wrapperStyle={{ fontSize: 10 }} />
              
              {/* Confidence interval band */}
              <Area
                type="monotone"
                dataKey="upper"
                stroke="none"
                fill="var(--color-chart-2)"
                fillOpacity={0.12}
                name="Confidence Interval"
                isAnimationActive={false}
              />
              <Area
                type="monotone"
                dataKey="lower"
                stroke="none"
                fill="var(--color-chart-2)"
                fillOpacity={0.0}
                legendType="none"
                isAnimationActive={false}
              />

              {/* Historical Line */}
              <Line
                type="monotone"
                dataKey="actual"
                stroke="var(--color-primary)"
                strokeWidth={2.5}
                dot={{ r: 3 }}
                name="Historical Trend"
                connectNulls={true}
              />

              {/* Forecast Line */}
              <Line
                type="monotone"
                dataKey="forecast"
                stroke="var(--color-chart-2)"
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={{ r: 3 }}
                name="ARIMA/WMA Forecast"
                connectNulls={true}
              />
            </ComposedChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-full flex items-center justify-center text-xs text-muted-foreground">
            No historical data available for forecasting in this scope.
          </div>
        )}
      </div>

      {advancedForecast && (
        <div className="mt-3 text-xs border-t border-border pt-3 flex items-center justify-between">
          <div>
            <span className="font-semibold text-foreground">Forecasting Algorithm:</span>{" "}
            <span className="font-mono text-primary bg-primary/10 px-1.5 py-0.5 rounded text-[10px]">
              {advancedForecast.method}
            </span>
          </div>
          <div>
            <span className="font-semibold text-foreground">Model Confidence Rating:</span>{" "}
            <span className={cn(
              "font-semibold",
              advancedForecast.confidence >= 0.8
                ? "text-success"
                : advancedForecast.confidence >= 0.65
                  ? "text-warning"
                  : "text-muted-foreground"
            )}>
              {Math.round(advancedForecast.confidence * 100)}%
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

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

      {/* Day 8: Advanced Monthly Crime Forecasting (ARIMA) */}
      <AdvancedMonthlyForecastCard />

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
                <XAxis
                  dataKey="week"
                  tick={{ fontSize: 11 }}
                  stroke="var(--color-muted-foreground)"
                />
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
            <span className="font-medium text-foreground">Auto-commentary:</span>{" "}
            {forecast.commentary}
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
