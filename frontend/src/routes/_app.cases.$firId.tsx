import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { PageHeader } from "@/components/app/primitives";
import { getFIR, getDecisionBrief } from "@/services/api";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";
import { cn } from "@/lib/utils";
import { useRBAC } from "@/hooks/useRBAC";
import { MaskField } from "@/components/rbac/permission";
import { PERMISSIONS } from "@/lib/rbac";

export const Route = createFileRoute("/_app/cases/$firId")({
  head: () => ({ meta: [{ title: "Case Detail — Crime Intelligence Assistant" }] }),
  component: CaseDetailPage,
});

function CaseDetailPage() {
  const { firId } = Route.useParams();
  const rbac = useRBAC();
  const { data: fir, isLoading } = useQuery({
    queryKey: ["fir", firId],
    queryFn: () => getFIR(firId),
  });

  const { data: brief, isLoading: isBriefLoading } = useQuery({
    queryKey: ["decision-brief", firId],
    queryFn: () => getDecisionBrief(firId),
    enabled: !!firId && rbac.role !== "ADMINISTRATOR" && rbac.role !== "POLICY_MAKER",
  });

  if (isLoading)
    return (
      <div className="p-6">
        <Skeleton className="h-64 animate-pulse rounded-xl" />
      </div>
    );
  if (!fir) return <div className="p-6 text-muted-foreground">Case not found.</div>;

  return (
    <div className="p-6 max-w-[1400px] mx-auto">
      <Link
        to="/cases"
        className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground mb-3 transition-colors"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> Back to case search
      </Link>
      <PageHeader
        title={`FIR ${fir.crimeNo}`}
        subtitle={`${fir.station} · ${fir.district} · Registered ${fir.date}`}
        actions={
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="border font-medium">
              {fir.status}
            </Badge>
            <Badge>{fir.gravity}</Badge>
          </div>
        }
      />

      <Tabs defaultValue="overview">
        <TabsList className="mb-4 bg-muted/40 p-1 border border-border/30 rounded-lg flex flex-wrap h-auto gap-0.5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="complainant">Complainant</TabsTrigger>
          <TabsTrigger value="accused">Accused</TabsTrigger>
          <TabsTrigger value="victims">Victims</TabsTrigger>
          <TabsTrigger value="acts">Acts & Sections</TabsTrigger>
          <TabsTrigger value="arrests">Arrests</TabsTrigger>
          <TabsTrigger value="chargesheet">Chargesheet</TabsTrigger>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
          {rbac.role !== "ADMINISTRATOR" && rbac.role !== "POLICY_MAKER" && (
            <>
              <TabsTrigger value="intelligence" className="bg-primary/5 text-primary-foreground border border-primary/20">
                Investigation Brief
              </TabsTrigger>
              <TabsTrigger value="similar">Similar Cases</TabsTrigger>
            </>
          )}
        </TabsList>

        <TabsContent value="overview">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card title="Case summary">
              <dl className="text-sm space-y-2">
                <Row label="Crime Head" value={fir.crimeHead} />
                <Row label="Case No." value={fir.caseNo} mono />
                <Row label="Station" value={fir.station} />
                <Row label="District" value={fir.district} />
                <Row label="Status" value={fir.status} />
              </dl>
            </Card>
            <Card title="Narrative">
              <p className="text-sm leading-relaxed text-foreground/90">{fir.narrative}</p>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="complainant">
          <Card title="Complainant Details">
            <dl className="text-sm space-y-2">
              <Row
                label="Complainant Name"
                value={
                  <MaskField
                    value={fir.complainant}
                    permission={PERMISSIONS.SENSITIVE_CASE_ACCESS}
                    kind="name"
                  />
                }
              />
              <Row
                label="Category"
                value={
                  <MaskField
                    value="General Category"
                    permission={PERMISSIONS.SENSITIVE_CASE_ACCESS}
                    kind="name"
                  />
                }
              />
              <Row
                label="Religion/Belief"
                value={
                  <MaskField
                    value="Category A"
                    permission={PERMISSIONS.SENSITIVE_CASE_ACCESS}
                    kind="name"
                  />
                }
              />
            </dl>
          </Card>
        </TabsContent>

        <TabsContent value="accused">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {(fir.accused ?? []).map((a: any) => (
              <Card key={a.id} title={`Accused ID: ${a.id}`}>
                <div className="text-sm font-semibold">
                  Name:{" "}
                  <MaskField
                    value={a.name}
                    permission={PERMISSIONS.SENSITIVE_CASE_ACCESS}
                    kind="name"
                  />
                </div>
                <div className="text-sm text-muted-foreground mt-1">Age: {a.age}</div>
                <div className="text-xs mt-2 text-muted-foreground/80">
                  Category:{" "}
                  <MaskField
                    value="General"
                    permission={PERMISSIONS.SENSITIVE_CASE_ACCESS}
                    kind="name"
                  />{" "}
                  · Religion:{" "}
                  <MaskField
                    value="Category A"
                    permission={PERMISSIONS.SENSITIVE_CASE_ACCESS}
                    kind="name"
                  />
                </div>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="victims">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {(fir.victims ?? []).map((v: any, i: number) => (
              <Card key={i} title={`Victim Record #${i + 1}`}>
                <div className="text-sm font-semibold">
                  Name:{" "}
                  <MaskField
                    value={v.name}
                    permission={PERMISSIONS.SENSITIVE_CASE_ACCESS}
                    kind="name"
                  />
                </div>
                <div className="text-sm text-muted-foreground mt-1">Age: {v.age}</div>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="acts">
          <Card title="Applicable acts & sections">
            <div className="flex flex-wrap gap-2">
              {(fir.actsSections ?? []).map((a: any) => (
                <Badge key={a} variant="secondary" className="font-mono">
                  {a}
                </Badge>
              ))}
            </div>
          </Card>
        </TabsContent>

        <TabsContent value="arrests">
          <Card title="Arrests Registry">
            {!fir.arrests || fir.arrests.length === 0 ? (
              <div className="text-sm text-muted-foreground">No arrests recorded.</div>
            ) : (
              <ul className="text-sm divide-y divide-border">
                {fir.arrests.map((a: any, i: number) => (
                  <li key={i} className="py-2.5 flex justify-between">
                    <span className="font-semibold">
                      <MaskField
                        value={a.name}
                        permission={PERMISSIONS.SENSITIVE_CASE_ACCESS}
                        kind="name"
                      />
                    </span>
                    <span className="text-muted-foreground tabular-nums">{a.date}</span>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="chargesheet">
          <Card title="Chargesheet Details">
            {fir.chargesheet ? (
              <div className="text-sm font-mono whitespace-pre-wrap">{fir.chargesheet}</div>
            ) : (
              <div className="text-sm text-muted-foreground">No chargesheet filed yet.</div>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="timeline">
          <Card title="Case timeline">
            <ol className="relative border-l-2 border-border ml-2 space-y-6 pl-6 pt-1">
              {(fir.timeline ?? []).map((t: any, i: number) => (
                <li key={i} className="relative">
                  <span className="absolute -left-[33px] top-0.5 h-5 w-5 rounded-full flex items-center justify-center border-2 bg-primary text-primary-foreground border-primary">
                    <span className="text-[10px]">{i + 1}</span>
                  </span>
                  <div className="text-sm font-medium">{t.title ?? t.label}</div>
                  <div className="text-xs text-muted-foreground">{t.date || "Pending"}</div>
                  {t.description && (
                    <div className="text-xs text-muted-foreground/70 mt-0.5">{t.description}</div>
                  )}
                </li>
              ))}
            </ol>
          </Card>
        </TabsContent>

        {rbac.role !== "ADMINISTRATOR" && rbac.role !== "POLICY_MAKER" && (
          <>
            <TabsContent value="intelligence">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-6">
                  {/* AI summary briefing */}
                  <div className="rounded-xl bg-gradient-to-r from-primary/10 via-primary/5 to-transparent p-5 border border-primary/20 shadow-md">
                    <h3 className="text-base font-bold text-primary mb-3">AI Narrative Summary</h3>
                    {isBriefLoading ? (
                      <Skeleton className="h-16 w-full" />
                    ) : (
                      <p className="text-sm leading-relaxed text-foreground/90 whitespace-pre-wrap">
                        {brief?.ai_summary || "AI narrative summary temporarily unavailable."}
                      </p>
                    )}
                  </div>

                  {/* Leads / follow-ups */}
                  <Card title="Suggested Investigative Follow-ups (Leads)">
                    {isBriefLoading ? (
                      <div className="space-y-2">
                        <Skeleton className="h-20 w-full" />
                        <Skeleton className="h-20 w-full" />
                      </div>
                    ) : !brief?.leads || brief.leads.length === 0 ? (
                      <div className="text-sm text-muted-foreground py-2">No evidence-backed leads identified.</div>
                    ) : (
                      <div className="space-y-4">
                        {brief.leads.map((lead: any) => {
                          const priorityColors: Record<string, string> = {
                            CRITICAL: "bg-red-500/20 border-red-500/30 text-red-400",
                            HIGH: "bg-orange-500/20 border-orange-500/30 text-orange-400",
                            MEDIUM: "bg-yellow-500/20 border-yellow-500/30 text-yellow-400",
                            LOW: "bg-blue-500/20 border-blue-500/30 text-blue-400",
                          };
                          return (
                            <div key={lead.lead_id} className="p-4 rounded-lg bg-card/60 border border-border/80 flex flex-col md:flex-row justify-between gap-4">
                              <div className="space-y-1.5 flex-1">
                                <div className="flex items-center gap-2 flex-wrap">
                                  <Badge className={cn("text-[10px] uppercase font-bold", priorityColors[lead.priority] || "bg-secondary")}>
                                    {lead.priority}
                                  </Badge>
                                  <span className="text-[10px] font-mono text-muted-foreground">{lead.lead_id}</span>
                                  <span className="text-[11px] text-primary font-medium">({lead.type})</span>
                                </div>
                                <h4 className="text-sm font-semibold">{lead.title}</h4>
                                <p className="text-xs text-muted-foreground leading-normal">{lead.description}</p>
                                {lead.evidence && (
                                  <div className="mt-2 text-[11px] text-muted-foreground/80 bg-muted/40 p-2 rounded leading-relaxed font-mono">
                                    <strong>Evidence base:</strong> {JSON.stringify(lead.evidence)}
                                  </div>
                                )}
                              </div>
                              <div className="flex md:flex-col items-start md:items-end justify-between md:justify-center gap-1 min-w-[120px]">
                                <div className="text-[10px] text-muted-foreground">Confidence Score</div>
                                <div className="text-lg font-bold text-emerald-400 tabular-nums">
                                  {Math.round(lead.confidence * 100)}%
                                </div>
                                <div className="text-[9px] text-muted-foreground mt-1">
                                  Source: {lead.source_modules?.join(", ")}
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </Card>
                </div>

                {/* Right sidebar for gaps & intelligence scope */}
                <div className="space-y-6">
                  {/* Evidence Gaps */}
                  <Card title="Information Gaps & Missing Evidence">
                    {isBriefLoading ? (
                      <Skeleton className="h-32 w-full" />
                    ) : !brief?.evidence_gaps || brief.evidence_gaps.length === 0 ? (
                      <div className="text-sm text-emerald-400 font-semibold py-2">✓ No critical evidence gaps identified.</div>
                    ) : (
                      <div className="space-y-3">
                        {brief.evidence_gaps.map((gap: any, i: number) => {
                          const severityIcons: Record<string, string> = {
                            HIGH: "🔴",
                            MEDIUM: "🟡",
                            LOW: "🔵",
                          };
                          return (
                            <div key={i} className="p-3 rounded-lg border border-border bg-card/40 text-xs space-y-1">
                              <div className="flex items-center justify-between">
                                <span className="font-bold tracking-tight text-foreground">{gap.type}</span>
                                <span>{severityIcons[gap.severity] || "⚪"}</span>
                              </div>
                              <p className="text-muted-foreground">{gap.description}</p>
                              <p className="text-[10px] text-muted-foreground/75 italic">Impact: {gap.impact}</p>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </Card>

                  {/* Composition Findings Overview */}
                  <Card title="Composed Modules Intelligence">
                    {isBriefLoading ? (
                      <Skeleton className="h-32 w-full" />
                    ) : (
                      <div className="text-xs space-y-3">
                        <div className="flex justify-between border-b border-border/40 pb-2">
                          <span className="text-muted-foreground">Day 5 Criminal Network Nodes:</span>
                          <span className="font-semibold text-foreground">{brief?.network_findings?.node_count ?? "Unavailable"}</span>
                        </div>
                        <div className="flex justify-between border-b border-border/40 pb-2">
                          <span className="text-muted-foreground">Day 5 Community ID:</span>
                          <span className="font-semibold text-primary">{brief?.network_findings?.community_id ?? "None detected"}</span>
                        </div>
                        <div className="flex justify-between border-b border-border/40 pb-2">
                          <span className="text-muted-foreground">Day 8 Highest Risk Suspect Score:</span>
                          <span className="font-semibold text-red-400 tabular-nums">
                            {brief?.risk_findings?.highest_risk_score ? `${brief.risk_findings.highest_risk_score.toFixed(1)}/100` : "None"}
                          </span>
                        </div>
                        <div className="flex justify-between border-b border-border/40 pb-2">
                          <span className="text-muted-foreground">Day 8 Behavioral tags:</span>
                          <span className="font-medium text-foreground text-right">{brief?.risk_findings?.behavioral_tags?.join(", ") || "None"}</span>
                        </div>
                        {rbac.canViewFinancialCrime && (
                          <div className="flex justify-between border-b border-border/40 pb-2">
                            <span className="text-muted-foreground">Suspicious transaction logs:</span>
                            <span className="font-semibold text-orange-400 tabular-nums">{brief?.financial_findings?.suspicious_transactions_count ?? 0}</span>
                          </div>
                        )}
                      </div>
                    )}
                  </Card>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="similar">
              <Card title="Similar Cases with Match Explanations">
                {isBriefLoading ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Skeleton className="h-36 w-full" />
                    <Skeleton className="h-36 w-full" />
                  </div>
                ) : !brief?.similar_cases || brief.similar_cases.length === 0 ? (
                  <div className="text-sm text-muted-foreground py-2">No similar cases found in the database.</div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {brief.similar_cases.map((sc: any, idx: number) => {
                      const dispatchUnauthorized = (district: string) => {
                        const e = new CustomEvent("district-not-authorized", {
                          detail: {
                            district_id: district,
                            can_request_access: true,
                            message: `You do not have access to data in ${district}`
                          }
                        });
                        window.dispatchEvent(e);
                      };

                      return (
                        <div key={idx} className="p-4 rounded-xl border border-border bg-card/40 flex flex-col justify-between gap-4">
                          <div className="space-y-2">
                            <div className="flex items-center justify-between flex-wrap gap-2">
                              <div>
                                <span className="text-xs font-mono font-bold text-primary">{sc.crime_no}</span>
                                <span className="text-xs text-muted-foreground block mt-0.5">District: {sc.district} · Station: {sc.police_station}</span>
                              </div>
                              <div className="flex items-center gap-1.5">
                                <Badge className="font-bold tabular-nums text-emerald-400 bg-emerald-500/10 border-emerald-500/20">
                                  {sc.similarity_score}% Similar
                                </Badge>
                              </div>
                            </div>

                            <div className="space-y-1 mt-2">
                              <div className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Matching Factors</div>
                              <ul className="text-xs space-y-1 list-inside list-disc text-foreground/90">
                                {sc.reasons.map((r: string, i: number) => (
                                  <li key={i}>{r}</li>
                                ))}
                              </ul>
                            </div>
                          </div>

                          <div className="pt-2 border-t border-border/50 flex justify-end">
                            {sc.is_authorized ? (
                              <Link to="/cases/$firId" params={{ firId: String(sc.case_master_id) }}>
                                <Button size="sm" variant="outline">
                                  View case details
                                </Button>
                              </Link>
                            ) : (
                              <Button
                                size="sm"
                                variant="destructive"
                                onClick={() => dispatchUnauthorized(sc.district)}
                                className="bg-red-950 text-red-200 border-red-900/40 hover:bg-red-900/50"
                              >
                                Request district access
                              </Button>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </Card>
            </TabsContent>
          </>
        )}
      </Tabs>
    </div>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl glass p-4">
      <div className="text-[11px] uppercase tracking-wider text-muted-foreground font-medium mb-3">
        {title}
      </div>
      {children}
    </div>
  );
}

function Row({ label, value, mono }: { label: string; value: React.ReactNode; mono?: boolean }) {
  return (
    <div className="flex justify-between gap-4 border-b border-border/60 pb-1.5 last:border-none last:pb-0">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className={cn(mono && "font-mono text-xs")}>{value}</dd>
    </div>
  );
}
