import { memo, useEffect, useState, useMemo } from "react";
import type React from "react";
import { Legend } from "./Legend";

interface CrimeMapProps {
  selected: string | null;
  setSelected: (district: string | null) => void;
  zoomLevel: number;
  setZoomLevel: (z: number) => void;
  data: {
    heatmap_points: any[];
    hotspots: any[];
    police_stations: any[];
  };
  layers: {
    showHeatmap: boolean;
    setShowHeatmap: (v: boolean) => void;
    showBubbles: boolean;
    setShowBubbles: (v: boolean) => void;
    showStations: boolean;
    setShowStations: (v: boolean) => void;
    showHotspots: boolean;
    setShowHotspots: (v: boolean) => void;
    showBoundaries: boolean;
    setShowBoundaries: (v: boolean) => void;
  };
  activeTab: "data" | "layers";
  appliedFilters: {
    district?: string;
    crime_type?: string;
    date_range?: string;
    gravity?: string;
    status?: string;
  };
  onOpenInvestigation?: (district: string) => void;
}

// Module-level cache: the dynamic import runs once per app lifetime.
// All instances of CrimeMap share the same resolved component reference.
let _resolvedInner: React.ComponentType<CrimeMapProps> | null = null;
let _resolveListeners: Array<() => void> = [];

function loadMapInner(): Promise<React.ComponentType<CrimeMapProps>> {
  if (_resolvedInner) return Promise.resolve(_resolvedInner);
  // @ts-ignore - dynamic import is resolved correctly by bundler, ignore IDE check
  return import("./CrimeMapInner").then((mod) => {
    _resolvedInner = mod.CrimeMapInner as React.ComponentType<CrimeMapProps>;
    _resolveListeners.forEach((fn) => fn());
    _resolveListeners = [];
    return _resolvedInner;
  });
}

/**
 * CrimeMap — client-only Leaflet GIS wrapper.
 *
 * Wrapped with React.memo so the MapContainer NEVER remounts when the parent
 * page re-renders (filter changes, district selection, sidebar updates, etc.).
 * The map is created once; only individual data layers update.
 *
 * Renders the Legend instantly on mount so there is no delay or waiting
 * for the dynamic Leaflet components to download.
 */
export const CrimeMap = memo(function CrimeMap(props: CrimeMapProps) {
  const [MapInner, setMapInner] = useState<React.ComponentType<CrimeMapProps> | null>(
    () => _resolvedInner  // sync init — already loaded on second render
  );

  useEffect(() => {
    if (_resolvedInner) {
      setMapInner(() => _resolvedInner);
      return;
    }
    // Register a listener so we're notified when the import resolves
    const notify = () => setMapInner(() => _resolvedInner);
    _resolveListeners.push(notify);
    loadMapInner();
    return () => {
      _resolveListeners = _resolveListeners.filter((fn) => fn !== notify);
    };
  }, []);

  const stats = useMemo(() => ({
    heatmapPoints: props.data.heatmap_points?.length || 0,
    policeStations: props.data.police_stations?.length || 0,
    hotspots: props.data.hotspots?.length || 0,
  }), [props.data.heatmap_points, props.data.police_stations, props.data.hotspots]);

  return (
    <div className="w-full h-full relative rounded-xl overflow-hidden border border-border">
      {MapInner ? (
        <MapInner {...props} />
      ) : (
        <div className="w-full h-full bg-[#020617] flex items-center justify-center">
          <div className="flex flex-col items-center gap-3">
            <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            <span className="text-slate-500 text-sm">Loading Karnataka Intelligence Map…</span>
          </div>
        </div>
      )}
      
      {/* Dynamic context-aware legend component */}
      <Legend
        activeTab={props.activeTab}
        appliedFilters={props.appliedFilters}
        stats={stats}
        layers={props.layers}
      />
    </div>
  );
});

export default CrimeMap;
