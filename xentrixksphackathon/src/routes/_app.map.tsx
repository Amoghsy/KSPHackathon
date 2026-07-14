import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useMemo, useCallback, useState, useEffect } from "react";
import { PageHeader } from "@/components/app/primitives";
import { getMapAnalytics } from "@/services/crimeMapApi";
import { getCasesMetadata } from "@/services/api";
import { CrimeMap } from "@/components/map/CrimeMap";
import { useCrimeMap } from "@/hooks/useCrimeMap";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import { useRBAC } from "@/hooks/useRBAC";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Shield,
  Network,
  BarChart2,
  MapPin,
  RotateCcw,
  RefreshCw,
  Database,
  Layers,
} from "lucide-react";
import { Switch } from "@/components/ui/switch";

export const Route = createFileRoute("/_app/map")({
  ssr: false,
  head: () => ({ meta: [{ title: "Crime Map — Crime Intelligence Assistant" }] }),
  component: MapPage,
});

// Empty fallback — defined once outside the component so it's always the same reference
const EMPTY_MAP_DATA = {
  heatmap_points: [] as any[],
  hotspots: [] as any[],
  police_stations: [] as any[],
  district_statistics: {} as Record<string, any>,
};

// Build query filter object from individual filter values
function buildFilters(
  selDistrict: string,
  crimeType: string,
  dateRange: string,
  gravity: string,
  status: string
) {
  return {
    district: selDistrict !== "All" ? selDistrict : undefined,
    crime_type: crimeType !== "All" ? crimeType : undefined,
    date_range: dateRange,
    gravity: gravity !== "All" ? gravity : undefined,
    status: status !== "All" ? status : undefined,
  };
}

