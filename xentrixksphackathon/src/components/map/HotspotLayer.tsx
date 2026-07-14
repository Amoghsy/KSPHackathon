import { memo, Fragment } from "react";
import { CircleMarker, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import { AlertTriangle, TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";

interface HotspotCenter {
  latitude: number;
  longitude: number;
}

interface Hotspot {
  cluster_id?: number;
  // Backend returns center as {latitude, longitude}
  center: HotspotCenter | [number, number];
  cases: number;
  dominant: string;
  // Backend returns severity (0-4 gravity avg), not confidence
  severity?: number;
  confidence?: number;
  district?: string;
  radius?: number;
}

interface HotspotLayerProps {
  hotspots: Hotspot[];
  show: boolean;
  onOpenInvestigation?: (district: string) => void;
}

// Custom DivIcon that matches the legend: red circle with an alert triangle icon
const hotspotIcon = L.divIcon({
  html: `<div class="flex items-center justify-center w-8 h-8 rounded-full bg-red-500/10 border-2 border-red-500 shadow-md">
           <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-red-500 animate-pulse" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
             <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
             <line x1="12" y1="9" x2="12" y2="13"/>
             <line x1="12" y1="17" x2="12.01" y2="17"/>
           </svg>
         </div>`,
  className: "custom-hotspot-icon",
  iconSize: [32, 32],
  iconAnchor: [16, 16],
});

/** Normalise the center field regardless of whether backend sends
 *  an object {latitude, longitude} or a [lat, lng] tuple. */
function resolveCenter(center: HotspotCenter | [number, number]): [number, number] | null {
  if (Array.isArray(center)) {
    if (typeof center[0] === "number" && typeof center[1] === "number") {
      return [center[0], center[1]];
    }
    return null;
  }
  if (
    center &&
    typeof center.latitude === "number" &&
    typeof center.longitude === "number"
  ) {
    return [center.latitude, center.longitude];
  }
  return null;
}

/** Map gravity avg (0-4) to a human-readable severity label. */
function severityLabel(severity?: number): string {
  if (severity === undefined) return "CRITICAL";
  if (severity >= 3.5) return "CRITICAL";
  if (severity >= 2.5) return "HIGH";
  if (severity >= 1.5) return "MEDIUM";
  return "LOW";
}

export const HotspotLayer = memo(function HotspotLayer({ hotspots, show, onOpenInvestigation }: HotspotLayerProps) {
  if (!show) return null;

  const validHotspots = hotspots
    .map((c) => ({ ...c, _center: resolveCenter(c.center) }))
    .filter((c) => c._center !== null) as (Hotspot & { _center: [number, number] })[];

  return (
    <>
      {validHotspots.map((c, i) => (
        <Fragment key={`hotspot-group-${c.cluster_id ?? i}`}>
          {/* Pulsing red coverage area */}
          <CircleMarker
            center={c._center}
            radius={24}
            fillColor="#EF4444"
            color="#EF4444"
            weight={1}
            fillOpacity={0.12}
            className="animate-pulse pointer-events-none"
          />
          {/* Clickable center icon matching the legend */}
          <Marker position={c._center} icon={hotspotIcon}>
            <Popup className="dark-theme-popup">
              <div className="text-xs p-1 text-foreground space-y-2 max-w-xs">
                <div className="font-bold flex items-center gap-1.5 text-red-500">
                  <AlertTriangle className="h-4 w-4 text-red-500" />
                  DBSCAN Hotspot Cluster
                </div>
                <div className="grid grid-cols-2 gap-y-0.5 border-b border-border pb-1">
                  <span className="text-muted-foreground">District:</span>
                  <span className="font-medium">{c.district || "—"}</span>
                  <span className="text-muted-foreground">Cases:</span>
                  <span className="font-bold">{c.cases} offenses</span>
                  <span className="text-muted-foreground">Dominant:</span>
                  <span className="font-semibold">{c.dominant}</span>
                  <span className="text-muted-foreground">Severity:</span>
                  <span className="font-semibold text-red-500">{severityLabel(c.severity)}</span>
                </div>

                <div className="flex items-center gap-1 text-[11px] text-muted-foreground italic">
                  <TrendingUp className="h-3 w-3 text-red-500" />
                  Emerging activity spike detected.
                </div>

                {onOpenInvestigation && (
                  <Button
                    size="sm"
                    className="w-full mt-1.5 h-7 text-[10px] bg-red-650 hover:bg-red-650/90 text-white font-semibold"
                    onClick={() => onOpenInvestigation(c.district || "Mysuru")}
                  >
                    Investigate Local Syndicate
                  </Button>
                )}
              </div>
            </Popup>
          </Marker>
        </Fragment>
      ))}
    </>
  );
});

export default HotspotLayer;
