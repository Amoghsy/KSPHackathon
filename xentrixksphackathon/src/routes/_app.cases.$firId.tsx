import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { PageHeader, Masked } from "@/components/app/primitives";
import { getFIR } from "@/services/api";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ArrowLeft, Check } from "lucide-react";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_app/cases/$firId")({
  head: () => ({ meta: [{ title: "Case Detail — Crime Intelligence Assistant" }] }),
  component: CaseDetailPage,
});

function CaseDetailPage() {
  const { firId } = Route.useParams();
  const { data: fir, isLoading } = useQuery({
    queryKey: ["fir", firId],
    queryFn: () => getFIR(firId),
  });

  if (isLoading) return <div className="p-6"><Skeleton className="h-64" /></div>;
  if (!fir) return <div className="p-6 text-muted-foreground">Case not found.</div>;

  return (
    <div className="p-6 max-w-[1400px] mx-auto">
      <Link
        to="/cases"
        className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground mb-3"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> Back to case search
      </Link>
      <PageHeader
        title={`FIR ${fir.crimeNo}`}
        subtitle={`${fir.station} · ${fir.district} · Registered ${fir.date}`}
        actions={
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="border font-medium">{fir.status}</Badge>
            <Badge>{fir.gravity}</Badge>
          </div>
        }
      />

      <Tabs defaultValue="overview">
        <TabsList className="mb-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="complainant">Complainant</TabsTrigger>
          <TabsTrigger value="accused">Accused</TabsTrigger>
          <TabsTrigger value="victims">Victims</TabsTrigger>
          <TabsTrigger value="acts">Acts & Sections</TabsTrigger>
          <TabsTrigger value="arrests">Arrests</TabsTrigger>
          <TabsTrigger value="chargesheet">Chargesheet</TabsTrigger>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
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
          <Card title="Complainant">
            <dl className="text-sm space-y-2">
              <Row label="Name" value={fir.complainant} />
              <Row label="Category" value={<Masked>General</Masked>} />
              <Row label="Religion" value={<Masked>Category A</Masked>} />
            </dl>
          </Card>
        </TabsContent>

        <TabsContent value="accused">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {fir.accused.map((a) => (
              <Card key={a.id} title={`${a.name} · ${a.id}`}>
                <div className="text-sm text-muted-foreground">Age {a.age}</div>
                <div className="text-xs mt-2">
                  Category: <Masked>General</Masked> · Religion: <Masked>Category A</Masked>
                </div>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="victims">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {fir.victims.map((v, i) => (
              <Card key={i} title={v.name}>
                <div className="text-sm text-muted-foreground">Age {v.age}</div>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="acts">
          <Card title="Applicable acts & sections">
            <div className="flex flex-wrap gap-2">
              {fir.actsSections.map((a) => (
                <Badge key={a} variant="secondary" className="font-mono">{a}</Badge>
              ))}
            </div>
          </Card>
        </TabsContent>

        <TabsContent value="arrests">
          <Card title="Arrests">
            {fir.arrests.length === 0 ? (
              <div className="text-sm text-muted-foreground">No arrests recorded.</div>
            ) : (
              <ul className="text-sm divide-y divide-border">
                {fir.arrests.map((a, i) => (
                  <li key={i} className="py-2 flex justify-between">
                    <span>{a.name}</span>
                    <span className="text-muted-foreground tabular-nums">{a.date}</span>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="chargesheet">
          <Card title="Chargesheet">
            {fir.chargesheet ? (
              <div className="text-sm font-mono">{fir.chargesheet}</div>
            ) : (
              <div className="text-sm text-muted-foreground">No chargesheet filed yet.</div>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="timeline">
          <Card title="Case timeline">
            <ol className="relative border-l-2 border-border ml-2 space-y-6 pl-6 pt-1">
              {fir.timeline.map((t, i) => (
                <li key={i} className="relative">
                  <span
                    className={cn(
                      "absolute -left-[33px] top-0.5 h-5 w-5 rounded-full flex items-center justify-center border-2",
                      t.done
                        ? "bg-primary text-primary-foreground border-primary"
                        : "bg-background border-border text-muted-foreground",
                    )}
                  >
                    {t.done ? <Check className="h-3 w-3" /> : <span className="text-[10px]">{i + 1}</span>}
                  </span>
                  <div className="text-sm font-medium">{t.label}</div>
                  <div className="text-xs text-muted-foreground">
                    {t.date || "Pending"}
                  </div>
                </li>
              ))}
            </ol>
          </Card>
        </TabsContent>
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
