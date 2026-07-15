import { useState } from "react";

export function useCrimeMap() {
  const [zoomLevel, setZoomLevel] = useState(7);
  const [selectedDistrict, setSelectedDistrict] = useState<string | null>(null);

  // Filters
  const [crimeType, setCrimeType] = useState<string>("All");
  const [dateRange, setDateRange] = useState<string>("3650");
  const [selDistrict, setSelDistrict] = useState<string>("All");
  const [gravity, setGravity] = useState<string>("All");
  const [status, setStatus] = useState<string>("All");
  const [policeStation, setPoliceStation] = useState<string>("All");

  // Layers Toggles
  const [showHeatmap, setShowHeatmap] = useState(true);
  const [showBubbles, setShowBubbles] = useState(true);
  const [showStations, setShowStations] = useState(true);
  const [showHotspots, setShowHotspots] = useState(true);
  const [showBoundaries, setShowBoundaries] = useState(true);

  return {
    zoomLevel,
    setZoomLevel,
    selectedDistrict,
    setSelectedDistrict,
    filters: {
      crimeType,
      setCrimeType,
      dateRange,
      setDateRange,
      selDistrict,
      setSelDistrict,
      gravity,
      setGravity,
      status,
      setStatus,
      policeStation,
      setPoliceStation,
    },
    layers: {
      showHeatmap,
      setShowHeatmap,
      showBubbles,
      setShowBubbles,
      showStations,
      setShowStations,
      showHotspots,
      setShowHotspots,
      showBoundaries,
      setShowBoundaries,
    }
  };
}
export type UseCrimeMapReturn = ReturnType<typeof useCrimeMap>;
