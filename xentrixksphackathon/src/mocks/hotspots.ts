import { DISTRICTS } from "./firs";

export interface Hotspot {
  district: string;
  x: number; // 0-100 (svg coord)
  y: number;
  intensity: number; // 0-100
  cases: number;
  dominant: string;
  trend: number; // % change
}

// Rough relative positions of KA districts on a stylised map (not geographic)
// Positions in the same 0..100 viewBox used by the Karnataka SVG path
const POS: Record<string, [number, number]> = {
  "Bengaluru Urban": [67.15, 77.93],
  "Bengaluru Rural": [68.65, 74.52],
  Mysuru: [54.3, 87.09],
  Mangaluru: [29.71, 79.3],
  Belagavi: [24.93, 38.58],
  Kalaburagi: [56.76, 18.36],
  "Hubballi-Dharwad": [33.4, 45.27],
  Tumakuru: [60.45, 72.88],
  Shivamogga: [39.41, 64.81],
  Ballari: [57.99, 48.28],
  Vijayapura: [41.6, 25.19],
  Udupi: [28.2, 72.88],
  Chitradurga: [50.89, 60.71],
  Hassan: [46.79, 77.52],
};


const CRIME_DOM = ["Theft", "Vehicle Theft", "Cybercrime", "Robbery", "Cheating"];

export function generateHotspots(): Hotspot[] {
  return DISTRICTS.map((d, i) => {
    const p = POS[d] ?? [50, 50];
    return {
      district: d,
      x: p[0],
      y: p[1],
      intensity: 25 + ((i * 37) % 75),
      cases: 40 + ((i * 53) % 220),
      dominant: CRIME_DOM[i % CRIME_DOM.length],
      trend: (i % 2 === 0 ? 1 : -1) * (2 + (i % 9)),
    };
  });
}
