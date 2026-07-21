/* eslint-disable */
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useRef, useState, lazy, Suspense } from "react";
import { useQuery } from "@tanstack/react-query";
import { PageHeader } from "@/components/app/primitives";
import { getNetwork, getNetworkExpansion } from "@/services/api";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useRBAC } from "@/hooks/useRBAC";
import {
  X,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Search,
  Award,
  Radio,
  MapPin,
  Users,
  History,
  ShieldAlert,
  ChevronRight,
  User,
  FileText
} from "lucide-react";

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

const DEFAULT_COLORS: Record<string, string> = {
  accused: "#1F3864",
  victim: "#2AA198",
  location: "#D4A017",
  case: "#6B7280",
};

function NetworkPage() {
  const navigate = useNavigate({ from: Route.fullPath });
  const filters = Route.useSearch();
  const rbac = useRBAC();
  const { user } = rbac;
  // Roles that see aggregated/all-district data: Analyst, Policy Maker, Supervisor, Administrator
  // (i.e., roles that do not have ABAC-scoped district assignments for investigative data)
  const isSuperOrAdmin =
    user?.role === "SUPERVISOR" ||
    user?.role === "ANALYST" ||
    user?.role === "POLICY_MAKER" ||
    user?.role === "ADMINISTRATOR";
  const userDistricts = user?.assignedDistricts ?? [];

  const { data, isLoading } = useQuery({
    queryKey: ["network", filters],
    queryFn: () => getNetwork(filters),
  });

  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<any>(null);
  const [dims, setDims] = useState({ w: 800, h: 600 });
  const [selected, setSelected] = useState<any>(null);
  const [q, setQ] = useState(filters.focusId || "");
  const [minWeight, setMinWeight] = useState(5);
  const [recent, setRecent] = useState<any[]>([]);
  const [graphState, setGraphState] = useState<{ nodes: any[]; links: any[] }>({ nodes: [], links: [] });
  const [isExpanding, setIsExpanding] = useState(false);

  // Form search states
  const [searchAccused, setSearchAccused] = useState("");
  const [searchCase, setSearchCase] = useState("");
  const [selDistrict, setSelDistrict] = useState("");

  // Check if we are in dashboard mode (Level 1) or workspace mode (Level 2)
  const isWorkspace = !!(filters.focusId || filters.district || filters.crimeType || filters.policeStation);

  useEffect(() => {
    if (filters.focusId) {
      setQ(filters.focusId);
    }
  }, [filters.focusId]);

  useEffect(() => {
    const stored = localStorage.getItem("recent_investigations");
    if (stored) {
      setRecent(JSON.parse(stored));
    }
  }, []);

  useEffect(() => {
    if (!containerRef.current) return;
    const ro = new ResizeObserver(() => {
      const r = containerRef.current!.getBoundingClientRect();
      const newW = Math.round(r.width);
      const newH = Math.round(r.height);
      setDims((prev) => {
        // Only trigger dimensions state updates if they differ by more than 2px
        // to filter out sub-pixel layout jitter during scrolling and zooming.
        if (Math.abs(prev.w - newW) > 2 || Math.abs(prev.h - newH) > 2) {
          return { w: newW, h: newH };
        }
        return prev;
      });
    });
    ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, []);


  useEffect(() => {
    if (graphRef.current) {
      const fg = graphRef.current;
      fg.d3Force("charge")?.strength(-180);
      fg.d3Force("link")?.distance(70)?.strength(0.25);
    }
  }, [graphState, graphRef.current]);

  // Sync graph state from loaded query data
  useEffect(() => {
    if (data?.nodes && data?.links) {
      setGraphState({
        nodes: [...data.nodes],
        links: [...data.links]
      });
      // Zoom to fit on initial filters / search load
      setTimeout(() => {
        graphRef.current?.zoomToFit(400, 80);
      }, 500);
    } else {
      setGraphState({ nodes: [], links: [] });
    }
  }, [data]);


  const addToRecent = (target: string, type: string) => {
    const item = { target, type, timestamp: new Date().toLocaleTimeString() };
    setRecent((prev) => {
      const filtered = prev.filter((i) => i.target !== target);
      const updated = [item, ...filtered].slice(0, 5);
      localStorage.setItem("recent_investigations", JSON.stringify(updated));
      return updated;
    });
  };

  const handleStartInvestigation = (target: string, type: string) => {
    addToRecent(target, type);
    navigate({
      search: () => {
        if (type === "accused") return { focusId: target };
        if (type === "case") return { focusId: target };
        if (type === "district") return { district: target };
        return {};
      }
    });
  };

  // Lazy-load neighbors (Level 3 Expansion)
  const handleExpandNode = async (nodeId: string, kind: string) => {
    setIsExpanding(true);
    try {
      const res = await getNetworkExpansion(nodeId, kind);
      if (res && res.nodes) {
        setGraphState((prev) => {
          const existingNodeIds = new Set(prev.nodes.map((n) => n.id));
          const newNodes = res.nodes.filter((n: any) => !existingNodeIds.has(n.id));

          const existingLinkKeys = new Set(
            prev.links.map((l) => {
              const s = typeof l.source === "object" ? l.source.id : l.source;
              const t = typeof l.target === "object" ? l.target.id : l.target;
              return `${s}-${t}`;
            })
          );

          const newLinks = res.links.filter((l: any) => {
            const s = typeof l.source === "object" ? l.source.id : l.source;
            const t = typeof l.target === "object" ? l.target.id : l.target;
            const key = `${s}-${t}`;
            const revKey = `${t}-${s}`;
            return !existingLinkKeys.has(key) && !existingLinkKeys.has(revKey);
          });

          return {
            nodes: [...prev.nodes, ...newNodes],
            links: [...prev.links, ...newLinks],
          };
        });
      }
    } catch (err) {
      console.error("Error expanding node:", err);
    } finally {
      setIsExpanding(false);
    }
  };

  // Filter links by slider value, and prune disconnected nodes
  const filteredLinks = graphState.links.filter((l: any) => {
    const w = l.weight ?? 5.0;
    return w >= minWeight;
  });

  const activeNodeIds = new Set();
  filteredLinks.forEach((l: any) => {
    const s = typeof l.source === "object" ? l.source.id : l.source;
    const t = typeof l.target === "object" ? l.target.id : l.target;
    activeNodeIds.add(s);
    activeNodeIds.add(t);
  });

  // Always keep the center node or the focused node even if it has no strong links
  if (data?.center_node) {
    activeNodeIds.add(data.center_node);
  }

  const filteredNodes = graphState.nodes.filter((n: any) => activeNodeIds.has(n.id));

  const renderedGraphData = {
    nodes: filteredNodes,
    links: filteredLinks,
  };

  return (
    <div className="flex flex-col min-h-full bg-background text-foreground">

      <div className="px-6 pt-6 border-b border-border pb-4 bg-background/40">
        <PageHeader
          title="Criminal Intelligence Network"
          subtitle="Workspace for co-offending links, Modularity gang clustering, and visual tracing."
          actions={
            <div className="flex items-center gap-3">
              {isWorkspace && (
                <>
                  {/* Slider control */}
                  <div className="flex flex-col gap-1 w-44 bg-background/60 p-2 rounded-lg border border-border">
                    <div className="flex justify-between text-[10px] text-muted-foreground font-bold uppercase tracking-wider">
                      <span>Min Link Weight</span>
                      <span className="text-primary font-mono">{minWeight}</span>
                    </div>
                    <input
                      type="range"
                      min="1"
                      max="10"
                      value={minWeight}
                      onChange={(e) => setMinWeight(parseInt(e.target.value))}
                      className="w-full h-1 bg-border rounded-lg appearance-none cursor-pointer accent-primary"
                    />
                  </div>

                  {/* Reset view */}
                  <Button
                    size="sm"
                    variant="outline"
                    className="border-border hover:bg-muted"
                    onClick={() => {
                      setQ("");
                      navigate({ search: () => ({}) });
                    }}
                    title="Close active investigation"
                  >
                    <X className="h-4 w-4 mr-2" />
                    Close
                  </Button>
                </>
              )}
            </div>
          }
        />

        {isWorkspace && data?.summary && (
          <div className="mt-3 rounded-xl border border-primary/25 bg-primary/5 p-4 text-xs leading-relaxed text-foreground shadow-sm animate-in fade-in duration-300">
            <div className="font-semibold text-primary mb-1 uppercase tracking-wider text-[10px] flex items-center gap-1.5">
              <ShieldAlert className="h-3.5 w-3.5 text-primary" />
              AI Intelligence Briefing
            </div>
            {data.summary}
          </div>
        )}
      </div>

      <div className="flex-1 relative flex">

        {!isWorkspace ? (
          /* Level 1 Dashboard View */
          <div className="flex-1 overflow-y-auto p-6 max-w-[1600px] mx-auto w-full space-y-6 animate-in fade-in duration-300">
            {/* Top row: Target Configurator */}
            <div className="rounded-xl glass border border-border p-6 shadow-sm relative overflow-hidden bg-card text-card-foreground">
              <h2 className="text-xs font-bold text-muted-foreground uppercase tracking-widest mb-4 flex items-center gap-2">
                <Search className="h-4 w-4 text-primary" />
                Target Configurator (Investigation Mode)
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Search accused */}
                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-muted-foreground uppercase">Search Accused</label>
                  <div className="flex gap-2">
                    <div className="relative flex-1">
                      <User className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
                      <Input
                        placeholder="Accused name or ID..."
                        value={searchAccused}
                        onChange={(e) => setSearchAccused(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" && searchAccused.trim()) {
                            handleStartInvestigation(searchAccused.trim(), "accused");
                          }
                        }}
                        className="bg-background/50 border-border text-xs h-8 pl-8"
                      />
                    </div>
                    <Button
                      size="sm"
                      className="bg-primary text-primary-foreground hover:opacity-90 h-8 px-4"
                      onClick={() => {
                        if (searchAccused.trim()) {
                          handleStartInvestigation(searchAccused.trim(), "accused");
                        }
                      }}
                    >
                      Search
                    </Button>
                  </div>
                </div>

                {/* Search Case */}
                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-muted-foreground uppercase">Search FIR / Case No</label>
                  <div className="flex gap-2">
                    <div className="relative flex-1">
                      <FileText className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
                      <Input
                        placeholder="FIR / Case number..."
                        value={searchCase}
                        onChange={(e) => setSearchCase(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" && searchCase.trim()) {
                            handleStartInvestigation(searchCase.trim(), "case");
                          }
                        }}
                        className="bg-background/50 border-border text-xs h-8 pl-8"
                      />
                    </div>
                    <Button
                      size="sm"
                      className="bg-primary text-primary-foreground hover:opacity-90 h-8 px-4"
                      onClick={() => {
                        if (searchCase.trim()) {
                          handleStartInvestigation(searchCase.trim(), "case");
                        }
                      }}
                    >
                      Search
                    </Button>
                  </div>
                </div>

                {/* Geographic & Crime Type Filters */}
                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-muted-foreground uppercase">Filter District</label>
                  <div className="flex gap-2">
                    <select
                      value={selDistrict}
                      onChange={(e) => {
                        setSelDistrict(e.target.value);
                        if (e.target.value && e.target.value !== "All") {
                          handleStartInvestigation(e.target.value, "district");
                        }
                      }}
                      className="w-full bg-background/50 border border-border rounded-lg text-xs px-2.5 py-1.5 h-8 focus:outline-none focus:ring-1 focus:ring-primary text-foreground"
                    >
                      <option value="">Select District…</option>
                      {isSuperOrAdmin && <option value="All">All Districts</option>}
                      {isSuperOrAdmin ? (
                        <>
                          <option value="Mysuru">Mysuru</option>
                          <option value="Bengaluru Urban">Bengaluru Urban</option>
                          <option value="Bengaluru Rural">Bengaluru Rural</option>
                          <option value="Mangaluru">Mangaluru</option>
                        </>
                      ) : (
                        userDistricts.map((d) => (
                          <option key={d} value={d}>{d}</option>
                        ))
                      )}
                    </select>
                  </div>
                </div>
              </div>
            </div>

            {/* Middle row: KPIs & Statistics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="rounded-xl glass border border-border p-4 shadow-sm bg-card text-card-foreground">
                <div className="flex justify-between items-start">
                  <div>
                    <span className="text-[10px] text-muted-foreground font-bold uppercase">Most Connected Criminal</span>
                    <h3 className="text-xs font-bold mt-1 text-foreground">
                      {data?.most_connected?.[0] || "None Identified"}
                    </h3>
                  </div>
                  <Award className="h-4 w-4 text-amber-500" />
                </div>
              </div>

              <div className="rounded-xl glass border border-border p-4 shadow-sm bg-card text-card-foreground">
                <div className="flex justify-between items-start">
                  <div>
                    <span className="text-[10px] text-muted-foreground font-bold uppercase">Connected PS</span>
                    <h3 className="text-xs font-bold mt-1 text-foreground">
                      {data?.most_connected_police_station || "None"}
                    </h3>
                  </div>
                  <MapPin className="h-4 w-4 text-blue-500" />
                </div>
              </div>

              <div className="rounded-xl glass border border-border p-4 shadow-sm bg-card text-card-foreground">
                <div className="flex justify-between items-start">
                  <div>
                    <span className="text-[10px] text-muted-foreground font-bold uppercase">Communities Detected</span>
                    <h3 className="text-xs font-bold mt-1 text-foreground">
                      {data?.communities?.length || 0} gang clusters
                    </h3>
                  </div>
                  <Users className="h-4 w-4 text-teal-500" />
                </div>
              </div>

              <div className="rounded-xl glass border border-border p-4 shadow-sm bg-card text-card-foreground">
                <div className="flex justify-between items-start">
                  <div>
                    <span className="text-[10px] text-muted-foreground font-bold uppercase">Density Ratio</span>
                    <h3 className="text-xs font-bold mt-1 text-foreground font-mono">
                      {data?.density || "0.00"}
                    </h3>
                  </div>
                  <Radio className="h-4 w-4 text-purple-500" />
                </div>
              </div>
            </div>

            {/* Splits: Left - Repeat Offenders, Right - Communities & History */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Left Column: Top Repeat Offenders */}
              <div className="lg:col-span-2 rounded-xl glass border border-border p-6 shadow-sm bg-card text-card-foreground">
                <h3 className="text-xs font-bold uppercase tracking-wider text-foreground mb-4 flex items-center gap-2 border-b border-border pb-2">
                  <Award className="h-4 w-4 text-red-500" />
                  Top Repeat Offenders (High Priority)
                </h3>
                {isLoading ? (
                  <div className="space-y-3">
                    <Skeleton className="h-10 w-full" />
                    <Skeleton className="h-10 w-full" />
                    <Skeleton className="h-10 w-full" />
                  </div>
                ) : (
                  <div className="divide-y divide-border max-h-[380px] overflow-y-auto pr-1">
                    {data?.repeat_offenders?.map((off: any) => (
                      <div key={off.id} className="py-3 flex justify-between items-center group">
                        <div className="space-y-1">
                          <div className="text-xs font-semibold text-foreground group-hover:text-primary transition-colors">
                            {off.name}
                          </div>
                          <div className="text-[10px] text-muted-foreground flex items-center gap-2">
                            <span>{off.crime_count} Cases</span>
                            <span>·</span>
                            <span>{off.known_associates?.length || 0} Associates</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="text-right">
                            <div className="text-[10px] font-bold text-muted-foreground">RISK SCORE</div>
                            <div className={`text-xs font-mono font-bold ${off.risk_score > 70 ? 'text-red-500' : 'text-amber-500'}`}>
                              {off.risk_score}%
                            </div>
                          </div>
                          <Button
                            size="sm"
                            className="bg-primary text-primary-foreground hover:opacity-90 text-[10px] h-7 px-3"
                            onClick={() => handleStartInvestigation(off.id, "accused")}
                          >
                            Investigate
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Right Column: Gang Communities & History */}
              <div className="space-y-6">
                {/* Gang Communities */}
                <div className="rounded-xl glass border border-border p-6 shadow-sm bg-card text-card-foreground">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-foreground mb-4 flex items-center gap-2 border-b border-border pb-2">
                    <Users className="h-4 w-4 text-teal-500" />
                    Top Crime Gangs
                  </h3>
                  <div className="space-y-3">
                    {data?.communities?.slice(0, 3).map((comm: any) => (
                      <div
                        key={comm.community_id}
                        className="bg-muted/50 p-3 rounded-xl border border-border flex justify-between items-center hover:border-muted-foreground/30 transition-colors"
                      >
                        <div className="space-y-1">
                          <span className="text-[9px] font-bold text-teal-600 dark:text-teal-400 uppercase tracking-widest">
                            Gang #{comm.community_id}
                          </span>
                          <div className="text-xs font-semibold text-foreground">
                            Leader: {comm.leader}
                          </div>
                          <div className="text-[9px] text-muted-foreground">
                            {comm.members?.length || 0} Members
                          </div>
                        </div>
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-8 w-8 hover:bg-muted"
                          onClick={() => handleStartInvestigation(comm.leader, "accused")}
                        >
                          <ChevronRight className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>

                {/* History */}
                {recent.length > 0 && (
                  <div className="rounded-xl glass border border-border p-6 shadow-sm bg-card text-card-foreground">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-foreground mb-3 flex items-center gap-2 border-b border-border pb-2">
                      <History className="h-4 w-4 text-purple-500" />
                      Recent Investigations
                    </h3>
                    <div className="space-y-2">
                      {recent.map((rec: any, idx: number) => (
                        <div
                          key={idx}
                          className="text-[10px] bg-muted/30 hover:bg-muted p-2.5 rounded-lg border border-border flex justify-between items-center cursor-pointer"
                          onClick={() => handleStartInvestigation(rec.target, rec.type)}
                        >
                          <div>
                            <span className="font-semibold text-foreground">{rec.target}</span>
                            <span className="text-muted-foreground ml-1.5 capitalize font-mono">({rec.type})</span>
                          </div>
                          <span className="text-[9px] text-muted-foreground">{rec.timestamp}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ) : (
          /* Level 2 Workspace View */
          <div className="w-full h-[650px] min-h-[600px] relative flex border-t border-border bg-muted/30 mt-4" ref={containerRef}>

            {data?.focus_reason && (
              <div className="absolute top-4 left-4 z-10 rounded-xl bg-card border border-border shadow-md p-2.5 text-xs text-foreground flex items-center gap-2 animate-in fade-in duration-200">
                <span className="font-semibold text-primary">Workspace Focus:</span>
                <span>{data.focus_reason}</span>
                <button
                  onClick={() => {
                    setQ("");
                    navigate({ search: () => ({}) });
                  }}
                  className="text-muted-foreground hover:text-foreground ml-2 p-0.5 rounded-full hover:bg-muted"
                  title="Close target"
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
                  graphData={renderedGraphData}
                  width={dims.w}
                  height={dims.h}
                  minZoom={0.15}
                  maxZoom={10}
                  linkColor={() => "rgba(148,163,184,0.15)"}
                  linkWidth={(l: any) => Math.sqrt(l.weight || 1) * 0.75}
                  nodeLabel={(n: any) => `${n.label} · ${n.kind}`}
                  onNodeClick={(n: any) => {
                    setSelected(n);
                    graphRef.current?.centerAt(n.x, n.y, 300);
                  }}
                  cooldownTicks={120}
                  nodeCanvasObject={(node: any, ctx, globalScale) => {
                    const label = node.label || node.id;
                    const val = node.val || 5;
                    const r = Math.sqrt(val) * 2.5;
                    
                    // Highlight selected node
                    if (selected && selected.id === node.id) {
                      ctx.beginPath();
                      ctx.arc(node.x, node.y, r + 4, 0, 2 * Math.PI, false);
                      ctx.fillStyle = "rgba(59, 130, 246, 0.45)";
                      ctx.fill();
                    }

                    // Main node circle
                    ctx.beginPath();
                    ctx.arc(node.x, node.y, r, 0, 2 * Math.PI, false);
                    ctx.fillStyle = node.color || DEFAULT_COLORS[node.kind] || '#6B7280';
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
                    const val = node.val || 5;
                    const r = Math.sqrt(val) * 2.5 + 8; // Extra padding for easy clicks
                    ctx.beginPath();
                    ctx.arc(node.x, node.y, r, 0, 2 * Math.PI, false);
                    ctx.fillStyle = color;
                    ctx.fill();
                  }}
                />
              </Suspense>
            )}

            {/* Legend */}
            <div className="absolute bottom-4 left-4 rounded-xl bg-card border border-border p-3.5 text-[10px] shadow-md text-foreground">
              <div className="text-[9px] uppercase tracking-wider text-muted-foreground mb-2 font-bold">
                Entity Legend
              </div>
              <div className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ background: "#EF4444" }} />
                  <span>Repeat Offender</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ background: "#F97316" }} />
                  <span>Community Leader</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ background: "#10B981" }} />
                  <span>Victim</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ background: "#3B82F6" }} />
                  <span>Police Station</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ background: "#8B5CF6" }} />
                  <span>Financial Account</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ background: "#64748B" }} />
                  <span>Case</span>
                </div>
              </div>
            </div>

            {/* Zoom controls */}
            <div className="absolute bottom-4 right-4 flex flex-col gap-1.5 z-10">
              <Button
                size="icon"
                variant="outline"
                className="h-8 w-8 bg-background border-border hover:bg-muted text-foreground"
                onClick={() => graphRef.current?.zoom((graphRef.current?.zoom() ?? 1) * 1.4, 300)}
                title="Zoom In"
              >
                <ZoomIn className="h-4 w-4" />
              </Button>
              <Button
                size="icon"
                variant="outline"
                className="h-8 w-8 bg-background border-border hover:bg-muted text-foreground"
                onClick={() => graphRef.current?.zoom((graphRef.current?.zoom() ?? 1) / 1.4, 300)}
                title="Zoom Out"
              >
                <ZoomOut className="h-4 w-4" />
              </Button>
              <Button
                size="icon"
                variant="outline"
                className="h-8 w-8 bg-background border-border hover:bg-muted text-foreground"
                onClick={() => {
                  graphRef.current?.zoomToFit(400, 80);
                }}
                title="Fit to Screen"
              >
                <Maximize2 className="h-4 w-4" />
              </Button>
            </div>


            {/* Side panel for node details (Level 3 Expansion) */}
            {selected && (
              <aside className="absolute top-4 right-4 w-76 rounded-xl bg-card border border-border shadow-lg p-4 animate-in slide-in-from-right duration-200 text-foreground">
                <div className="flex items-start justify-between gap-2 border-b border-border pb-2.5">
                  <div>
                    <div className="text-[9px] uppercase tracking-wider text-primary font-bold">
                      {selected.kind}
                    </div>
                    <div className="text-sm font-semibold">{selected.label}</div>
                    <div className="text-[10px] text-muted-foreground font-mono mt-0.5">{selected.id}</div>
                  </div>
                  <button
                    onClick={() => setSelected(null)}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>

                <div className="mt-3.5 space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Total Connections</span>
                    <Badge variant="secondary">
                      {data?.links.filter(
                        (l: any) =>
                          l.source.id === selected.id ||
                          l.source === selected.id ||
                          l.target.id === selected.id ||
                          l.target === selected.id
                      ).length ?? 0}
                    </Badge>
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
                                  className={`text-[9px] font-bold ${ro.risk_score > 70
                                      ? "bg-red-50 dark:bg-red-950 text-red-650 dark:text-red-400 border border-red-500/20"
                                      : "bg-muted text-foreground"
                                    }`}
                                >
                                  {ro.risk_score} / 100
                                </Badge>
                              </div>
                              {ro.cases && ro.cases.length > 0 && (
                                <div className="pt-2 border-t border-border mt-2">
                                  <div className="text-muted-foreground mb-1 text-[9px] font-bold uppercase">
                                    Cases ({ro.cases.length})
                                  </div>
                                  <div className="flex flex-wrap gap-1 max-h-24 overflow-y-auto">
                                    {ro.cases.map((c: string) => (
                                      <Badge key={c} variant="outline" className="text-[9px] border-border text-foreground">
                                        {c}
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

                  {selected.kind === "case" && selected.metadata?.brief_facts && (
                    <div className="pt-2 border-t border-border mt-2">
                      <span className="text-muted-foreground text-[9px] font-bold uppercase">Facts Summary</span>
                      <p className="text-[10px] text-foreground leading-relaxed mt-1 line-clamp-4">
                        {selected.metadata.brief_facts}
                      </p>
                    </div>
                  )}
                </div>

                <div className="mt-5 space-y-2">
                  <Button
                    size="sm"
                    className="w-full bg-primary text-primary-foreground hover:opacity-90 font-semibold text-xs py-1.5 h-8 flex items-center justify-center gap-1.5"
                    onClick={() => handleExpandNode(selected.id, selected.kind)}
                    disabled={isExpanding}
                  >
                    {isExpanding ? "Expanding..." : "Expand Neighbors"}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="w-full border-border hover:bg-muted text-foreground text-xs py-1.5 h-8"
                    onClick={() => {
                      navigate({ search: (old) => ({ ...old, focusId: selected.id }) });
                      setSelected(null);
                    }}
                  >
                    Focus Graph Here
                  </Button>
                </div>
              </aside>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
