/* eslint-disable */
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useRef, useState, lazy, Suspense } from "react";
import { useQuery } from "@tanstack/react-query";
import { PageHeader } from "@/components/app/primitives";
import { MockBadge } from "@/components/app/mock-badge";
import { getNetwork } from "@/services/api";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { X, ZoomIn, ZoomOut, Maximize2 } from "lucide-react";

const ForceGraph2D = lazy(() => import("react-force-graph-2d"));

type NetworkSearch = {
  district?: string;
  crimeType?: string;
  policeStation?: string;
  timePeriod?: string;
  focusId?: string;
};

export const Route = createFileRoute("/_app/network")({
  validateSearch: (search: Record<string, unknown>): NetworkSearch => {
    return {
      district: (search.district as string) || undefined,
      crimeType: (search.crimeType as string) || undefined,
      policeStation: (search.policeStation as string) || undefined,
      timePeriod: (search.timePeriod as string) || undefined,
      focusId: (search.focusId as string) || undefined,
    };
  },
  head: () => ({ meta: [{ title: "Criminal Network — Crime Intelligence Assistant" }] }),
  component: NetworkPage,
});

const COLORS: Record<string, string> = {
  accused: "#1F3864",
  victim: "#2AA198",
  location: "#D4A017",
  case: "#6B7280",
};


