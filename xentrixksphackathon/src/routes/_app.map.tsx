import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { PageHeader } from "@/components/app/primitives";
import { getMapAnalytics } from "@/services/crimeMapApi";
import { DISTRICTS, CRIME_HEADS, GRAVITY } from "@/mocks/firs";
import { CrimeMap } from "@/components/map/CrimeMap";
import { useCrimeMap } from "@/hooks/useCrimeMap";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Shield, Network, BarChart2, MapPin } from "lucide-react";

export const Route = createFileRoute("/_app/map")({
  ssr: false,
  head: () => ({ meta: [{ title: "Crime Map — Crime Intelligence Assistant" }] }),
  component: MapPage,
});

function MapPage() {
  const navigate = useNavigate();
  const { zoomLevel, setZoomLevel, selectedDistrict, setSelectedDistrict, filters, layers } = useCrimeMap();

  const queryFilters = {
    district: filters.selDistrict !== "All" ? filters.selDistrict : undefined,
    crime_type: filters.crimeType !== "All" ? filters.crimeType : undefined,
    date_range: filters.dateRange,
    gravity: filters.gravity !== "All" ? filters.gravity : undefined,
    status: filters.status !== "All" ? filters.status : undefined,
  };

  // Single aggregated query for all map layers and statistics
  const { data, isLoading } = useQuery({
    queryKey: ["mapAnalyticsPayload", queryFilters],
    queryFn: () => getMapAnalytics(queryFilters),
  });

  const mapData = data || {
    heatmap_points: [],
    hotspots: [],
    police_stations: [],
    district_statistics: {}
  };

  const selectedStats = selectedDistrict ? mapData.district_statistics[selectedDistrict] : null;

  return (
    <div className="flex flex-col h-full bg-background text-foreground">
      <div className="px-6 pt-6">
        <PageHeader
          title="Karnataka Crime Intelligence GIS"
          subtitle="Dedicated state-level crime mapping and spatial intelligence portal."
          actions={null}
        />
      </div>

      <div className="flex flex-1 gap-4 px-6 pb-6 min-h-0">
        {/* Sidebar Filters */}
        <aside className="w-64 shrink-0 rounded-xl bg-card border border-border p-4 space-y-4 self-start text-card-foreground">
          <div className="text-[11px] uppercase tracking-wider text-muted-foreground font-semibold border-b border-border pb-1">
            GIS Filters
          </div>

          <div className="space-y-2">
            <Label className="text-xs text-foreground">Crime Type</Label>
            <Select value={filters.crimeType} onValueChange={filters.setCrimeType}>
              <SelectTrigger className="bg-background border-input text-foreground text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-popover border-border text-popover-foreground text-xs">
                <SelectItem value="All">All types</SelectItem>
                {CRIME_HEADS.map((c) => (
                  <SelectItem key={c} value={c}>
                    {c}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label className="text-xs text-foreground">Time Range</Label>
            <Select value={filters.dateRange} onValueChange={filters.setDateRange}>
              <SelectTrigger className="bg-background border-input text-foreground text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-popover border-border text-popover-foreground text-xs">
                <SelectItem value="7">Last 7 Days</SelectItem>
                <SelectItem value="30">Last 30 Days</SelectItem>
                <SelectItem value="90">Last 90 Days</SelectItem>
                <SelectItem value="365">Last Year</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label className="text-xs text-foreground">District Focus</Label>
            <Select value={filters.selDistrict} onValueChange={(val) => {
              filters.setSelDistrict(val);
              if (val !== "All") setSelectedDistrict(val);
            }}>
              <SelectTrigger className="bg-background border-input text-foreground text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-popover border-border text-popover-foreground text-xs">
                <SelectItem value="All">All districts</SelectItem>
                {DISTRICTS.map((d) => (
                  <SelectItem key={d} value={d}>
                    {d}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label className="text-xs text-foreground">Severity Gravity</Label>
            <Select value={filters.gravity} onValueChange={filters.setGravity}>
              <SelectTrigger className="bg-background border-input text-foreground text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-popover border-border text-popover-foreground text-xs">
                <SelectItem value="All">All</SelectItem>
                {GRAVITY.map((g) => (
                  <SelectItem key={g} value={g}>
                    {g}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label className="text-xs text-foreground">Case Status</Label>
            <Select value={filters.status} onValueChange={filters.setStatus}>
              <SelectTrigger className="bg-background border-input text-foreground text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-popover border-border text-popover-foreground text-xs">
                <SelectItem value="All">All Statuses</SelectItem>
                <SelectItem value="Under Investigation">Under Investigation</SelectItem>
                <SelectItem value="Charge Sheeted">Charge Sheeted</SelectItem>
                <SelectItem value="Closed">Closed</SelectItem>
                <SelectItem value="Undetected">Undetected</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </aside>

        {/* Map Viewport */}
        <div className="flex-1 relative rounded-xl overflow-hidden min-h-[500px]">
          <CrimeMap
            selected={selectedDistrict}
            setSelected={setSelectedDistrict}
            zoomLevel={zoomLevel}
            setZoomLevel={setZoomLevel}
            data={mapData}
            layers={layers}
            onOpenInvestigation={(district) => {
              navigate({ to: "/network", search: { district } });
            }}
          />

          {/* District Intelligence Panel */}
          {selectedDistrict && selectedStats && (
            <div className="absolute top-4 right-4 w-80 rounded-xl bg-card/95 backdrop-blur border border-border shadow-2xl p-4 animate-in fade-in duration-200 text-card-foreground space-y-4.5 z-[500]">
              <div className="flex justify-between items-start">
                <div>
                  <div className="text-[10px] uppercase tracking-wider text-primary font-bold">
                    District Intelligence Panel
                  </div>
                  <h3 className="text-base font-bold text-foreground mt-0.5">{selectedDistrict}</h3>
                </div>
                <button
                  onClick={() => setSelectedDistrict(null)}
                  className="text-muted-foreground hover:text-foreground text-xs font-medium"
                >
                  ✕
                </button>
              </div>

              {/* Case Stats grid */}
              <div className="grid grid-cols-3 gap-2 border-t border-border pt-2.5">
                <div className="text-center bg-muted/50 p-1.5 rounded-lg border border-border/40">
                  <div className="text-[9px] text-muted-foreground uppercase font-semibold">Total FIRs</div>
                  <div className="text-base font-bold text-foreground mt-0.5 tabular-nums">{selectedStats.cases}</div>
                </div>
                <div className="text-center bg-muted/50 p-1.5 rounded-lg border border-border/40">
                  <div className="text-[9px] text-emerald-500 uppercase font-semibold">Solved</div>
                  <div className="text-base font-bold text-emerald-500 mt-0.5 tabular-nums">{selectedStats.solved}</div>
                </div>
                <div className="text-center bg-muted/50 p-1.5 rounded-lg border border-border/40">
                  <div className="text-[9px] text-red-500 dark:text-red-400 uppercase font-semibold">Pending</div>
                  <div className="text-base font-bold text-red-550 dark:text-red-400 mt-0.5 tabular-nums">{selectedStats.pending}</div>
                </div>
              </div>

              {/* Details List */}
              <div className="space-y-1.5 border-t border-border pt-2.5 text-xs">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Dominant Crime:</span>
                  <span className="font-semibold text-primary">{selectedStats.dominant}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Growth Rate:</span>
                  <span className={cn("font-semibold flex items-center gap-1", selectedStats.growth >= 0 ? "text-red-550 dark:text-red-400" : "text-emerald-600 dark:text-emerald-500")}>
                    {selectedStats.growth >= 0 ? `+${selectedStats.growth}%` : `${selectedStats.growth}%`}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Repeat Offenders:</span>
                  <span className="font-semibold text-foreground">{selectedStats.repeat_offenders}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Gang Count:</span>
                  <span className="font-semibold text-foreground">{selectedStats.gangs} gangs</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Emerging Hotspots:</span>
                  <span className="font-semibold text-foreground">{selectedStats.hotspots} zones</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Forecast (Next Month):</span>
                  <span className="font-bold text-primary">{selectedStats.prediction} cases</span>
                </div>
              </div>

              {/* Tactical Buttons */}
              <div className="border-t border-border pt-3 space-y-2">
                <Button
                  size="sm"
                  className="w-full text-xs bg-primary hover:bg-primary/90 text-primary-foreground font-semibold flex items-center justify-center gap-1.5"
                  onClick={() => navigate({ to: "/network", search: { district: selectedDistrict } })}
                >
                  <Network className="h-3.5 w-3.5" />
                  Open Criminal Network
                </Button>

                <Button
                  size="sm"
                  variant="outline"
                  className="w-full text-xs border-border hover:bg-accent hover:text-accent-foreground text-foreground font-semibold flex items-center justify-center gap-1.5"
                  onClick={() => navigate({ to: "/sociological", search: { district: selectedDistrict } })}
                >
                  <BarChart2 className="h-3.5 w-3.5 text-primary" />
                  View Pattern Analytics
                </Button>

                <Button
                  size="sm"
                  variant="outline"
                  className="w-full text-xs border-border hover:bg-accent hover:text-accent-foreground text-foreground font-semibold flex items-center justify-center gap-1.5"
                  onClick={() => {
                    layers.setShowStations(true);
                    setZoomLevel(10); // make stations visible
                  }}
                >
                  <MapPin className="h-3.5 w-3.5 text-primary" />
                  View Police Stations
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
export default MapPage;
