import { useEffect, useState, useCallback, useMemo } from "react";
import { MapContainer, TileLayer, useMap, GeoJSON } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

import { usePrefs } from "@/stores/prefs";
import { BoundaryMask } from "./BoundaryMask";
import { DistrictLayer } from "./DistrictLayer";
import { HeatLayer } from "./HeatLayer";
import { BubbleLayer } from "./BubbleLayer";
import { PoliceStationLayer } from "./PoliceStationLayer";
import { HotspotLayer } from "./HotspotLayer";
import { MapControls } from "./MapControls";

// Karnataka Bounding Box Coordinates
const KARNATAKA_BOUNDS: L.LatLngBoundsExpression = [
  [11.0, 73.5],
  [19.0, 79.0],
];

const MAP_CENTER: L.LatLngExpression = [15.0, 76.2];

const DISTRICT_CENTROIDS: Record<string, [number, number]> = {
  "Bengaluru Urban": [12.9716, 77.5946],
  "Bengaluru Rural": [13.25, 77.7],
  Mysuru: [12.3, 76.64],
  Mangaluru: [12.91, 74.85],
  Belagavi: [15.84, 74.5],
  Kalaburagi: [17.32, 76.83],
  "Hubballi-Dharwad": [15.36, 75.12],
  Tumakuru: [13.33, 77.1],
  Shivamogga: [13.92, 75.56],
  Ballari: [15.13, 76.92],
  Vijayapura: [16.83, 75.71],
  Udupi: [13.34, 74.74],
  Chitradurga: [14.23, 76.4],
  Hassan: [13.0, 76.1],
};

// Tile layers: dark = CartoDB dark matter, light = CartoDB Positron (clean white)
const TILE_URLS = {
  dark: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
  light: "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
};

function MapController({
  selected,
  centerOnSelected,
}: {
  selected: string | null;
  centerOnSelected: boolean;
}) {
  const map = useMap();

  useEffect(() => {
    if (!map) return;
    map.setMaxBounds(KARNATAKA_BOUNDS);
    map.fitBounds(KARNATAKA_BOUNDS, { padding: [10, 10] });
  }, [map]);

  useEffect(() => {
    if (selected && centerOnSelected && DISTRICT_CENTROIDS[selected]) {
      const coords = DISTRICT_CENTROIDS[selected];
      map.flyTo(coords, 9, { duration: 1.5 });
    }
  }, [selected, centerOnSelected, map]);

  return null;
}

function ZoomListener({
  onZoomChange,
}: {
  onZoomChange: (zoom: number) => void;
}) {
  const map = useMap();

  useEffect(() => {
    if (!map) return;
    const handleZoom = () => onZoomChange(map.getZoom());
    map.on("zoomend", handleZoom);
    return () => {
      map.off("zoomend", handleZoom);
    };
  }, [map, onZoomChange]);

  return null;
}

interface CrimeMapInnerProps {
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

export function CrimeMapInner({
  selected,
  setSelected,
  zoomLevel,
  setZoomLevel,
  data,
  layers,
  onOpenInvestigation,
}: CrimeMapInnerProps) {
  const [geojsonData, setGeojsonData] = useState<any>(null);
  const [outlineData, setOutlineData] = useState<any>(null);
  const [centerOnSelected, setCenterOnSelected] = useState(true);
  const theme = usePrefs((s) => s.theme);
  const isDark = theme === "dark";

  useEffect(() => {
    fetch("/karnataka.geojson?v=karnataka-gis-v3")
      .then((res) => res.json())
      .then((gj) => setGeojsonData(gj))
      .catch((err) => console.error("Error loading karnataka.geojson:", err));

    fetch("/karnataka_outline.geojson?v=karnataka-gis-v3")
      .then((res) => res.json())
      .then((gj) => setOutlineData(gj))
      .catch((err) => console.error("Error loading karnataka_outline.geojson:", err));
  }, []);

  // Stable zoom callback — doesn't recreate on every render
  const handleZoomChange = useCallback((zoom: number) => {
    setZoomLevel(zoom);
    setCenterOnSelected(false);
  }, [setZoomLevel]);

  // Stable district select callback
  const handleSelectDistrict = useCallback((d: string | null) => {
    setCenterOnSelected(true);
    setSelected(d);
  }, [setSelected]);

  // Map background colour follows the theme
  const mapBg = isDark ? "#0d1117" : "#e8ecf0";

  // Outline style is static — memoize to prevent GeoJSON child re-renders
  const outlineStyle = useMemo(() => ({
    fillColor: "transparent",
    fillOpacity: 0,
    color: isDark ? "#3b82f6" : "#2563eb",
    weight: 3.0,
    opacity: 1.0,
    interactive: false,
  }), [isDark]);

  return (
    <div
      className="w-full h-full relative rounded-xl overflow-hidden border border-border"
      style={{ background: mapBg }}
    >
      <MapContainer
        center={MAP_CENTER}
        zoom={7}
        minZoom={6}
        maxZoom={12}
        zoomControl={false}
        className="w-full h-full"
        style={{ background: mapBg }}
      >
        <MapController selected={selected} centerOnSelected={centerOnSelected} />
        <ZoomListener onZoomChange={handleZoomChange} />

        {/* Base tile layer — switches with theme */}
        <TileLayer
          key={theme}
          url={TILE_URLS[theme]}
          attribution="&copy; OpenStreetMap &copy; CARTO"
        />

        {/* Outside-Karnataka mask — adapts colour to theme */}
        {useMemo(() => geojsonData ? (
          <BoundaryMask geojsonData={geojsonData} isDark={isDark} />
        ) : null, [geojsonData, isDark])}

        {/* Highlighted Karnataka State Outer Boundary Contour Line */}
        {useMemo(() => outlineData ? (
          <GeoJSON
            key={`karnataka-outline-${theme}`}
            data={outlineData}
            style={outlineStyle}
          />
        ) : null, [outlineData, theme, outlineStyle])}

        {/* District Boundaries — no remount on selection change */}
        {geojsonData && (
          <DistrictLayer
            geojsonData={geojsonData}
            selected={selected}
            setSelected={handleSelectDistrict}
            show={layers.showBoundaries}
            isDark={isDark}
          />
        )}

        {/* Heatmap — memoized, stays mounted, opacity-toggled */}
        <HeatLayer points={data.heatmap_points} show={layers.showHeatmap} />

        {/* Crime Bubbles / FIR Pins — memoized */}
        <BubbleLayer
          points={data.heatmap_points}
          zoomLevel={zoomLevel}
          show={layers.showBubbles}
        />

        {/* Police Station Clusters — memoized */}
        <PoliceStationLayer
          stations={data.police_stations}
          zoomLevel={zoomLevel}
          show={layers.showStations}
          onOpenInvestigation={onOpenInvestigation}
        />

        {/* DBSCAN Hotspot Rings — memoized */}
        <HotspotLayer
          hotspots={data.hotspots}
          show={layers.showHotspots}
          onOpenInvestigation={onOpenInvestigation}
        />

        {/* Controls */}
        <MapControls layers={layers} />
      </MapContainer>
    </div>
  );
}

export default CrimeMapInner;