function MapPage() {
  const navigate = useNavigate();
  const rbac = useRBAC();
  const { user, role } = rbac;

  const { data: metadata } = useQuery({
    queryKey: ["casesMetadata"],
    queryFn: getCasesMetadata,
    staleTime: Infinity,
  });

  const districtsList = useMemo(() => metadata?.districts ?? [
    "Bengaluru Urban", "Bengaluru Rural", "Mysuru", "Mangaluru", "Belagavi",
    "Kalaburagi", "Hubballi-Dharwad", "Tumakuru", "Shivamogga", "Ballari",
    "Vijayapura", "Udupi", "Chitradurga", "Hassan",
  ], [metadata]);

  const crimeHeadsList = useMemo(() => metadata?.crime_heads ?? [
    "Theft", "Robbery", "Cyber Fraud", "Murder", "Assault",
    "Kidnapping", "Vehicle Theft", "Drug Trafficking", "Financial Fraud", "Human Trafficking"
  ], [metadata]);

  const gravityList = useMemo(() => metadata?.gravity ?? ["Low", "Medium", "High", "Grievous"], [metadata]);

  const districtOptions = useMemo(() => {
    if (!user) return [];
    if (role === "Admin" || role === "Analyst" || role === "Policymaker" || role === "Policy Maker") {
      return districtsList;
    }
    return user.assignedDistricts ?? [];
  }, [user, role, districtsList]);

  const canSelectAll = role === "Admin" || role === "Analyst" || role === "Policymaker" || role === "Policy Maker";

  const [activeTab, setActiveTab] = useState<"data" | "layers">("data");
  const { zoomLevel, setZoomLevel, selectedDistrict, setSelectedDistrict, filters, layers } =
    useCrimeMap();

  // Enforce district restrictions on mount / load
  useEffect(() => {
    if (!canSelectAll && districtOptions.length > 0) {
      if (filters.selDistrict === "All" || !districtOptions.includes(filters.selDistrict)) {
        filters.setSelDistrict(districtOptions[0]);
        setSelectedDistrict(districtOptions[0]);
      }
    }
  }, [canSelectAll, districtOptions, filters.selDistrict]);

  // "Applied" filters — only updated when the user clicks "Load Statistics"
  const [appliedFilters, setAppliedFilters] = useState(() =>
    buildFilters(
      !canSelectAll && districtOptions.length > 0 ? districtOptions[0] : filters.selDistrict,
      filters.crimeType,
      filters.dateRange,
      filters.gravity,
      filters.status
    )
  );

  // "Pending" filters — reflect what the user has currently selected in the sidebar
  const pendingFilters = useMemo(
    () =>
      buildFilters(
        filters.selDistrict,
        filters.crimeType,
        filters.dateRange,
        filters.gravity,
        filters.status
      ),
    [filters.selDistrict, filters.crimeType, filters.dateRange, filters.gravity, filters.status]
  );

  // True when the sidebar dropdowns differ from what was last applied
  const hasUnappliedChanges =
    JSON.stringify(pendingFilters) !== JSON.stringify(appliedFilters);

  // React Query — only fires when appliedFilters changes (i.e. when the button is clicked)
  const {
    data,
    isFetching,
    isLoading,
  } = useQuery({
    queryKey: ["mapAnalyticsPayload", appliedFilters],
    queryFn: () => getMapAnalytics(appliedFilters),
    staleTime: 0, // always re-fetch when filters are applied
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  // Apply current sidebar filters and trigger a fresh fetch
  const handleLoadStatistics = useCallback(() => {
    setAppliedFilters(pendingFilters);
  }, [pendingFilters]);

  // Reset all sidebar filters to defaults and reload
  const handleResetFilters = useCallback(() => {
    filters.setCrimeType("All");
    filters.setDateRange("30");
    filters.setSelDistrict("All");
    filters.setGravity("All");
    filters.setStatus("All");
    const resetFilters = buildFilters("All", "All", "30", "All", "All");
    setAppliedFilters(resetFilters);
  }, [filters]);

  const mapData = useMemo(() => data ?? EMPTY_MAP_DATA, [data]);

  // Stable callback — won't break React.memo on CrimeMap when parent re-renders
  const handleOpenInvestigation = useCallback(
    (district: string) => navigate({ to: "/network", search: { district } }),
    [navigate]
  );

  const selectedStats = selectedDistrict
    ? mapData.district_statistics[selectedDistrict]
    : null;

  const isBusy = isFetching || isLoading;

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)] overflow-hidden bg-background text-foreground">
      <div className="px-6 pt-6">
        <PageHeader
          title="Karnataka Crime Intelligence GIS"
          subtitle="Dedicated state-level crime mapping and spatial intelligence portal."
          actions={null}
        />
      </div>

      <div className="flex flex-1 gap-4 px-6 pb-6 min-h-0">
        {/* Sidebar Filters */}
        <aside className="w-64 shrink-0 rounded-xl bg-card border border-border p-4 space-y-4 text-card-foreground h-full overflow-y-auto scrollbar-thin">
          {/* Tab Selection */}
          <div className="grid grid-cols-2 bg-muted/40 p-1 rounded-lg border border-border/30 gap-1 mb-2 shrink-0">
            <button
              onClick={() => setActiveTab("data")}
              type="button"
              className={cn(
                "py-1.5 text-[10px] font-bold rounded-md transition-all flex items-center justify-center gap-1 cursor-pointer",
                activeTab === "data"
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              <Database className="h-3 w-3" />
              GIS Data
            </button>
            <button
              onClick={() => setActiveTab("layers")}
              type="button"
              className={cn(
                "py-1.5 text-[10px] font-bold rounded-md transition-all flex items-center justify-center gap-1 cursor-pointer",
                activeTab === "layers"
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              <Layers className="h-3 w-3" />
              Map Layers
            </button>
          </div>

          {activeTab === "data" ? (
            <div className="space-y-4 animate-in fade-in duration-200">
              {/* Header */}
              <div className="flex items-center justify-between border-b border-border pb-2">
                <div className="text-[11px] uppercase tracking-wider text-muted-foreground font-semibold">
                  GIS Filters
                </div>
                {hasUnappliedChanges && (
                  <span className="flex items-center gap-1 text-[9px] font-bold text-amber-500 bg-amber-500/10 border border-amber-500/30 px-1.5 py-0.5 rounded-full animate-pulse">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-500 inline-block" />
                    Pending
                  </span>
                )}
              </div>

              {/* Crime Type */}
              <div className="space-y-1.5">
                <Label className="text-xs text-foreground font-medium">Crime Type</Label>
                <Select value={filters.crimeType} onValueChange={filters.setCrimeType}>
                  <SelectTrigger className="bg-background border-input text-foreground text-xs h-8">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-popover border-border text-popover-foreground text-xs">
                    <SelectItem value="All">All types</SelectItem>
                    {crimeHeadsList.map((c) => (
                      <SelectItem key={c} value={c}>
                        {c}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Time Range */}
              <div className="space-y-1.5">
                <Label className="text-xs text-foreground font-medium">Time Range</Label>
                <Select value={filters.dateRange} onValueChange={filters.setDateRange}>
                  <SelectTrigger className="bg-background border-input text-foreground text-xs h-8">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-popover border-border text-popover-foreground text-xs">
                    <SelectItem value="7">Last 7 Days</SelectItem>
                    <SelectItem value="30">Last 30 Days</SelectItem>
                    <SelectItem value="90">Last 90 Days</SelectItem>
                    <SelectItem value="365">Last Year</SelectItem>
                    <SelectItem value="1825">Last 5 Years</SelectItem>
                    <SelectItem value="3650">All Time</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* District Focus */}
              <div className="space-y-1.5">
                <Label className="text-xs text-foreground font-medium">District Focus</Label>
                <Select
                  value={filters.selDistrict}
                  onValueChange={(val) => {
                    filters.setSelDistrict(val);
                    if (val !== "All") setSelectedDistrict(val);
                    else setSelectedDistrict(null);
                  }}
                >
                  <SelectTrigger className="bg-background border-input text-foreground text-xs h-8">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-popover border-border text-popover-foreground text-xs">
                    {canSelectAll && <SelectItem value="All">All districts</SelectItem>}
                    {districtOptions.map((d) => (
                      <SelectItem key={d} value={d}>
                        {d}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Severity Gravity */}
              <div className="space-y-1.5">
                <Label className="text-xs text-foreground font-medium">Severity Gravity</Label>
                <Select value={filters.gravity} onValueChange={filters.setGravity}>
                  <SelectTrigger className="bg-background border-input text-foreground text-xs h-8">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-popover border-border text-popover-foreground text-xs">
                    <SelectItem value="All">All</SelectItem>
                    {gravityList.map((g) => (
                      <SelectItem key={g} value={g}>
                        {g}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Case Status */}
              <div className="space-y-1.5">
                <Label className="text-xs text-foreground font-medium">Case Status</Label>
                <Select value={filters.status} onValueChange={filters.setStatus}>
                  <SelectTrigger className="bg-background border-input text-foreground text-xs h-8">
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

              {/* ── Load Statistics Button ── */}
              <div className="pt-1 border-t border-border space-y-2">
                <Button
                  className={cn(
                    "w-full h-9 text-xs font-bold flex items-center justify-center gap-2 transition-all cursor-pointer",
                    hasUnappliedChanges
                      ? "bg-primary hover:bg-primary/90 text-primary-foreground shadow-lg shadow-primary/25 ring-1 ring-primary/40"
                      : "bg-primary/80 hover:bg-primary text-primary-foreground"
                  )}
                  onClick={handleLoadStatistics}
                  disabled={isBusy}
                >
                  {isBusy ? (
                    <>
                      <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                      Loading…
                    </>
                  ) : (
                    <>
                      <Database className="h-3.5 w-3.5" />
                      Load Statistics
                      {hasUnappliedChanges && (
                        <span className="ml-1 w-2 h-2 rounded-full bg-amber-400 ring-1 ring-amber-400/60 animate-ping absolute" />
                      )}
                    </>
                  )}
                </Button>

                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full h-7 text-[10px] text-muted-foreground hover:text-foreground flex items-center gap-1.5 cursor-pointer"
                  onClick={handleResetFilters}
                  disabled={isBusy}
                >
                  <RotateCcw className="h-3 w-3" />
                  Reset Filters
                </Button>
              </div>

              {/* Active Map Telemetry (always visible) */}
              <div className="text-[10px] space-y-1.5 border-t border-border/40 pt-3 mt-1">
                <div className="font-bold uppercase tracking-widest text-[9px] text-muted-foreground/80 mb-2 flex items-center justify-between">
                  <span>Active Map Telemetry</span>
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                </div>
                
                <div className="grid grid-cols-2 gap-y-1.5 text-muted-foreground/75 bg-muted/30 p-2 rounded-lg border border-border/30">
                  <span className="font-medium">Crime Type:</span>
                  <span className="font-semibold text-foreground text-right truncate">
                    {appliedFilters.crime_type ?? "All"}
                  </span>

                  <span className="font-medium">Time Range:</span>
                  <span className="font-semibold text-foreground text-right">
                    {appliedFilters.date_range
                      ? appliedFilters.date_range === "3650"
                        ? "All Time"
                        : appliedFilters.date_range === "1825"
                        ? "5 Years"
                        : `${appliedFilters.date_range} Days`
                      : "—"}
                  </span>

                  <span className="font-medium">District:</span>
                  <span className="font-semibold text-foreground text-right truncate">
                    {appliedFilters.district ?? "All"}
                  </span>

                  <span className="font-medium">Severity:</span>
                  <span className="font-semibold text-foreground text-right">
                    {appliedFilters.gravity ?? "All"}
                  </span>

                  <span className="font-medium">Status:</span>
                  <span className="font-semibold text-foreground text-right truncate">
                    {appliedFilters.status ?? "All"}
                  </span>
                </div>

                <div className="bg-primary/5 border border-primary/20 rounded-lg p-2 mt-2 space-y-1">
                  <div className="text-[9px] uppercase tracking-wider text-muted-foreground/70 font-semibold">Loaded Objects</div>
                  <div className="flex justify-between font-mono font-bold text-primary text-xs pt-0.5">
                    <span className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-red-500 inline-block shadow-sm shadow-red-550" />
                      {mapData.heatmap_points.length} pts
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-blue-500 inline-block shadow-sm shadow-blue-500" />
                      {mapData.police_stations.length} stn
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-500 inline-block shadow-sm shadow-amber-500" />
                      {mapData.hotspots.length} hsp
                    </span>
                  </div>
                </div>
              </div>

              {/* Pending Changes Tip */}
              {hasUnappliedChanges && (
                <div className="text-[10px] leading-relaxed text-amber-500 bg-amber-500/5 border border-amber-500/20 rounded-lg p-2.5 mt-2.5 text-center animate-in fade-in duration-200 shadow-inner">
                  Filters modified. Click <strong className="text-amber-400 font-semibold">Load Statistics</strong> above to refresh map.
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-4 animate-in fade-in duration-200">
              <div className="text-[11px] uppercase tracking-wider text-muted-foreground font-semibold border-b border-border pb-2">
                Tactical Map Layers
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between gap-4 bg-muted/20 p-2.5 rounded-lg border border-border/20 hover:bg-muted/30 transition-colors">
                  <Label htmlFor="heatmap" className="text-xs font-semibold cursor-pointer text-foreground">Heatmap Layer</Label>
                  <Switch id="heatmap" checked={layers.showHeatmap} onCheckedChange={layers.setShowHeatmap} />
                </div>
                
                <div className="flex items-center justify-between gap-4 bg-muted/20 p-2.5 rounded-lg border border-border/20 hover:bg-muted/30 transition-colors">
                  <Label htmlFor="bubbles" className="text-xs font-semibold cursor-pointer text-foreground">Crime Bubbles</Label>
                  <Switch id="bubbles" checked={layers.showBubbles} onCheckedChange={layers.setShowBubbles} />
                </div>
                
                <div className="flex items-center justify-between gap-4 bg-muted/20 p-2.5 rounded-lg border border-border/20 hover:bg-muted/30 transition-colors">
                  <Label htmlFor="stations" className="text-xs font-semibold cursor-pointer text-foreground">Police Stations</Label>
                  <Switch id="stations" checked={layers.showStations} onCheckedChange={layers.setShowStations} />
                </div>
                
                <div className="flex items-center justify-between gap-4 bg-muted/20 p-2.5 rounded-lg border border-border/20 hover:bg-muted/30 transition-colors">
                  <Label htmlFor="hotspots" className="text-xs font-semibold cursor-pointer text-foreground">DBSCAN Hotspots</Label>
                  <Switch id="hotspots" checked={layers.showHotspots} onCheckedChange={layers.setShowHotspots} />
                </div>

                <div className="flex items-center justify-between gap-4 bg-muted/20 p-2.5 rounded-lg border border-border/20 hover:bg-muted/30 transition-colors">
                  <Label htmlFor="boundaries" className="text-xs font-semibold cursor-pointer text-foreground">District Boundaries</Label>
                  <Switch id="boundaries" checked={layers.showBoundaries} onCheckedChange={layers.setShowBoundaries} />
                </div>
              </div>

              <div className="bg-primary/5 border border-primary/20 rounded-lg p-3 text-[10px] text-muted-foreground leading-relaxed">
                <span className="font-semibold text-primary block mb-1">Instant Layer Control</span>
                Toggling these layers adjusts their visibility on the map instantly. No query reload is triggered.
              </div>
            </div>
          )}
        </aside>

        {/* Map Viewport */}
        <div className="flex-1 h-full relative rounded-xl overflow-hidden">
          {/* Global loading overlay */}
          {isBusy && (
            <div className="absolute inset-0 z-[600] flex items-center justify-center bg-background/40 backdrop-blur-[2px] rounded-xl">
              <div className="flex flex-col items-center gap-3 bg-card/90 border border-border rounded-xl px-6 py-4 shadow-2xl">
                <RefreshCw className="h-6 w-6 text-primary animate-spin" />
                <span className="text-sm font-semibold text-foreground">
                  Loading map data…
                </span>
                <span className="text-[10px] text-muted-foreground">
                  Applying filters to all GIS layers
                </span>
              </div>
            </div>
          )}

          <CrimeMap
            selected={selectedDistrict}
            setSelected={setSelectedDistrict}
            zoomLevel={zoomLevel}
            setZoomLevel={setZoomLevel}
            data={mapData}
            layers={layers}
            activeTab={activeTab}
            appliedFilters={appliedFilters}
            onOpenInvestigation={handleOpenInvestigation}
          />

          {/* District Intelligence Panel */}
          {selectedDistrict && selectedStats && (
            <div className="absolute top-4 right-4 w-80 rounded-xl bg-card/95 backdrop-blur border border-border shadow-2xl p-4 animate-in fade-in duration-200 text-card-foreground space-y-4.5 z-[500]">
              <div className="flex justify-between items-start">
                <div>
                  <div className="text-[10px] uppercase tracking-wider text-primary font-bold">
                    District Intelligence Panel
                  </div>
                  <h3 className="text-base font-bold text-foreground mt-0.5">
                    {selectedDistrict}
                  </h3>
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
                  <div className="text-[9px] text-muted-foreground uppercase font-semibold">
                    Total FIRs
                  </div>
                  <div className="text-base font-bold text-foreground mt-0.5 tabular-nums">
                    {selectedStats.cases}
                  </div>
                </div>
                <div className="text-center bg-muted/50 p-1.5 rounded-lg border border-border/40">
                  <div className="text-[9px] text-emerald-500 uppercase font-semibold">
                    Solved
                  </div>
                  <div className="text-base font-bold text-emerald-500 mt-0.5 tabular-nums">
                    {selectedStats.solved}
                  </div>
                </div>
                <div className="text-center bg-muted/50 p-1.5 rounded-lg border border-border/40">
                  <div className="text-[9px] text-red-500 dark:text-red-400 uppercase font-semibold">
                    Pending
                  </div>
                  <div className="text-base font-bold text-red-550 dark:text-red-400 mt-0.5 tabular-nums">
                    {selectedStats.pending}
                  </div>
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
                  <span
                    className={cn(
                      "font-semibold flex items-center gap-1",
                      selectedStats.growth >= 0
                        ? "text-red-550 dark:text-red-400"
                        : "text-emerald-600 dark:text-emerald-500"
                    )}
                  >
                    {selectedStats.growth >= 0
                      ? `+${selectedStats.growth}%`
                      : `${selectedStats.growth}%`}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Repeat Offenders:</span>
                  <span className="font-semibold text-foreground">
                    {selectedStats.repeat_offenders}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Gang Count:</span>
                  <span className="font-semibold text-foreground">
                    {selectedStats.gangs} gangs
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Emerging Hotspots:</span>
                  <span className="font-semibold text-foreground">
                    {selectedStats.hotspots} zones
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Forecast (Next Month):</span>
                  <span className="font-bold text-primary">
                    {selectedStats.prediction} cases
                  </span>
                </div>
              </div>

              {/* Tactical Buttons */}
              <div className="border-t border-border pt-3 space-y-2">
                <Button
                  size="sm"
                  className="w-full text-xs bg-primary hover:bg-primary/90 text-primary-foreground font-semibold flex items-center justify-center gap-1.5"
                  onClick={() =>
                    navigate({ to: "/network", search: { district: selectedDistrict } })
                  }
                >
                  <Network className="h-3.5 w-3.5" />
                  Open Criminal Network
                </Button>

                <Button
                  size="sm"
                  variant="outline"
                  className="w-full text-xs border-border hover:bg-accent hover:text-accent-foreground text-foreground font-semibold flex items-center justify-center gap-1.5"
                  onClick={() =>
                    navigate({ to: "/sociological", search: { district: selectedDistrict } })
                  }
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
                    setZoomLevel(10);
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
