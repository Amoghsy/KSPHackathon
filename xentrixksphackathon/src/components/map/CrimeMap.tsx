import { useEffect, useState, useRef } from "react";
import type React from "react";

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
  onOpenInvestigation?: (district: string) => void;
}

/**
 * CrimeMap — client-only Leaflet GIS wrapper.
 *
 * All leaflet/react-leaflet imports are deferred to the browser via dynamic
 * import() so they never execute during the TanStack Start SSR pass, which
 * would crash because Leaflet accesses `window` at module load time.
 */
export function CrimeMap(props: CrimeMapProps) {
  const [MapInner, setMapInner] = useState<React.ComponentType<CrimeMapProps> | null>(null);
  const loaded = useRef(false);

  useEffect(() => {
    if (loaded.current) return;
    loaded.current = true;
    // Dynamically import the inner component that carries all Leaflet deps
    import("./CrimeMapInner").then((mod) => {
      setMapInner(() => mod.CrimeMapInner);
    });
  }, []);

  if (!MapInner) {
    return (
      <div className="w-full h-full relative rounded-xl overflow-hidden border border-border bg-[#020617] flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <span className="text-slate-500 text-sm">Loading Karnataka Intelligence Map…</span>
        </div>
      </div>
    );
  }

  return <MapInner {...props} />;
}

export default CrimeMap;
