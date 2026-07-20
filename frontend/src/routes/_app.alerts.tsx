import { createFileRoute, useNavigate } from "@tanstack/react-router";
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import { format } from "date-fns";
import { AlertTriangle, TrendingUp, ShieldAlert, Activity, BarChart3, ExternalLink } from "lucide-react";

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
  const navigate = useNavigate();
  const [sev, setSev] = useState<(typeof SEV)[number]>("All");
  const [crime, setCrime] = useState<ForecastCrime>("Robbery");
  const [selectedAlert, setSelectedAlert] = useState<any | null>(null);
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
              onClick={() => setSelectedAlert(a)}
              className={cn(
                "rounded-xl glass border-l-4 p-4 hover:shadow-md transition-all cursor-pointer group",
                color,
              )}
            >
              <div className="flex items-start gap-3">
                <Badge className={badge}>{a.severity}</Badge>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <h3 className="text-sm font-semibold group-hover:text-primary transition-colors">{a.title}</h3>
                    <div className="text-xs text-muted-foreground shrink-0">
                      {format(new Date(a.ts), "d MMM yyyy · HH:mm")}
                    </div>
                  </div>
                  <div className="text-xs text-muted-foreground mt-0.5">{a.area}</div>
                  <p className="text-sm mt-2 text-foreground/90 leading-relaxed">{a.detail}</p>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedAlert(a);
                    }}
                    className="mt-2 text-xs font-medium text-primary hover:underline flex items-center gap-1"
                  >
                    <span>View details</span>
                    <ExternalLink className="h-3 w-3" />
                  </button>
                </div>
              </div>
            </li>
          );
        })}
      </ul>

      {/* Alert Details Dialog */}
      <Dialog open={!!selectedAlert} onOpenChange={(open) => !open && setSelectedAlert(null)}>
        <DialogContent className="max-w-2xl bg-card border-border shadow-2xl">
          {selectedAlert && (
            <>
              <DialogHeader className="space-y-2 border-b border-border pb-4">
                <div className="flex items-center justify-between">
                  <Badge
                    className={cn(
                      "px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider",
                      selectedAlert.severity === "Critical"
                        ? "bg-destructive text-destructive-foreground"
                        : selectedAlert.severity === "Warning"
                          ? "bg-warning text-warning-foreground"
                          : "bg-info text-info-foreground"
                    )}
                  >
                    {selectedAlert.severity} Alert
                  </Badge>
                  <span className="text-xs text-muted-foreground font-mono">
                    {format(new Date(selectedAlert.ts), "dd MMM yyyy, HH:mm:ss")}
                  </span>
                </div>
                <DialogTitle className="text-lg font-bold text-foreground flex items-center gap-2">
                  <ShieldAlert className="h-5 w-5 text-primary shrink-0" />
                  {selectedAlert.title}
                </DialogTitle>
                <DialogDescription className="text-xs text-muted-foreground font-medium">
                  Scope: <span className="text-foreground font-semibold">{selectedAlert.area}</span>
                </DialogDescription>
              </DialogHeader>

              <div className="py-3 space-y-4">
                {/* Statistical Metrics Grid */}
                <div className="grid grid-cols-3 gap-3">
                  <div className="rounded-xl border border-border/80 bg-muted/40 p-3 text-center">
                    <div className="flex items-center justify-center gap-1.5 text-muted-foreground text-[11px] font-medium mb-1">
                      <BarChart3 className="h-3.5 w-3.5 text-primary" />
                      <span>Volume Count</span>
                    </div>
                    <div className="text-base font-bold text-foreground font-mono">
                      {selectedAlert.count ?? "N/A"}
                    </div>
                  </div>

                  <div className="rounded-xl border border-border/80 bg-muted/40 p-3 text-center">
                    <div className="flex items-center justify-center gap-1.5 text-muted-foreground text-[11px] font-medium mb-1">
                      <Activity className="h-3.5 w-3.5 text-warning" />
                      <span>Z-Score Anomaly</span>
                    </div>
                    <div className="text-base font-bold text-foreground font-mono">
                      {selectedAlert.z_score ? `+${selectedAlert.z_score}σ` : "N/A"}
                    </div>
                  </div>

                  <div className="rounded-xl border border-border/80 bg-muted/40 p-3 text-center">
                    <div className="flex items-center justify-center gap-1.5 text-muted-foreground text-[11px] font-medium mb-1">
                      <ShieldAlert className="h-3.5 w-3.5 text-success" />
                      <span>Confidence Rating</span>
                    </div>
                    <div className="text-base font-bold text-foreground font-mono">
                      {selectedAlert.confidence
                        ? `${Math.round(selectedAlert.confidence * 100)}%`
                        : "N/A"}
                    </div>
                  </div>
                </div>

                {/* Analysis Breakdown */}
                <div className="rounded-xl border border-primary/20 bg-primary/5 p-4 space-y-1.5">
                  <div className="text-xs font-bold uppercase tracking-wider text-primary flex items-center gap-1.5">
                    <span>AI Intelligence Diagnosis</span>
                  </div>
                  <p className="text-xs text-foreground/90 leading-relaxed font-normal">
                    {selectedAlert.detail}
                  </p>
                </div>
              </div>

              <DialogFooter className="border-t border-border pt-4 sm:justify-between items-center gap-2">
                <div className="text-[11px] text-muted-foreground">
                  Reference ID: <span className="font-mono text-foreground">{selectedAlert.id}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSelectedAlert(null)}
                    className="text-xs h-8"
                  >
                    Close
                  </Button>
                  <Button
                    size="sm"
                    onClick={() => {
                      setSelectedAlert(null);
                      navigate({ to: "/cases" });
                    }}
                    className="text-xs h-8 bg-primary text-primary-foreground hover:opacity-90 gap-1.5"
                  >
                    <span>Investigate in Cases</span>
                    <ExternalLink className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
