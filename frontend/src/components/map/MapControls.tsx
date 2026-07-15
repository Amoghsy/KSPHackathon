import { useMap } from "react-leaflet";
import L from "leaflet";
import { Button } from "@/components/ui/button";
import { Plus, Minus, Crosshair } from "lucide-react";

const KARNATAKA_BOUNDS: L.LatLngBoundsExpression = [
  [11.0, 73.5],
  [19.0, 79.0]
];

export function MapControls() {
  const map = useMap();

  const handleRecenter = () => {
    map.fitBounds(KARNATAKA_BOUNDS, { padding: [12, 12], duration: 1.5 });
  };

  const handleZoomIn = () => {
    map.zoomIn();
  };

  const handleZoomOut = () => {
    map.zoomOut();
  };

  return (
    <div className="absolute bottom-4 left-4 z-[500] flex flex-col gap-1.5 bg-card/90 backdrop-blur border border-border p-1.5 rounded-xl shadow-lg">
      <Button
        size="icon"
        variant="ghost"
        className="h-8 w-8 hover:bg-accent text-foreground rounded-lg"
        onClick={handleZoomIn}
        title="Zoom In"
      >
        <Plus className="h-4 w-4" />
      </Button>
      <Button
        size="icon"
        variant="ghost"
        className="h-8 w-8 hover:bg-accent text-foreground rounded-lg border-b border-border pb-1.5"
        onClick={handleZoomOut}
        title="Zoom Out"
      >
        <Minus className="h-4 w-4" />
      </Button>
      <Button
        size="icon"
        variant="ghost"
        className="h-8 w-8 hover:bg-accent text-foreground rounded-lg"
        onClick={handleRecenter}
        title="Recenter Map"
      >
        <Crosshair className="h-4 w-4" />
      </Button>
    </div>
  );
}

export default MapControls;
