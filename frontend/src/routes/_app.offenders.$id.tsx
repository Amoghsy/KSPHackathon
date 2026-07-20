import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { PageHeader } from "@/components/app/primitives";
import { getOffender, similarOffenders, getOffenderIntelligence } from "@/services/api";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, User } from "lucide-react";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_app/offenders/$id")({
  head: () => ({ meta: [{ title: "Offender Profile — Crime Intelligence Assistant" }] }),
  component: OffenderDetailPage,
});

function OffenderDetailPage() {
  const { id } = Route.useParams();
  const { data: o, isLoading } = useQuery({
    queryKey: ["offender", id],
    queryFn: () => getOffender(id),
  });
  const { data: similar } = useQuery({
    queryKey: ["offender-similar", id],
    queryFn: () => similarOffenders(id),
  });
  const { data: intelligence } = useQuery({
    queryKey: ["offender-intelligence", id],
    queryFn: () => getOffenderIntelligence(id),
    enabled: !!o,
  });

  if (isLoading)
    return (
      <div className="p-6">
        <Skeleton className="h-64" />
      </div>
    );
  if (!o) return <div className="p-6 text-muted-foreground">Offender not found.</div>;

  const riskLvl = (o.risk_level || o.risk || "Low").toUpperCase();
  const riskCol =
    riskLvl === "CRITICAL" || riskLvl === "HIGH"
      ? "bg-destructive text-destructive-foreground"
      : riskLvl === "MEDIUM"
        ? "bg-warning text-warning-foreground"
        : "bg-success text-success-foreground";

  return (
    <div className="p-6 max-w-[1400px] mx-auto">
      <Link
        to="/offenders"
        className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground mb-3"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> Back to offender list
      </Link>
      <PageHeader
        title={o.name}
        subtitle={`${o.person_id || o.id} · Age ${o.age || "N/A"} · Last known: ${o.lastKnown || o.district}`}
        actions={
          <Badge className={riskCol}>
            {riskLvl} risk · {o.risk_score ?? o.riskScore ?? 0}/100
          </Badge>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 space-y-4">
          {o.behavioral_tags && o.behavioral_tags.length > 0 && (
            <div className="rounded-xl glass p-4">
              <div className="text-[11px] uppercase tracking-wider text-muted-foreground font-medium mb-3">
                Behavioral Tags & Security Indicators
              </div>
              <div className="flex flex-wrap gap-2">
                {o.behavioral_tags.map((t: any) => (
                  <div key={t.code} className="inline-flex flex-col p-2 bg-card border border-border rounded-lg max-w-[280px]">
                    <Badge className="w-fit mb-1 bg-primary/20 text-foreground border-none text-[10px]">
                      {t.label}
                    </Badge>
                    <span className="text-[10px] text-muted-foreground leading-normal">{t.reason}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {intelligence && (
            <div className="rounded-xl glass p-4 border border-primary/20">
              <div className="text-[11px] uppercase tracking-wider text-primary font-semibold mb-3 flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-primary animate-pulse" />
                AI Security Briefing Summary
              </div>
              <p className="text-xs text-foreground leading-relaxed whitespace-pre-wrap">
                {intelligence.summary}
              </p>
            </div>
          )}

          <div className="rounded-xl glass p-4">
            <div className="text-[11px] uppercase tracking-wider text-muted-foreground font-medium mb-3">
              Risk score breakdown
            </div>
            <div className="space-y-3">
              {(o.risk_factors ?? o.factors ?? []).map((f: any) => {
                const val = f.score !== undefined ? (f.score / f.max_score) * 100 : f.value;
                const scoreText = f.score !== undefined ? `${f.score}/${f.max_score}` : `${f.value}%`;
                const reasonText = f.reason;
                return (
                  <div key={f.label || f.name}>
                    <div className="flex justify-between text-xs mb-1">
                      <span>{f.label}</span>
                      <span className="font-mono tabular-nums">{scoreText}</span>
                    </div>
                    <div className="h-2 rounded bg-muted overflow-hidden mb-1">
                      <div
                        className={cn(
                          "h-full",
                          val > 70
                            ? "bg-destructive"
                            : val > 45
                              ? "bg-warning"
                              : "bg-success",
                        )}
                        style={{ width: `${val}%` }}
                      />
                    </div>
                    {reasonText && <p className="text-[10px] text-muted-foreground">{reasonText}</p>}
                  </div>
                );
              })}
            </div>
          </div>

          <div className="rounded-xl glass p-4">
            <div className="text-[11px] uppercase tracking-wider text-muted-foreground font-medium mb-3">
              Modus operandi
            </div>
            <div className="flex flex-wrap gap-2">
              {(o.modusOperandi ?? []).map((m: any) => (
                <Badge key={m} variant="secondary">
                  {m}
                </Badge>
              ))}
            </div>
          </div>

          <div className="rounded-xl glass p-4">
            <div className="text-[11px] uppercase tracking-wider text-muted-foreground font-medium mb-3">
              Linked case history
            </div>
            {(!o.cases || o.cases.length === 0) ? (
              <div className="text-sm text-muted-foreground">No cases on record.</div>
            ) : (
              <ul className="text-sm divide-y divide-border">
                {o.cases.map((c: any) => (
                  <li key={c.id} className="py-2 flex justify-between items-center">
                    <Link
                      to="/cases/$firId"
                      params={{ firId: c.id }}
                      className="font-mono text-xs text-primary hover:underline"
                    >
                      {c.crimeNo}
                    </Link>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      <span>{c.station}</span>
                      <span>{c.date}</span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        <div className="rounded-xl glass p-4">
          <div className="text-[11px] uppercase tracking-wider text-muted-foreground font-medium mb-3">
            Similar offenders
          </div>
          <ul className="space-y-2">
            {(similar ?? []).map((s) => (
              <li key={s.id}>
                <Link
                  to="/offenders/$id"
                  params={{ id: s.id }}
                  className="flex items-center gap-3 p-2 rounded hover:bg-accent"
                >
                  <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center">
                    <User className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="text-sm font-medium truncate">{s.name}</div>
                    <div className="text-[11px] text-muted-foreground">
                      {s.id} · {s.linkedCases} cases
                    </div>
                  </div>
                  <Badge
                    className={cn(
                      "text-[10px]",
                      s.risk === "High"
                        ? "bg-destructive text-destructive-foreground"
                        : s.risk === "Medium"
                          ? "bg-warning text-warning-foreground"
                          : "bg-success text-success-foreground",
                    )}
                  >
                    {s.risk}
                  </Badge>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