function NetworkPage() {
  const navigate = useNavigate({ from: Route.fullPath });
  const filters = Route.useSearch();
  const { data, isLoading } = useQuery({
    queryKey: ["network", filters],
    queryFn: () => getNetwork(filters),
  });
  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<any>(null);
  const [dims, setDims] = useState({ w: 800, h: 600 });
  const [selected, setSelected] = useState<any>(null);
  const [q, setQ] = useState(filters.focusId || "");

  useEffect(() => {
    if (filters.focusId) {
      setQ(filters.focusId);
    }
  }, [filters.focusId]);

  useEffect(() => {
    if (!containerRef.current) return;
    const ro = new ResizeObserver(() => {
      const r = containerRef.current!.getBoundingClientRect();
      setDims({ w: r.width, h: r.height });
    });
    ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, []);

  return (
    <div className="flex flex-col h-full">
      <div className="px-6 pt-6">
        <PageHeader
          title="Criminal Network"
          subtitle="Interactive graph of accused, victims, locations and linked cases."
          actions={
            <div className="flex items-center gap-2">
              <MockBadge />
              <Input
                placeholder="Search node ID, name, or case no…"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && q.trim()) {
                    navigate({ search: (old) => ({ ...old, focusId: q.trim() }) });
                  }
                }}
                className="w-56 h-8"
              />
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  if (q.trim()) {
                    navigate({ search: (old) => ({ ...old, focusId: q.trim() }) });
                  }
                }}
              >
                Find
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setQ("");
                  navigate({ search: (old) => ({ ...old, focusId: undefined }) });
                  setTimeout(() => graphRef.current?.zoomToFit(400), 100);
                }}
                title="Reset investigation focus"
              >
                <Maximize2 className="h-4 w-4" />
              </Button>
            </div>
          }
        />

        
        {data?.summary && (
          <div className="mt-3 rounded-xl border border-primary/20 bg-primary/5 p-4 text-xs leading-relaxed text-foreground shadow-sm animate-in fade-in duration-300">
            <div className="font-semibold text-primary mb-1 uppercase tracking-wider text-[10px]">
              AI Intelligence Briefing
            </div>
            {data.summary}
          </div>
        )}
      </div>

      <div className="flex-1 relative border-t border-border bg-muted/30 mt-4" ref={containerRef}>
        {data?.focus_reason && (
          <div className="absolute top-4 left-4 z-10 rounded-xl glass shadow-lg p-2.5 text-xs text-foreground flex items-center gap-2 animate-in fade-in duration-200">
            <span className="font-semibold text-primary">Active Investigation:</span>
            <span>{data.focus_reason}</span>
            <button
              onClick={() => {
                setQ("");
                navigate({ search: (old) => ({ ...old, focusId: undefined }) });
              }}
              className="text-muted-foreground hover:text-foreground ml-1 p-0.5 rounded-full hover:bg-muted"
              title="Reset focus"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        )}

        {isLoading || !data ? (
          <Skeleton className="absolute inset-4" />
        ) : (
          <Suspense fallback={<Skeleton className="absolute inset-4" />}>
            <ForceGraph2D
              ref={graphRef}
              graphData={data as any}
              width={dims.w}
              height={dims.h}
              nodeColor={(n: any) => COLORS[n.kind]}
              nodeRelSize={5}
              linkColor={() => "rgba(100,116,139,0.35)"}
              linkWidth={1}
              nodeLabel={(n: any) => `${n.label} · ${n.kind}`}
              onNodeClick={(n: any) => setSelected(n)}
              cooldownTicks={80}
            />
          </Suspense>
        )}


        {/* Legend */}
        <div className="absolute bottom-4 left-4 rounded-xl glass/95 backdrop-blur p-3 text-xs shadow-sm">
          <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1.5 font-medium">
            Legend
          </div>
          <div className="space-y-1">
            {Object.entries(COLORS).map(([k, c]) => (
              <div key={k} className="flex items-center gap-2 capitalize">
                <span className="h-3 w-3 rounded-full" style={{ background: c }} />
                {k}
              </div>
            ))}
          </div>
        </div>

        {/* Zoom controls */}
        <div className="absolute bottom-4 right-4 flex flex-col gap-1">
          <Button
            size="icon"
            variant="outline"
            className="h-8 w-8"
            onClick={() => graphRef.current?.zoom((graphRef.current?.zoom() ?? 1) * 1.4, 300)}
          >
            <ZoomIn className="h-4 w-4" />
          </Button>
          <Button
            size="icon"
            variant="outline"
            className="h-8 w-8"
            onClick={() => graphRef.current?.zoom((graphRef.current?.zoom() ?? 1) / 1.4, 300)}
          >
            <ZoomOut className="h-4 w-4" />
          </Button>
        </div>

        {/* Side panel */}
        {selected && (
          <aside className="absolute top-4 right-4 w-72 rounded-xl glass shadow-lg p-4 animate-in slide-in-from-right duration-200">
            <div className="flex items-start justify-between gap-2">
              <div>
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">
                  {selected.kind}
                </div>
                <div className="text-sm font-semibold">{selected.label}</div>
                <div className="text-[11px] text-muted-foreground font-mono">{selected.id}</div>
              </div>
              <button
                onClick={() => setSelected(null)}
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="mt-3 space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Connections</span>
                <Badge variant="secondary">
                  {data?.links.filter(
                    (l: any) =>
                      l.source.id === selected.id ||
                      l.source === selected.id ||
                      l.target.id === selected.id ||
                      l.target === selected.id,
                  ).length ?? 0}
                </Badge>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Type</span>
                <span className="capitalize">{selected.kind}</span>
              </div>
              
              {selected.kind === "accused" && (
                <>
                  {selected.metadata?.age !== undefined && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Age / Gender</span>
                      <span>
                        {selected.metadata.age} y/o · {selected.metadata.gender === 1 ? "Male" : "Female"}
                      </span>
                    </div>
                  )}
                  {(() => {
                    const ro = data?.repeat_offenders?.find((o: any) => o.id === selected.id);
                    if (ro) {
                      return (
                        <>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Risk Score</span>
                            <Badge
                              variant={ro.risk_score > 70 ? "destructive" : "secondary"}
                              className="text-[10px] font-semibold"
                            >
                              {ro.risk_score} / 100
                            </Badge>
                          </div>
                          {ro.cases && ro.cases.length > 0 && (
                            <div className="pt-2 border-t border-border mt-2">
                              <div className="text-muted-foreground mb-1 text-[10px] font-medium uppercase tracking-wide">
                                Cases ({ro.cases.length})
                              </div>
                              <div className="flex flex-wrap gap-1 max-h-24 overflow-y-auto">
                                {ro.cases.map((c: string) => (
                                  <Badge key={c} variant="outline" className="text-[10px] py-0">
                                    {c}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          )}
                          {ro.known_associates && ro.known_associates.length > 0 && (
                            <div className="pt-2 border-t border-border mt-2">
                              <div className="text-muted-foreground mb-1 text-[10px] font-medium uppercase tracking-wide">
                                Known Associates
                              </div>
                              <div className="flex flex-wrap gap-1 max-h-20 overflow-y-auto">
                                {ro.known_associates.map((a: string) => (
                                  <Badge key={a} variant="secondary" className="text-[10px] py-0">
                                    {a}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          )}
                        </>
                      );
                    }
                    return null;
                  })()}
                </>
              )}
            </div>
            <Button
              size="sm"
              className="w-full mt-4 bg-primary text-primary-foreground hover:opacity-90 font-medium"
              onClick={() => {
                navigate({ search: (old) => ({ ...old, focusId: selected.id }) });
                setSelected(null);
              }}
            >
              Focus Investigation
            </Button>
          </aside>

        )}

      </div>
    </div>
  );
}
