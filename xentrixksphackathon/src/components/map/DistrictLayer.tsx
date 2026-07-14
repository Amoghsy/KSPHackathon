import { GeoJSON } from "react-leaflet";
import { useRef, useEffect } from "react";

interface DistrictLayerProps {
  geojsonData: any;
  selected: string | null;
  setSelected: (district: string | null) => void;
  show: boolean;
  isDark: boolean;
}

export function DistrictLayer({
  geojsonData,
  selected,
  setSelected,
  show,
  isDark,
}: DistrictLayerProps) {
  // Keep a ref to each named Leaflet layer so we can style them imperatively
  const layerMapRef = useRef<Record<string, any>>({});

  // Theme-aware colour tokens
  const colors = {
    selected: {
      fill: isDark ? "#3B82F6" : "#1D4ED8",
      fillOpacity: isDark ? 0.22 : 0.15,
      border: isDark ? "#3B82F6" : "#1D4ED8",
      weight: 2.5,
      dashArray: "",
    },
    default: {
      fill: isDark ? "#475569" : "#334155",
      fillOpacity: isDark ? 0.06 : 0.04,
      border: isDark ? "#64748B" : "#475569",
      weight: 1.2,
      dashArray: "4 3",
    },
    hover: {
      fillOpacity: isDark ? 0.16 : 0.12,
      border: isDark ? "#94A3B8" : "#64748B",
    },
  };

  // Imperatively update district styles when `selected` or `isDark` changes —
  // NO remount, no flicker.
  useEffect(() => {
    const layers = layerMapRef.current;
    Object.keys(layers).forEach((name) => {
      const layer = layers[name];
      if (!layer) return;
      const isSelected = selected === name;
      const c = isSelected ? colors.selected : colors.default;
      layer.setStyle({
        fillColor: c.fill,
        fillOpacity: c.fillOpacity,
        color: c.border,
        weight: c.weight,
        dashArray: c.dashArray,
      });
    });
  }, [selected, isDark]);

  if (!show || !geojsonData) return null;

  const geojsonStyle = (feature: any) => {
    const isSelected = selected === feature.properties.name;
    const c = isSelected ? colors.selected : colors.default;
    return {
      fillColor: c.fill,
      fillOpacity: c.fillOpacity,
      color: c.border,
      weight: c.weight,
      dashArray: c.dashArray,
    };
  };

  const onEachFeature = (feature: any, layer: any) => {
    const name: string = feature.properties.name;

    // Register layer so imperative effect can reach it
    layerMapRef.current[name] = layer;

    layer.bindTooltip(name, {
      permanent: false,
      sticky: true,
      className: "leaflet-district-tooltip",
      direction: "center",
    });

    layer.on({
      mouseover: (e: any) => {
        if (selected !== name) {
          e.target.setStyle({
            fillOpacity: colors.hover.fillOpacity,
            color: colors.hover.border,
            weight: 1.8,
          });
        }
      },
      mouseout: (e: any) => {
        if (selected !== name) {
          e.target.setStyle({
            fillOpacity: colors.default.fillOpacity,
            color: colors.default.border,
            weight: colors.default.weight,
          });
        }
      },
      click: () => {
        setSelected(name);
      },
    });
  };

  return (
    <GeoJSON
      // key only changes on theme switch — NOT on district selection
      key={`districts-${isDark}`}
      data={geojsonData}
      style={geojsonStyle}
      onEachFeature={onEachFeature}
    />
  );
}
