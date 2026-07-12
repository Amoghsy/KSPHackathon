import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { PageHeader } from "@/components/app/primitives";
import { MockBadge } from "@/components/app/mock-badge";
import { listOffenders } from "@/services/api";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { User } from "lucide-react";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_app/offenders/")({
  head: () => ({ meta: [{ title: "Offender Profiles — Crime Intelligence Assistant" }] }),
  component: OffendersPage,
});

function riskColor(r: string) {
  if (r === "High") return "bg-destructive text-destructive-foreground";
  if (r === "Medium") return "bg-warning text-warning-foreground";
  return "bg-success text-success-foreground";
}

function OffendersPage() {
  const { data, isLoading } = useQuery({ queryKey: ["offenders"], queryFn: listOffenders });
  const [q, setQ] = useState("");
  const items = (data ?? []).filter((o) => o.name.toLowerCase().includes(q.toLowerCase()));

  return (
    <div className="p-6 max-w-[1600px] mx-auto">
      <PageHeader
        title="Offender Profiles"
        subtitle={`${data?.length ?? 0} offenders tracked · sorted by risk score`}
        actions={<MockBadge />}
      />
      <div className="mb-4 max-w-md">
        <Input placeholder="Search by name…" value={q} onChange={(e) => setQ(e.target.value)} />
      </div>

      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
          {Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-40 rounded-md" />)}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
        {items.map((o) => (
          <Link
            key={o.id}
            to="/offenders/$id"
            params={{ id: o.id }}
            className="rounded-xl glass p-4 hover:shadow-sm hover:border-primary/50 transition-all"
          >
            <div className="flex items-start gap-3">
              <div className="h-11 w-11 rounded-full bg-muted flex items-center justify-center shrink-0">
                <User className="h-5 w-5 text-muted-foreground" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="text-sm font-semibold truncate">{o.name}</div>
                <div className="text-[11px] text-muted-foreground">
                  {o.id} · Age {o.age} · {o.lastKnown}
                </div>
              </div>
              <Badge className={cn("shrink-0", riskColor(o.risk))}>{o.risk}</Badge>
            </div>
            <div className="mt-3 flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Linked FIRs</span>
              <span className="font-semibold tabular-nums">{o.linkedCases}</span>
            </div>
            <div className="mt-1 flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Risk score</span>
              <span className="font-mono tabular-nums">{o.riskScore}/100</span>
            </div>
            <div className="mt-2 flex flex-wrap gap-1">
              {o.modusOperandi.slice(0, 2).map((m) => (
                <Badge key={m} variant="secondary" className="text-[10px]">{m}</Badge>
              ))}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
