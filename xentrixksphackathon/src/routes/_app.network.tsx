import { createFileRoute } from "@tanstack/react-router";
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

export const Route = createFileRoute("/_app/network")({
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
  const { data, isLoading } = useQuery({ queryKey: ["network"], queryFn: getNetwork });
  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<any>(null);
  const [dims, setDims] = useState({ w: 800, h: 600 });
  const [selected, setSelected] = useState<any>(null);
  const [q, setQ] = useState("");

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
                placeholder="Search node ID or label…"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                className="w-56 h-8"
              />
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  if (!data) return;
                  const node = data.nodes.find(
                    (n) =>
                      n.id.toLowerCase() === q.toLowerCase() ||
                      n.label.toLowerCase().includes(q.toLowerCase()),
                  );
                  if (node && graphRef.current) {
                    setSelected(node);
                    graphRef.current.centerAt((node as any).x, (node as any).y, 700);
                    graphRef.current.zoom(3, 700);
                  }
                }}
              >
                Find
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => graphRef.current?.zoomToFit(400)}
                title="Reset view"
              >
                <Maximize2 className="h-4 w-4" />
              </Button>
            </div>
          }
        />
      </div>

      <div className="flex-1 relative border-t border-border bg-muted/30" ref={containerRef}>
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
          <Button size="icon" variant="outline" className="h-8 w-8" onClick={() => graphRef.current?.zoom((graphRef.current?.zoom() ?? 1) * 1.4, 300)}>
            <ZoomIn className="h-4 w-4" />
          </Button>
          <Button size="icon" variant="outline" className="h-8 w-8" onClick={() => graphRef.current?.zoom((graphRef.current?.zoom() ?? 1) / 1.4, 300)}>
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
              <button onClick={() => setSelected(null)} className="text-muted-foreground hover:text-foreground">
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="mt-3 space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Connections</span>
                <Badge variant="secondary">
                  {data?.links.filter((l: any) => l.source.id === selected.id || l.source === selected.id || l.target.id === selected.id || l.target === selected.id).length ?? 0}
                </Badge>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Type</span>
                <span className="capitalize">{selected.kind}</span>
              </div>
            </div>
            <Button size="sm" className="w-full mt-4">Expand connections</Button>
          </aside>
        )}
      </div>
    </div>
  );
}
