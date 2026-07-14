import { useEffect, useRef, memo } from "react";
import { useMap } from "react-leaflet";
import L from "leaflet";

interface HeatLayerProps {
  points: Array<{
    latitude: number;
    longitude: number;
    crime_type: string;
    gravity: number;
    district: string;
  }>;
  show: boolean;
}

export const HeatLayer = memo(function HeatLayer({ points, show }: HeatLayerProps) {
  const map = useMap();
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    if (!show) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      return;
    }

    const render = () => {
      const size = map.getSize();
      canvas.width = size.x;
      canvas.height = size.y;
      ctx.clearRect(0, 0, size.x, size.y);

      points.forEach((p) => {
        if (!p.latitude || !p.longitude) return;
        const latLng = L.latLng(p.latitude, p.longitude);
        const pixel = map.latLngToContainerPoint(latLng);

        // Dynamically adjust radius by zoom level
        const zoom = map.getZoom();
        const rad = zoom >= 11 ? 40 : zoom >= 9 ? 28 : 18;

        const grad = ctx.createRadialGradient(pixel.x, pixel.y, 2, pixel.x, pixel.y, rad);

        // Severity mapping (Grievous=4, High=3, Medium=2, Low=1)
        const weight = p.gravity === 4 ? 0.85 : p.gravity === 3 ? 0.65 : p.gravity === 2 ? 0.4 : 0.25;

        grad.addColorStop(0, `rgba(239, 68, 68, ${weight})`);
        grad.addColorStop(0.2, `rgba(249, 115, 22, ${weight * 0.65})`);
        grad.addColorStop(0.5, `rgba(234, 179, 8, ${weight * 0.25})`);
        grad.addColorStop(1, "rgba(0, 0, 0, 0)");

        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(pixel.x, pixel.y, rad, 0, Math.PI * 2);
        ctx.fill();
      });
    };

    render();
    map.on("move", render);
    map.on("zoom", render);
    map.on("resize", render);

    return () => {
      map.off("move", render);
      map.off("zoom", render);
      map.off("resize", render);
    };
  }, [map, points, show]);

  // Always render the canvas element — control visibility via CSS opacity
  // Avoids mount/unmount flicker when toggling
  return (
    <canvas
      ref={canvasRef}
      className="pointer-events-none absolute inset-0 z-[400]"
      style={{
        mixBlendMode: "screen",
        opacity: show ? 0.75 : 0,
        transition: "opacity 0.2s ease",
      }}
    />
  );
});
