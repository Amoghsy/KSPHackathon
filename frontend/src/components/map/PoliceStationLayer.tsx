import { memo } from "react";
import { Marker, Popup } from "react-leaflet";
import MarkerClusterGroup from "react-leaflet-cluster";
import L from "leaflet";
import { Button } from "@/components/ui/button";
import { Shield } from "lucide-react";

interface Station {
  name: string;
  district: string;
  latitude: number;
  longitude: number;
  cases: number;
  solved: number;
  pending: number;
  dominant: string;
  repeat_offenders: number;
}

interface PoliceStationLayerProps {
  stations: Station[];
  zoomLevel: number;
  show: boolean;
  onOpenInvestigation?: (district: string) => void;
}

const stationIcon = L.divIcon({
  html: `<div class="flex items-center justify-center w-8 h-8 rounded-full bg-blue-500/20 border border-blue-500 shadow-md">
           <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-blue-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
             <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
           </svg>
         </div>`,
  className: "custom-station-icon",
  iconSize: [32, 32],
  iconAnchor: [16, 16]
});

const createClusterIcon = (cluster: any) => {
  return L.divIcon({
    html: `<div class="flex items-center justify-center w-full h-full rounded-full bg-blue-600/30 border-2 border-blue-500 shadow-lg text-blue-100 dark:text-blue-50 font-bold text-xs">
             ${cluster.getChildCount()}
           </div>`,
    className: "custom-station-cluster",
    iconSize: L.point(36, 36)
  });
};

export const PoliceStationLayer = memo(function PoliceStationLayer({ stations, zoomLevel, show, onOpenInvestigation }: PoliceStationLayerProps) {
  if (!show) return null;

  return (
    <MarkerClusterGroup
      key={`station-cluster-${stations.length}`}
      iconCreateFunction={createClusterIcon}
    >
      {stations.map((ps) => (
        <Marker
          key={ps.name}
          position={[ps.latitude, ps.longitude]}
          icon={stationIcon}
        >
          <Popup className="dark-theme-popup">
            <div className="text-xs p-1 text-foreground space-y-2 max-w-xs">
              <div className="flex items-center gap-1.5 font-bold border-b border-border pb-1 text-blue-400">
                <Shield className="h-4 w-4 text-blue-400" />
                {ps.name}
              </div>
              <div className="grid grid-cols-2 gap-y-0.5">
                <span className="text-muted-foreground">District:</span>
                <span className="font-medium">{ps.district}</span>
                <span className="text-muted-foreground">Total cases:</span>
                <span className="font-bold">{ps.cases}</span>
                <span className="text-emerald-500 font-semibold">Solved:</span>
                <span className="text-emerald-500 font-semibold">{ps.solved}</span>
                <span className="text-red-400 font-semibold">Pending:</span>
                <span className="text-red-400 font-semibold">{ps.pending}</span>
                <span className="text-muted-foreground">Top Crime:</span>
                <span className="font-semibold text-primary">{ps.dominant}</span>
                <span className="text-muted-foreground">Repeat Offenders:</span>
                <span className="font-medium">{ps.repeat_offenders}</span>
              </div>
              
              {onOpenInvestigation && (
                <Button
                  size="sm"
                  className="w-full h-7 text-[10px] bg-blue-650 hover:bg-blue-650/90 text-white font-semibold"
                  onClick={() => onOpenInvestigation(ps.district)}
                >
                  Open Station Investigation
                </Button>
              )}
            </div>
          </Popup>
        </Marker>
      ))}
    </MarkerClusterGroup>
  );
});
