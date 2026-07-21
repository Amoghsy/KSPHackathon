/* eslint-disable */
import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState, lazy, Suspense } from "react";
import { useQuery } from "@tanstack/react-query";
import { PageHeader } from "@/components/app/primitives";
import {
  getFinancialTopSuspects,
  searchFinancialNetwork,
} from "@/services/api";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import {
  X,
  ZoomIn,
  ZoomOut,
  Maximize2,
  ShieldAlert,
  ArrowLeft,
  Search,
  User,
  TrendingUp,
  FileText,
  AlertTriangle,
  Building2
} from "lucide-react";

const ForceGraph2D = lazy(() => import("react-force-graph-2d"));

export const Route = createFileRoute("/_app/financial")({
  head: () => ({
    meta: [{ title: "Financial Crime — Crime Intelligence Assistant" }],
  }),
  component: FinancialPage,
});

const COLORS: Record<string, string> = {
  accused: "#1F3864",
  "community leader": "#F97316",
  account: "#8B5CF6",
  case: "#64748B",
  location: "#475569",
};

const SUSPICIOUS_COLOR = "#DC2626";
const NORMAL_LINK = "rgba(100,116,139,0.35)";

const DISTRICTS = [
  "All",
  "Bengaluru Urban",
  "Bengaluru Rural",
  "Mysuru",
  "Hubballi-Dharwad",
  "Belagavi",
  "Kalaburagi",
  "Ballari",
  "Shivamogga",
  "Tumakuru",
  "Udupi"
];

