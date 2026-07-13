/* eslint-disable */
import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState, lazy, Suspense } from "react";
import { useQuery } from "@tanstack/react-query";
import { PageHeader } from "@/components/app/primitives";
import { MockBadge } from "@/components/app/mock-badge";
import { getFinancialNetwork } from "@/services/api";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { X, ZoomIn, ZoomOut, Maximize2, ShieldAlert } from "lucide-react";

const ForceGraph2D = lazy(() => import("react-force-graph-2d"));

export const Route = createFileRoute("/_app/financial")({
  head: () => ({
    meta: [{ title: "Financial Crime — Crime Intelligence Assistant" }],
  }),
  component: FinancialPage,
});

const COLORS: Record<string, string> = {
  accused: "#1F3864",
  account: "#0EA5A4",
  case: "#6B7280",
  location: "#D4A017",
};

const SUSPICIOUS_COLOR = "#DC2626";
const NORMAL_LINK = "rgba(100,116,139,0.35)";

function FinancialPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["financial-network"],
    queryFn: getFinancialNetwork,
  });
  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<any>(null);
  const [dims, setDims] = useState({ w: 800, h: 600 });
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [selectedLink, setSelectedLink] = useState<any>(null);
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
          title="Financial Crime & Transaction Links"
          subtitle="Interactive graph of accused, bank accounts, and suspicious transactions."
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
                    setSelectedNode(node);
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
        {data?.patterns && (
          <div className="mt-1 mb-2 flex flex-wrap gap-2 animate-in fade-in duration-300">
            {data.patterns.circular_flows?.length > 0 && (
              <Badge variant="destructive" className="gap-1.5 animate-pulse">
                <ShieldAlert className="h-3.5 w-3.5" />
                Circular Flows: {data.patterns.circular_flows.length} loop(s) detected
              </Badge>
            )}
            {data.patterns.shared_accounts?.length > 0 && (
              <Badge variant="outline" className="gap-1.5 border-destructive/40 bg-destructive/10 text-destructive-foreground">
                <ShieldAlert className="h-3.5 w-3.5" />
                Shared Accounts: {data.patterns.shared_accounts.length} account(s) shared
              </Badge>
            )}
            {data.patterns.high_value_transfers?.length > 0 && (
              <Badge variant="outline" className="gap-1.5 border-warning/40 bg-warning/10 text-warning-foreground">
                <ShieldAlert className="h-3.5 w-3.5" />
                Suspicious Transfers: {data.patterns.high_value_transfers.length} flagged
              </Badge>
            )}
          </div>
        )}
      </div>

      <div className="flex-1 relative border-t border-border bg-muted/30" ref={containerRef}>
        {/* Floating Intelligence Panel */}
        {data?.patterns && (
          <div className="absolute top-4 left-4 z-10 w-72 rounded-xl glass shadow-lg p-3 max-h-[300px] overflow-y-auto">
            <div className="text-[10px] font-bold text-primary uppercase tracking-wider mb-2">
              Financial Intelligence Alerts
            </div>
            
            {data.patterns.circular_flows?.length > 0 ? (
              <div className="space-y-1.5 mb-3">
                <div className="text-[9px] font-bold text-destructive uppercase">
                  Circular Flows ({data.patterns.circular_flows.length})
                </div>
                {data.patterns.circular_flows.map((c: any, i: number) => (
                  <div key={i} className="text-[10px] bg-destructive/10 border border-destructive/20 rounded p-1.5 leading-relaxed font-mono">
                    {c.flow}
                  </div>
                ))}
              </div>
            ) : null}

            {data.patterns.shared_accounts?.length > 0 ? (
              <div className="space-y-1.5">
                <div className="text-[9px] font-bold text-warning uppercase">
                  Shared Accounts ({data.patterns.shared_accounts.length})
                </div>
                {data.patterns.shared_accounts.map((s: any, i: number) => (
                  <div key={i} className="text-[10px] bg-warning/10 border border-warning/20 rounded p-1.5 leading-normal">
                    <strong>{s.label}</strong> shared by:
                    <div className="text-[9px] text-muted-foreground mt-0.5">
                      {s.owners.join(", ")}
                    </div>
                  </div>
                ))}
              </div>
            ) : null}

            {data.patterns.circular_flows?.length === 0 && data.patterns.shared_accounts?.length === 0 && (
              <div className="text-[10px] text-muted-foreground">
                No money laundering cycles or shared accounts detected.
              </div>
            )}
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
              nodeColor={(n: any) => COLORS[n.kind] ?? "#888"}
              nodeRelSize={5}
              linkColor={(l: any) => (l.suspicious ? SUSPICIOUS_COLOR : NORMAL_LINK)}
              linkWidth={(l: any) => (l.suspicious ? 2 : 1)}
              linkDirectionalArrowLength={(l: any) => (l.suspicious ? 4 : 0)}
              linkDirectionalArrowRelPos={1}
              nodeLabel={(n: any) =>
                n.kind === "account" ? `${n.label} · ${n.bank}` : `${n.label} · ${n.kind}`
              }
              onNodeClick={(n: any) => {
                setSelectedNode(n);
                setSelectedLink(null);
              }}
              onLinkClick={(l: any) => {
                setSelectedLink(l);
                setSelectedNode(null);
              }}
              cooldownTicks={90}
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
            <div className="flex items-center gap-2 pt-1 border-t border-border mt-1">
              <span className="h-0.5 w-6" style={{ background: SUSPICIOUS_COLOR }} />
              Suspicious transaction
            </div>
          </div>
        </div>

        {/* Zoom */}
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

        {/* Side panel — node */}
        {selectedNode && (
          <aside className="absolute top-4 right-4 w-72 rounded-xl glass shadow-lg p-4 animate-in slide-in-from-right duration-200">
            <div className="flex items-start justify-between gap-2">
              <div>
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">
                  {selectedNode.kind}
                </div>
                <div className="text-sm font-semibold">{selectedNode.label}</div>
                <div className="text-[11px] text-muted-foreground font-mono">{selectedNode.id}</div>
              </div>
              <button
                onClick={() => setSelectedNode(null)}
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            {selectedNode.bank && (
              <div className="mt-3 text-xs flex justify-between">
                <span className="text-muted-foreground">Bank</span>
                <span>{selectedNode.bank}</span>
              </div>
            )}
            <div className="mt-2 text-xs flex justify-between">
              <span className="text-muted-foreground">Connections</span>
              <Badge variant="secondary">
                {data?.links.filter(
                  (l: any) =>
                    l.source.id === selectedNode.id ||
                    l.source === selectedNode.id ||
                    l.target.id === selectedNode.id ||
                    l.target === selectedNode.id,
                ).length ?? 0}
              </Badge>
            </div>
          </aside>
        )}

        {/* Side panel — link */}
        {selectedLink && (
          <aside className="absolute top-4 right-4 w-80 rounded-xl glass shadow-lg p-4 animate-in slide-in-from-right duration-200">
            <div className="flex items-start justify-between gap-2">
              <div>
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">
                  Transaction
                </div>
                <div className="text-sm font-semibold">
                  {selectedLink.source?.label ?? selectedLink.source} →{" "}
                  {selectedLink.target?.label ?? selectedLink.target}
                </div>
              </div>
              <button
                onClick={() => setSelectedLink(null)}
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="mt-3 space-y-2 text-xs">
              {selectedLink.amount !== undefined && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Amount</span>
                  <span className="tabular-nums font-medium">
                    ₹{selectedLink.amount.toLocaleString("en-IN")}
                  </span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-muted-foreground">Status</span>
                {selectedLink.suspicious ? (
                  <Badge className="bg-destructive text-destructive-foreground">Suspicious</Badge>
                ) : (
                  <Badge variant="secondary">Normal</Badge>
                )}
              </div>
              {selectedLink.reason && (
                <div className="pt-2 border-t border-border">
                  <div className="text-muted-foreground mb-1">Flag reason</div>
                  <div className="text-foreground leading-relaxed">{selectedLink.reason}</div>
                </div>
              )}
            </div>
          </aside>
        )}
      </div>
    </div>
  );
}
