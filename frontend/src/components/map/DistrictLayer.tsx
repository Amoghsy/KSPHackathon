import { GeoJSON } from "react-leaflet";
import { useRef, useEffect, useMemo } from "react";

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
  const colors = useMemo(() => ({
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
  }), [isDark]);

  // Imperatively update district styles when selected, colors, or show changes.
  // Instead of unmounting the layer when show is false, we set styling to transparent.
  // This avoids unmount/remount lag and prevents "setStyle of undefined" errors.
  useEffect(() => {
    const layers = layerMapRef.current;
    Object.keys(layers).forEach((name) => {
      // Skip internal properties stored on the ref
      if (name.startsWith("__")) return;
      const layer = layers[name];
      if (!layer) return;
      
      const isSelected = selected === name;
      const c = isSelected ? colors.selected : colors.default;
      
      layer.setStyle({
        fillColor: show ? c.fill : "transparent",
        fillOpacity: show ? c.fillOpacity : 0,
        color: show ? c.border : "transparent",
        weight: show ? c.weight : 0,
        dashArray: c.dashArray,
      });

      // Update tooltip binding based on visibility
      if (!show) {
        layer.closeTooltip();
      }
    });
  }, [selected, colors, show]);

  if (!geojsonData) return null;

  // Render the GeoJSON element ONCE per theme switch.
  // It is NOT re-rendered or reconciled when the selected district changes.
  const geojsonElement = useMemo(() => {
    const geojsonStyle = (feature: any) => {
      const isSelected = selected === feature.properties.name;
      const c = isSelected ? colors.selected : colors.default;
      return {
        fillColor: show ? c.fill : "transparent",
        fillOpacity: show ? c.fillOpacity : 0,
        color: show ? c.border : "transparent",
        weight: show ? c.weight : 0,
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
          // Only apply hover styling if boundaries are toggled ON
          if (!layerMapRef.current.__showBoundaries) return;
          if (layerMapRef.current.__selectedDistrict !== name) {
            e.target.setStyle({
              fillOpacity: colors.hover.fillOpacity,
              color: colors.hover.border,
              weight: 1.8,
            });
          }
        },
        mouseout: (e: any) => {
          if (!layerMapRef.current.__showBoundaries) return;
          const currentSelected = layerMapRef.current.__selectedDistrict;
          const isSel = currentSelected === name;
          const c = isSel ? colors.selected : colors.default;
          e.target.setStyle({
            fillOpacity: c.fillOpacity,
            color: c.border,
            weight: c.weight,
            dashArray: c.dashArray,
          });
        },
        click: () => {
          if (!layerMapRef.current.__showBoundaries) return;
          setSelected(name);
        },
      });
    };

    return (
      <GeoJSON
        key={`districts-${isDark}`}
        data={geojsonData}
        style={geojsonStyle}
        onEachFeature={onEachFeature}
      />
    );
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [geojsonData, isDark, colors, setSelected]);

  // Keep references to values on the ref object so event handlers can read them dynamically
  // without needing to re-register the event listeners or recreate the GeoJSON layer
  layerMapRef.current.__selectedDistrict = selected;
  layerMapRef.current.__showBoundaries = show;

  return geojsonElement;
}