function FinancialPage() {
  const [district, setDistrict] = useState<string>("All");
  const [searchAccused, setSearchAccused] = useState<string>("");
  const [searchCase, setSearchCase] = useState<string>("");

  // activeQuery handles the search query to backend
  const [activeQuery, setActiveQuery] = useState<{ q: string; type: "accused" | "case" } | null>(null);

  // Fetch top recommendations
  const { data: topSuspects, isLoading: topLoading } = useQuery<any[]>({
    queryKey: ["financial-top-suspects", district],
    queryFn: () => getFinancialTopSuspects({ district: district === "All" ? undefined : district }),
  });

  // Fetch search-based network graph data
  const { data: graphData, isLoading: graphLoading } = useQuery<any>({
    queryKey: ["financial-search-network", activeQuery, district],
    queryFn: () => {
      if (!activeQuery) return null;
      return searchFinancialNetwork({
        q: activeQuery.q,
        district: district === "All" ? undefined : district,
      });
    },
    enabled: !!activeQuery,
  });

  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<any>(null);
  const [dims, setDims] = useState({ w: 800, h: 500 });
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [selectedLink, setSelectedLink] = useState<any>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const ro = new ResizeObserver(() => {
      const r = containerRef.current!.getBoundingClientRect();
      setDims({ w: r.width, h: r.height });
    });
    ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, [activeQuery]); // Re-observe when switching view states

  // Handlers
  const handleAccusedSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchAccused.trim()) {
      setActiveQuery({ q: searchAccused.trim(), type: "accused" });
      setSearchCase(""); // Clear sibling search
    }
  };

  const handleCaseSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchCase.trim()) {
      setActiveQuery({ q: searchCase.trim(), type: "case" });
      setSearchAccused(""); // Clear sibling search
    }
  };

  const handleResetSearch = () => {
    setActiveQuery(null);
    setSearchAccused("");
    setSearchCase("");
    setSelectedNode(null);
    setSelectedLink(null);
  };

  // Indian Rupee currency formatter
  const formatINR = (value: number) => {
    if (value >= 10000000) {
      return `₹${(value / 10000000).toFixed(2)} Cr`;
    }
    if (value >= 100000) {
      return `₹${(value / 100000).toFixed(2)} Lakhs`;
    }
    return `₹${value.toLocaleString("en-IN")}`;
  };

  return (
    <div className="flex flex-col h-full space-y-6 px-6 py-6">
      {/* Page Header */}
      <div>
        <PageHeader
          title="Financial Crime & Transaction Intelligence"
          subtitle="Discover money laundering networks, circular round-tripping, and shared account anomalies."
        />
      </div>

      {/* Persistent Filters & Search Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 border border-border/60 bg-card/35 backdrop-blur-md rounded-xl p-4 shadow-sm">
        {/* Search Accused Form */}
        <form onSubmit={handleAccusedSearch} className="lg:col-span-4 flex flex-col gap-1.5">
          <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Search Accused</label>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
              <Input
                placeholder="Accused name or ID..."
                value={searchAccused}
                onChange={(e) => setSearchAccused(e.target.value)}
                className="pl-8 h-9 text-xs"
              />
            </div>
            <Button type="submit" size="sm" className="h-9 gap-1.5 text-xs">
              Search
            </Button>
          </div>
        </form>

        {/* Search Case Form */}
        <form onSubmit={handleCaseSearch} className="lg:col-span-4 flex flex-col gap-1.5">
          <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Search FIR / Case No</label>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <FileText className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
              <Input
                placeholder="FIR / Case number..."
                value={searchCase}
                onChange={(e) => setSearchCase(e.target.value)}
                className="pl-8 h-9 text-xs"
              />
            </div>
            <Button type="submit" size="sm" className="h-9 gap-1.5 text-xs">
              Search
            </Button>
          </div>
        </form>

        {/* Filter District */}
        <div className="lg:col-span-4 flex flex-col gap-1.5">
          <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Filter District</label>
          <select
            value={district}
            onChange={(e) => setDistrict(e.target.value)}
            className="w-full bg-background/50 border border-border rounded-lg text-xs px-2.5 py-1.5 h-9 focus:outline-none focus:ring-1 focus:ring-primary text-foreground"
          >
            {DISTRICTS.map((d) => (
              <option key={d} value={d}>
                {d === "All" ? "All Districts" : d}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* STATE A: LANDING PAGE — Discovery Recommendations */}
      {!activeQuery ? (
        <div className="flex-1 flex flex-col space-y-4 animate-in fade-in duration-300">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold tracking-tight">Top Recommended Profiles of Financial Crime</h3>
              <p className="text-xs text-muted-foreground">Highest-risk suspects flagged by transaction anomalies, round-tripping, and laundering volume.</p>
            </div>
            {district !== "All" && (
              <Badge variant="outline" className="text-xs text-primary/80 border-primary/20 bg-primary/5">
                District: {district}
              </Badge>
            )}
          </div>

          {topLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="h-44 rounded-xl border border-border/40 bg-card/20 p-5 flex flex-col justify-between">
                  <Skeleton className="h-5 w-2/3" />
                  <Skeleton className="h-3 w-1/2" />
                  <Skeleton className="h-10 w-full" />
                </div>
              ))}
            </div>
          ) : !topSuspects || topSuspects.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center border border-dashed border-border rounded-xl p-12 text-center bg-card/10">
              <AlertTriangle className="h-8 w-8 text-muted-foreground mb-3" />
              <p className="text-sm font-medium">No high-risk suspects flagged</p>
              <p className="text-xs text-muted-foreground mt-1 max-w-sm">No suspicious financial transactions recorded in the selected district filter.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {topSuspects.map((suspect) => {
                // Determine risk color
                let riskColor = "bg-emerald-500/10 text-emerald-500 border-emerald-500/20";
                if (suspect.risk_score >= 0.8) {
                  riskColor = "bg-red-500/10 text-red-500 border-red-500/20";
                } else if (suspect.risk_score >= 0.6) {
                  riskColor = "bg-amber-500/10 text-amber-500 border-amber-500/20";
                }

                return (
                  <Card
                    key={suspect.person_id}
                    onClick={() => {
                      setSearchAccused(suspect.accused_name);
                      setActiveQuery({ q: suspect.person_id, type: "accused" });
                    }}
                    className="relative group cursor-pointer border-border/60 bg-card/40 hover:bg-card/75 transition-all duration-300 hover:shadow-md hover:border-primary/30 rounded-xl"
                  >
                    <CardHeader className="pb-3 flex flex-row items-start justify-between space-y-0">
                      <div>
                        <CardTitle className="text-sm font-semibold flex items-center gap-1.5 group-hover:text-primary transition-colors">
                          <User className="h-4 w-4 text-muted-foreground group-hover:text-primary/70" />
                          {suspect.accused_name}
                        </CardTitle>
                        <span className="text-[10px] font-mono text-muted-foreground mt-1 block">ID: {suspect.person_id}</span>
                      </div>
                      <Badge variant="outline" className={`${riskColor} font-mono px-2 py-0.5 text-[10px] tracking-wider uppercase font-semibold`}>
                        Risk {Math.round(suspect.risk_score * 100)}%
                      </Badge>
                    </CardHeader>
                    <CardContent className="pb-4 space-y-3">
                      {/* Stats Grid */}
                      <div className="grid grid-cols-2 gap-2 text-xs border-t border-border/50 pt-2">
                        <div>
                          <span className="text-[10px] text-muted-foreground uppercase block font-medium">Laundering Volume</span>
                          <span className="font-semibold text-foreground text-xs mt-0.5 block">{formatINR(suspect.total_suspicious_amount)}</span>
                        </div>
                        <div>
                          <span className="text-[10px] text-muted-foreground uppercase block font-medium">District</span>
                          <span className="font-semibold text-foreground text-xs mt-0.5 block truncate">{suspect.district}</span>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-2 text-xs pt-1">
                        <div>
                          <span className="text-[10px] text-muted-foreground uppercase block font-medium">Suspicious Tx</span>
                          <span className="font-semibold text-foreground text-xs mt-0.5 block">{suspect.suspicious_tx_count} transfers</span>
                        </div>
                        <div>
                          <span className="text-[10px] text-muted-foreground uppercase block font-medium">Related Cases</span>
                          <span className="font-semibold text-foreground text-xs mt-0.5 block">{suspect.case_count} cases</span>
                        </div>
                      </div>

                      {/* Action hover button */}
                      <div className="text-[10px] font-semibold text-primary/80 group-hover:text-primary mt-2 flex items-center justify-end gap-1 transition-all">
                        <span>Investigate Transaction Network</span>
                        <span className="transition-transform group-hover:translate-x-1">→</span>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      ) : (
        /* STATE B: GRAPH VISUALIZATION MODE */
        <div className="flex-1 flex flex-col space-y-4 animate-in fade-in duration-300 min-h-0">
          {/* Back Button & Details header */}
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={handleResetSearch}
              className="gap-2 h-8 text-xs font-medium"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              Back to Suspect List
            </Button>
            <div className="h-6 w-[1px] bg-border" />
            <div>
              <h3 className="text-xs font-semibold">
                Network Centered On: <span className="text-primary">"{activeQuery.q}"</span>
              </h3>
              <p className="text-[10px] text-muted-foreground">Showing linked accounts, case associations, and transaction directions.</p>
            </div>
          </div>

          <div className="flex-1 flex flex-col lg:flex-row gap-4 relative min-h-0">
            {/* Graph Canvas */}
            <div
              className="flex-1 relative border border-border/80 bg-muted/15 rounded-xl min-h-[450px] overflow-hidden"
              ref={containerRef}
            >
              {graphLoading ? (
                <div className="absolute inset-0 flex flex-col items-center justify-center bg-background/50 z-20">
                  <Skeleton className="h-full w-full absolute inset-0" />
                  <span className="text-xs text-muted-foreground z-30 font-medium animate-pulse">Assembling transaction graph...</span>
                </div>
              ) : !graphData || graphData.nodes.length === 0 ? (
                <div className="absolute inset-0 flex flex-col items-center justify-center p-8 text-center">
                  <AlertTriangle className="h-8 w-8 text-muted-foreground mb-2" />
                  <p className="text-sm font-semibold">No Network Matches</p>
                  <p className="text-xs text-muted-foreground max-w-sm mt-1">
                    No related case transactions or accused ownership records match the query.
                  </p>
                </div>
              ) : (
                <Suspense fallback={<Skeleton className="absolute inset-0" />}>
                  <ForceGraph2D
                    ref={graphRef}
                    graphData={graphData}
                    width={dims.w}
                    height={dims.h}
                    minZoom={0.15}
                    maxZoom={10}
                    linkColor={(l: any) => (l.suspicious ? SUSPICIOUS_COLOR : NORMAL_LINK)}
                    linkWidth={(l: any) => (l.suspicious ? 2 : 1)}
                    linkDirectionalArrowLength={(l: any) => (l.suspicious ? 4 : 0)}
                    linkDirectionalArrowRelPos={1}
                    nodeLabel={(n: any) =>
                      n.kind === "account" ? `${n.label} · ${n.metadata?.bank || "Unknown Bank"}` : `${n.label} · ${n.kind}`
                    }
                    onNodeClick={(n: any) => {
                      setSelectedNode(n);
                      setSelectedLink(null);
                    }}
                    onLinkClick={(l: any) => {
                      setSelectedLink(l);
                      setSelectedNode(null);
                    }}
                    cooldownTicks={120}
                    nodeCanvasObject={(node: any, ctx, globalScale) => {
                      const label = node.label || node.id;
                      const val = node.val || 8;
                      const r = Math.sqrt(val) * 2.5;

                      // Highlight selected node
                      if (selectedNode && selectedNode.id === node.id) {
                        ctx.beginPath();
                        ctx.arc(node.x, node.y, r + 4, 0, 2 * Math.PI, false);
                        ctx.fillStyle = "rgba(59, 130, 246, 0.45)";
                        ctx.fill();
                      }

                      // Main node circle
                      ctx.beginPath();
                      ctx.arc(node.x, node.y, r, 0, 2 * Math.PI, false);
                      ctx.fillStyle = node.color || COLORS[node.kind] || '#888';
                      ctx.fill();

                      // Node border
                      ctx.strokeStyle = '#ffffff';
                      ctx.lineWidth = 1.2 / globalScale;
                      ctx.stroke();

                      // Text labels
                      const fontSize = Math.max(3.5, 9 / globalScale);
                      ctx.font = `600 ${fontSize}px sans-serif`;
                      ctx.textAlign = 'center';
                      ctx.textBaseline = 'top';

                      const isDark = document.documentElement.classList.contains('dark');
                      ctx.fillStyle = isDark ? '#f1f5f9' : '#0f172a';
                      
                      // Draw text label slightly below the node
                      ctx.fillText(label, node.x, node.y + r + 2);
                    }}
                    nodePointerAreaPaint={(node: any, color, ctx) => {
                      const val = node.val || 8;
                      const r = Math.sqrt(val) * 2.5 + 8; // Extra padding for easy clicks
                      ctx.beginPath();
                      ctx.arc(node.x, node.y, r, 0, 2 * Math.PI, false);
                      ctx.fillStyle = color;
                      ctx.fill();
                    }}
                  />
                </Suspense>
              )}

              {/* Float A: Intelligence alerts panel */}
              {graphData?.patterns && (
                <div className="absolute top-3 left-3 z-10 w-72 rounded-xl bg-background/90 border border-border/80 shadow-lg p-3 max-h-[220px] overflow-y-auto backdrop-blur-md">
                  <div className="text-[10px] font-bold text-primary uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <ShieldAlert className="h-3.5 w-3.5 text-primary" />
                    Financial Intelligence Alerts
                  </div>

                  {graphData.patterns.circular_flows?.length > 0 ? (
                    <div className="space-y-1.5 mb-3">
                      <div className="text-[9px] font-bold text-destructive uppercase tracking-wide">
                        Circular Flows ({graphData.patterns.circular_flows.length})
                      </div>
                      {graphData.patterns.circular_flows.map((c: any, i: number) => (
                        <div key={i} className="text-[9px] bg-red-500/10 border border-red-500/20 text-red-600 dark:text-red-400 rounded p-1.5 leading-relaxed font-semibold font-mono">
                          {c.flow}
                        </div>
                      ))}
                    </div>
                  ) : null}

                  {graphData.patterns.shared_accounts?.length > 0 ? (
                    <div className="space-y-1.5">
                      <div className="text-[9px] font-bold text-warning uppercase tracking-wide">
                        Shared Accounts ({graphData.patterns.shared_accounts.length})
                      </div>
                      {graphData.patterns.shared_accounts.map((s: any, i: number) => (
                        <div key={i} className="text-[9px] bg-amber-500/10 border border-amber-500/20 text-amber-800 dark:text-amber-300 rounded p-1.5 leading-normal">
                          <strong>{s.label}</strong> shared by:
                          <div className="text-[8px] text-muted-foreground mt-0.5">
                            {s.owners.join(", ")}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : null}

                  {graphData.patterns.circular_flows?.length === 0 && graphData.patterns.shared_accounts?.length === 0 && (
                    <div className="text-[9px] text-muted-foreground">
                      No laundering cycles or shared accounts detected in current scope.
                    </div>
                  )}
                </div>
              )}

              {/* Float B: Legend */}
              <div className="absolute bottom-3 left-3 rounded-xl bg-background/90 border border-border/80 backdrop-blur-md p-3 text-[10px] shadow-lg">
                <div className="text-[9px] uppercase tracking-wider text-muted-foreground mb-1.5 font-bold">
                  Node Legend
                </div>
                <div className="space-y-1.5">
                  {Object.entries(COLORS).map(([k, c]) => (
                    <div key={k} className="flex items-center gap-2 capitalize font-medium">
                      <span className="h-2.5 w-2.5 rounded-full" style={{ background: c }} />
                      {k}
                    </div>
                  ))}
                  <div className="flex items-center gap-2 pt-1.5 border-t border-border mt-1.5">
                    <span className="h-0.5 w-5" style={{ background: SUSPICIOUS_COLOR }} />
                    Suspicious Transaction
                  </div>
                </div>
              </div>

              {/* Float C: Zoom Controls */}
              <div className="absolute bottom-3 right-3 flex flex-col gap-1">
                <Button
                  size="icon"
                  variant="outline"
                  className="h-8 w-8 bg-background/90 border border-border"
                  onClick={() => graphRef.current?.zoom((graphRef.current?.zoom() ?? 1) * 1.4, 300)}
                >
                  <ZoomIn className="h-3.5 w-3.5" />
                </Button>
                <Button
                  size="icon"
                  variant="outline"
                  className="h-8 w-8 bg-background/90 border border-border"
                  onClick={() => graphRef.current?.zoom((graphRef.current?.zoom() ?? 1) / 1.4, 300)}
                >
                  <ZoomOut className="h-3.5 w-3.5" />
                </Button>
                <Button
                  size="icon"
                  variant="outline"
                  className="h-8 w-8 bg-background/90 border border-border"
                  onClick={() => graphRef.current?.zoomToFit(400)}
                >
                  <Maximize2 className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>

            {/* Side Information Panel */}
            {selectedNode && (
              <aside className="w-full lg:w-72 border border-border/80 bg-background/90 backdrop-blur-md rounded-xl p-4 shadow-lg animate-in slide-in-from-right duration-200">
                <div className="flex items-start justify-between gap-2 border-b border-border/60 pb-2.5">
                  <div>
                    <span className="text-[9px] uppercase tracking-wider text-primary font-bold">
                      {selectedNode.kind}
                    </span>
                    <h4 className="text-xs font-semibold text-foreground mt-0.5">{selectedNode.label}</h4>
                    <span className="text-[9px] text-muted-foreground font-mono mt-0.5 block">{selectedNode.id}</span>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6 text-muted-foreground hover:text-foreground"
                    onClick={() => setSelectedNode(null)}
                  >
                    <X className="h-3.5 w-3.5" />
                  </Button>
                </div>

                <div className="mt-3.5 space-y-2.5 text-[11px]">
                  {selectedNode.metadata?.bank && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground flex items-center gap-1">
                        <Building2 className="h-3.5 w-3.5 text-muted-foreground/70" /> Bank
                      </span>
                      <span className="font-medium text-foreground">{selectedNode.metadata.bank}</span>
                    </div>
                  )}

                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Direct Links</span>
                    <Badge variant="secondary" className="font-mono text-[9px] py-0 px-1.5">
                      {graphData?.links.filter(
                        (l: any) =>
                          l.source.id === selectedNode.id ||
                          l.source === selectedNode.id ||
                          l.target.id === selectedNode.id ||
                          l.target === selectedNode.id,
                      ).length ?? 0}
                    </Badge>
                  </div>
                </div>
              </aside>
            )}

            {selectedLink && (
              <aside className="w-full lg:w-80 border border-border/80 bg-background/90 backdrop-blur-md rounded-xl p-4 shadow-lg animate-in slide-in-from-right duration-200">
                <div className="flex items-start justify-between gap-2 border-b border-border/60 pb-2.5">
                  <div>
                    <span className="text-[9px] uppercase tracking-wider text-primary font-bold">
                      Transaction Info
                    </span>
                    <h4 className="text-xs font-semibold text-foreground mt-0.5">
                      {selectedLink.source?.label ?? selectedLink.source}
                      <span className="text-muted-foreground mx-1">→</span>
                      {selectedLink.target?.label ?? selectedLink.target}
                    </h4>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6 text-muted-foreground hover:text-foreground"
                    onClick={() => setSelectedLink(null)}
                  >
                    <X className="h-3.5 w-3.5" />
                  </Button>
                </div>

                <div className="mt-3.5 space-y-2.5 text-[11px]">
                  {selectedLink.amount !== undefined && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Amount</span>
                      <span className="tabular-nums font-bold text-foreground">
                        ₹{selectedLink.amount.toLocaleString("en-IN")}
                      </span>
                    </div>
                  )}

                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Severity Status</span>
                    {selectedLink.suspicious ? (
                      <Badge className="bg-destructive/10 text-destructive border-destructive/20 text-[9px] font-semibold py-0.5">
                        Suspicious Anomaly
                      </Badge>
                    ) : (
                      <Badge variant="secondary" className="text-[9px] font-semibold py-0.5">
                        Normal Transfer
                      </Badge>
                    )}
                  </div>

                  {selectedLink.reason && (
                    <div className="pt-2 border-t border-border/60 mt-2">
                      <span className="text-muted-foreground block mb-1">Flag Reason</span>
                      <p className="text-foreground leading-relaxed bg-muted/30 border border-border/40 p-2 rounded text-[10px]">
                        {selectedLink.reason}
                      </p>
                    </div>
                  )}
                </div>
              </aside>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

