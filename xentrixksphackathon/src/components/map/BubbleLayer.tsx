import { memo } from "react";
import { CircleMarker, Popup } from "react-leaflet";

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

export const BubbleLayer = memo(function BubbleLayer({ points, show }: BubbleLayerProps) {
  if (!show) return null;

  const validPoints = points.filter(
    (p) => p && typeof p.latitude === "number" && typeof p.longitude === "number"
  );

  return (
    <>
      {validPoints.map((p, i) => {
        let color = "#10b981"; // Low (1) - Emerald
        if (p.gravity === 4) color = "#ef4444";      // Grievous (4) - Red
        else if (p.gravity === 3) color = "#f97316"; // High (3) - Orange
        else if (p.gravity === 2) color = "#f59e0b"; // Medium (2) - Amber

        // Scale radius slightly to match visual significance
        const rad = p.gravity === 4 ? 9 : p.gravity === 3 ? 7.5 : p.gravity === 2 ? 6 : 4.5;

        return (
          <CircleMarker
            key={`bubble-${p.crime_type}-${i}`}
            center={[p.latitude, p.longitude]}
            radius={rad}
            fillColor={color}
            color="#ffffff"
            weight={1.5}
            fillOpacity={0.85}
            pane="markerPane"
          >
            <Popup className="dark-theme-popup">
              <div className="text-xs p-1 space-y-1 text-foreground min-w-[120px]">
                <div className="font-bold border-b border-border pb-0.5 text-primary text-[11px]">
                  {p.crime_type} Incident
                </div>
                <div className="grid grid-cols-2 gap-y-0.5 text-[10px] pt-0.5">
                  <span className="text-muted-foreground">District:</span>
                  <span className="font-medium text-right">{p.district}</span>
                  
                  <span className="text-muted-foreground">Severity:</span>
                  <span className="font-bold text-right" style={{ color }}>
                    {p.gravity === 4 ? "Grievous" : p.gravity === 3 ? "High" : p.gravity === 2 ? "Medium" : "Low"}
                  </span>
                </div>
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </>
  );
});

export default BubbleLayer;
