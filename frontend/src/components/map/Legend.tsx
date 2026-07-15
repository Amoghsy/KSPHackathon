import { Shield, AlertTriangle } from "lucide-react";

interface LegendProps {
  activeTab: "data" | "layers";
  appliedFilters: {
    district?: string;
    crime_type?: string;
    date_range?: string;
    gravity?: string;
    status?: string;
  };
  stats: {
    heatmapPoints: number;
    policeStations: number;
    hotspots: number;
  };
  layers: {
    showHeatmap: boolean;
    showBubbles: boolean;
    showStations: boolean;
    showHotspots: boolean;
    showBoundaries: boolean;
  };
}

export function Legend({ activeTab, appliedFilters, stats, layers }: LegendProps) {
  // GIS Data Tab Legend
  if (activeTab === "data") {
    return (
      <div className="absolute bottom-4 right-4 z-[500] bg-card/95 backdrop-blur border border-border p-4 rounded-xl shadow-2xl text-foreground w-80 space-y-3 animate-in fade-in duration-200">
        <div className="flex items-center justify-between border-b border-border pb-1.5">
          <div className="text-[10px] font-bold text-primary uppercase tracking-widest">
            GIS Query Telemetry
          </div>
          <span className="flex h-2 w-2 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
        </div>

        {/* Filter Summary Grid */}
        <div className="space-y-1 text-xs">
          <div className="grid grid-cols-2 gap-y-1.5 text-[10px] text-muted-foreground bg-muted/30 p-2 rounded-lg border border-border/30 font-mono">
            <span className="font-medium">Crime Type:</span>
            <span className="text-foreground font-semibold text-right truncate">
              {appliedFilters.crime_type ?? "All"}
            </span>

            <span className="font-medium">Time Range:</span>
            <span className="text-foreground font-semibold text-right">
              {appliedFilters.date_range
                ? appliedFilters.date_range === "3650"
                  ? "All Time"
                  : appliedFilters.date_range === "1825"
                  ? "5 Years"
                  : `${appliedFilters.date_range} Days`
                : "—"}
            </span>

            <span className="font-medium">District:</span>
            <span className="text-foreground font-semibold text-right truncate">
              {appliedFilters.district ?? "All"}
            </span>

            <span className="font-medium">Severity:</span>
            <span className="text-foreground font-semibold text-right">
              {appliedFilters.gravity ?? "All"}
            </span>

            <span className="font-medium">Status:</span>
            <span className="text-foreground font-semibold text-right truncate">
              {appliedFilters.status ?? "All"}
            </span>
          </div>
        </div>

        {/* Loaded Statistics Counters */}
        <div className="space-y-1.5 border-t border-border/40 pt-2">
          <div className="text-[9px] uppercase tracking-wider text-muted-foreground/80 font-bold">Plotted Dataset Statistics</div>
          <div className="grid grid-cols-3 gap-2 font-bold text-center">
            <div className="bg-red-500/10 border border-red-500/20 p-1.5 rounded-lg">
              <div className="text-[9px] text-red-400">Heat Points</div>
              <div className="text-sm font-mono text-red-500">{stats.heatmapPoints}</div>
            </div>
            <div className="bg-blue-500/10 border border-blue-500/20 p-1.5 rounded-lg">
              <div className="text-[9px] text-blue-400">Stations</div>
              <div className="text-sm font-mono text-blue-500">{stats.policeStations}</div>
            </div>
            <div className="bg-amber-500/10 border border-amber-500/20 p-1.5 rounded-lg">
              <div className="text-[9px] text-amber-400">Hotspots</div>
              <div className="text-sm font-mono text-amber-500">{stats.hotspots}</div>
            </div>
          </div>
        </div>

        {/* Severity Scale */}
        <div className="space-y-1 border-t border-border/40 pt-2 text-xs">
          <div className="font-semibold text-muted-foreground text-[10px] uppercase tracking-wider">Severity Marker Scale</div>
          <div className="grid grid-cols-4 gap-1 text-[9px] font-medium text-center">
            <div className="flex flex-col items-center">
              <span className="h-2 w-2 rounded-full bg-emerald-500 mb-0.5 shadow-sm shadow-emerald-550" />
              <span>Low</span>
            </div>
            <div className="flex flex-col items-center">
              <span className="h-2 w-2 rounded-full bg-amber-500 mb-0.5 shadow-sm shadow-amber-555" />
              <span>Medium</span>
            </div>
            <div className="flex flex-col items-center">
              <span className="h-2 w-2 rounded-full bg-orange-500 mb-0.5 shadow-sm shadow-orange-555" />
              <span>High</span>
            </div>
            <div className="flex flex-col items-center">
              <span className="h-2 w-2 rounded-full bg-red-500 mb-0.5 shadow-sm shadow-red-555" />
              <span>Critical</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Map Layers Tab Legend (activeTab === "layers")
  return (
    <div className="absolute bottom-4 right-4 z-[500] bg-card/95 backdrop-blur border border-border p-4 rounded-xl shadow-2xl text-foreground w-64 space-y-3 animate-in fade-in duration-200">
      <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest border-b border-border pb-1.5">
        Tactical Layers Legend
      </div>

      <div className="space-y-2.5 text-xs">
        {/* Heatmap Density */}
        {layers.showHeatmap && (
          <div className="space-y-1 animate-in fade-in duration-150">
            <div className="font-semibold text-muted-foreground text-[9px] uppercase tracking-wider">HEATMAP DENSITY</div>
            <div className="h-1.5 w-full rounded-sm bg-gradient-to-r from-yellow-500/20 via-orange-500/60 to-red-500" />
            <div className="flex justify-between text-[8px] text-muted-foreground">
              <span>Low</span>
              <span>Critical</span>
            </div>
          </div>
        )}

        {/* Crime Severity Scale */}
        {layers.showBubbles && (
          <div className="space-y-1 border-t border-border/20 pt-1.5 animate-in fade-in duration-150">
            <div className="font-semibold text-muted-foreground text-[9px] uppercase tracking-wider">CRIME SEVERITY BUBBLES</div>
            <div className="grid grid-cols-2 gap-1.5 text-[9px] font-medium">
              <div className="flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 block"></span>
                <span>Low</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-amber-500 block"></span>
                <span>Medium</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-orange-500 block"></span>
                <span>High</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-red-500 block"></span>
                <span>Critical</span>
              </div>
            </div>
          </div>
        )}

        {/* Entities (Dynamic visibility) */}
        {(layers.showStations || layers.showHotspots || layers.showBoundaries) && (
          <div className="space-y-1.5 border-t border-border/20 pt-2 text-[10px]">
            <div className="font-semibold text-muted-foreground text-[9px] uppercase tracking-wider mb-1">MAP SYMBOLS</div>
            
            {layers.showStations && (
              <div className="flex items-center gap-2 animate-in fade-in duration-150">
                <div className="flex items-center justify-center w-5 h-5 rounded-full bg-blue-500/20 border border-blue-500">
                  <Shield className="h-2.5 w-2.5 text-blue-400" />
                </div>
                <span className="text-[10px] font-medium text-foreground/80">Police Station</span>
              </div>
            )}
            
            {layers.showHotspots && (
              <div className="flex items-center gap-2 animate-in fade-in duration-150">
                <div className="flex items-center justify-center w-5 h-5 rounded-full bg-red-500/10 border border-red-500/40">
                  <AlertTriangle className="h-2.5 w-2.5 text-red-500 animate-pulse" />
                </div>
                <span className="text-[10px] font-medium text-foreground/80">DBSCAN Hotspot</span>
              </div>
            )}

            {layers.showBoundaries && (
              <div className="flex items-center gap-2 animate-in fade-in duration-150">
                <div className="h-2.5 w-5 border border-dashed border-slate-500 rounded bg-slate-500/5" />
                <span className="text-[10px] font-medium text-foreground/80">District Boundary</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default Legend;
