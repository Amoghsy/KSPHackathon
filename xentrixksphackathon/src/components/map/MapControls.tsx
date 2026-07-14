import { useMap } from "react-leaflet";
import L from "leaflet";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Crosshair, Plus, Minus, Layers } from "lucide-react";
import { useState } from "react";

const KARNATAKA_BOUNDS: L.LatLngBoundsExpression = [
  [11.0, 73.5],
  [19.0, 79.0]
];

interface MapControlsProps {
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
}

export function MapControls({ layers }: MapControlsProps) {
  const map = useMap();
  const [showToggles, setShowToggles] = useState(true);

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
    <>
      {/* Zoom and Recenter Toolbar */}
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

      {/* Dynamic GIS Layer Toggles */}
      <div className="absolute top-4 left-4 z-[500] flex flex-col gap-2 bg-card/90 backdrop-blur border border-border p-3.5 rounded-xl shadow-lg text-foreground max-w-xs animate-in slide-in-from-left duration-200">
        <div className="flex items-center justify-between gap-6 border-b border-border pb-1.5 mb-1">
          <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest flex items-center gap-1.5">
            <Layers className="h-3.5 w-3.5 text-primary" />
            Tactical Map Layers
          </div>
          <button
            onClick={() => setShowToggles(!showToggles)}
            className="text-[9px] text-muted-foreground hover:text-foreground font-semibold"
          >
            {showToggles ? "Hide" : "Show"}
          </button>
        </div>
        
        {showToggles && (
          <div className="space-y-2.5">
            <div className="flex items-center justify-between gap-4">
              <Label htmlFor="heatmap" className="text-xs font-semibold cursor-pointer">Heatmap Layer</Label>
              <Switch id="heatmap" checked={layers.showHeatmap} onCheckedChange={layers.setShowHeatmap} />
            </div>
            
            <div className="flex items-center justify-between gap-4">
              <Label htmlFor="bubbles" className="text-xs font-semibold cursor-pointer">Crime Bubbles</Label>
              <Switch id="bubbles" checked={layers.showBubbles} onCheckedChange={layers.setShowBubbles} />
            </div>
            
            <div className="flex items-center justify-between gap-4">
              <Label htmlFor="stations" className="text-xs font-semibold cursor-pointer">Police Stations</Label>
              <Switch id="stations" checked={layers.showStations} onCheckedChange={layers.setShowStations} />
            </div>
            
            <div className="flex items-center justify-between gap-4">
              <Label htmlFor="hotspots" className="text-xs font-semibold cursor-pointer">DBSCAN Hotspots</Label>
              <Switch id="hotspots" checked={layers.showHotspots} onCheckedChange={layers.setShowHotspots} />
            </div>

            <div className="flex items-center justify-between gap-4">
              <Label htmlFor="boundaries" className="text-xs font-semibold cursor-pointer">District Boundaries</Label>
              <Switch id="boundaries" checked={layers.showBoundaries} onCheckedChange={layers.setShowBoundaries} />
            </div>
          </div>
        )}
      </div>
    </>
  );
}
export default MapControls;
