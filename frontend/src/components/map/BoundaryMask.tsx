import { Polygon } from "react-leaflet";
import L from "leaflet";
import { memo, useMemo } from "react";

interface BoundaryMaskProps {
  geojsonData: any;
  isDark: boolean;
}

export const BoundaryMask = memo(function BoundaryMask({ geojsonData, isDark }: BoundaryMaskProps) {
  if (!geojsonData || !geojsonData.features) return null;

  // Memoize coordinates calculation so we don't parse 2.8MB on every parent render
  const rings = useMemo(() => {
    // World exterior ring — covers everything outside Karnataka
    const worldExterior: L.LatLngExpression[] = [
      [-90, -180],
      [-90, 180],
      [90, 180],
      [90, -180],
      [-90, -180],
    ];

    const tempRings: L.LatLngExpression[][] = [worldExterior];

    // Extract each district's polygon coordinates as interior rings (holes)
    // so Karnataka itself remains visible and interactive
    geojsonData.features.forEach((feature: any) => {
      const { geometry } = feature;
      if (geometry.type === "Polygon") {
        geometry.coordinates.forEach((ring: any[]) => {
          const latLngs = ring.map(
            (coord) => [coord[1], coord[0]] as [number, number]
          );
          tempRings.push(latLngs);
        });
      } else if (geometry.type === "MultiPolygon") {
        geometry.coordinates.forEach((poly: any[][]) => {
          poly.forEach((ring: any[]) => {
            const latLngs = ring.map(
              (coord) => [coord[1], coord[0]] as [number, number]
            );
            tempRings.push(latLngs);
          });
        });
      }
    });

    return tempRings;
  }, [geojsonData]);

  const pathOptions = useMemo(() => ({
    // Dark mode: heavy dark overlay. Light mode: elegant dark-shadow overlay.
    fillColor: "#020617",
    fillOpacity: isDark ? 0.85 : 0.45,
    stroke: false, // No borders drawn by the mask polygon itself
    interactive: false, // click events pass through to underlying layers
  }), [isDark]);

  return (
    <Polygon
      positions={rings as L.LatLngExpression[][]}
      pathOptions={pathOptions}
    />
  );
});
