import { memo } from "react";
import { CircleMarker, Marker, Popup } from "react-leaflet";
import MarkerClusterGroup from "react-leaflet-cluster";
import L from "leaflet";

interface HeatmapPoint {
  latitude: number;
  longitude: number;
  crime_type: string;
  gravity: number;
  district: string;
}

interface BubbleLayerProps {
  points: HeatmapPoint[];
  zoomLevel: number;
  show: boolean;
}

// Custom pin icon for individual FIR incidents at zoom 14+
const incidentPinIcon = L.divIcon({
  html: `<div class="flex items-center justify-center w-6 h-6 rounded-full bg-red-500/30 border border-red-500 shadow-md">
           <div class="w-2 h-2 rounded-full bg-red-500"></div>
         </div>`,
  className: "custom-incident-pin",
  iconSize: [24, 24],
  iconAnchor: [12, 12]
});

const createClusterIcon = (cluster: any) => {
  return L.divIcon({
    html: `<div class="flex items-center justify-center w-full h-full rounded-full bg-red-600/30 border-2 border-red-500 shadow-lg text-red-100 dark:text-red-50 font-bold text-xs">
             ${cluster.getChildCount()}
           </div>`,
    className: "custom-crime-cluster",
    iconSize: L.point(36, 36)
  });
};

export const BubbleLayer = memo(function BubbleLayer({ points, zoomLevel, show }: BubbleLayerProps) {
  if (!show) return null;

  const validPoints = points.filter(
    (p) => p && typeof p.latitude === "number" && typeof p.longitude === "number"
  );

  const isClusteredView = zoomLevel < 12;
  const isIndividualPins = zoomLevel >= 14;

  if (isClusteredView || isIndividualPins) {
    return (
      <MarkerClusterGroup iconCreateFunction={createClusterIcon}>
        {validPoints.map((p, i) => (
          <Marker
            key={`fir-${i}`}
            position={[p.latitude, p.longitude]}
            icon={incidentPinIcon}
          >
            <Popup className="dark-theme-popup">
              <div className="text-xs p-1 space-y-1 text-foreground">
                <div className="font-bold border-b border-border pb-0.5 text-primary">Incident Record</div>
                <div>Offense: <span className="font-semibold">{p.crime_type}</span></div>
                <div>District: <span>{p.district}</span></div>
                <div>Severity: <span className="font-semibold text-red-400">{p.gravity === 4 ? 'Grievous' : p.gravity === 3 ? 'High' : p.gravity === 2 ? 'Medium' : 'Low'}</span></div>
              </div>
            </Popup>
          </Marker>
        ))}
      </MarkerClusterGroup>
    );
  }

  // Otherwise, render aggregated Crime Bubbles (CircleMarkers) at Zoom 12 & 13
  return (
    <>
      {validPoints.map((p, i) => {
        let color = "#10B981"; // Low (1)
        if (p.gravity === 4) color = "#EF4444";      // Grievous (4) - Red
        else if (p.gravity === 3) color = "#F97316"; // High (3) - Orange
        else if (p.gravity === 2) color = "#F59E0B"; // Medium (2) - Yellow

        // Bubble radius scale
        const rad = p.gravity === 4 ? 8 : p.gravity === 3 ? 6.5 : p.gravity === 2 ? 5 : 4;

        return (
          <CircleMarker
            key={`bubble-${i}`}
            center={[p.latitude, p.longitude]}
            radius={rad}
            fillColor={color}
            color="rgba(255, 255, 255, 0.45)"
            weight={1}
            fillOpacity={0.85}
            className="transition-all duration-300 transform hover:scale-150"
          >
            <Popup className="dark-theme-popup">
              <div className="text-xs space-y-1 text-foreground">
                <div className="font-bold border-b border-border pb-0.5">{p.crime_type}</div>
                <div>District: <span className="font-medium">{p.district}</span></div>
                <div>Severity: <span className="font-semibold text-primary">{p.gravity === 4 ? 'Grievous' : p.gravity === 3 ? 'High' : p.gravity === 2 ? 'Medium' : 'Low'}</span></div>
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </>
  );
});
