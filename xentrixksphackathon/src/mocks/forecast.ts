import { int, resetSeed } from "./rng";

export type ForecastCrime = "Robbery" | "Theft" | "Cybercrime" | "Assault";

export interface ForecastPoint {
  week: string;
  actual: number | null;
  forecast: number | null;
  band?: [number, number]; // for recharts Area (lower, upper)
}

const BASE: Record<ForecastCrime, number> = {
  Robbery: 22,
  Theft: 65,
  Cybercrime: 41,
  Assault: 33,
};

export function generateForecast(crime: ForecastCrime): ForecastPoint[] {
  resetSeed(crime.length * 131 + BASE[crime]);
  const points: ForecastPoint[] = [];
  const base = BASE[crime];

  // 8 actual weeks
  for (let i = 1; i <= 8; i++) {
    const v = base + int(-6, 8) + i * (crime === "Cybercrime" ? 2 : 1);
    points.push({ week: `W${i}`, actual: v, forecast: null });
  }
  // pivot week: actual = forecast
  const lastActual = points[points.length - 1].actual!;
  points[points.length - 1].forecast = lastActual;
  points[points.length - 1].band = [lastActual, lastActual];

  // 4 forecast weeks
  for (let i = 9; i <= 12; i++) {
    const trend = lastActual + (i - 8) * (crime === "Cybercrime" ? 3 : 1.5);
    const spread = 4 + (i - 8) * 2;
    points.push({
      week: `W${i}`,
      actual: null,
      forecast: Math.round(trend),
      band: [Math.round(trend - spread), Math.round(trend + spread)],
    });
  }

  return points;
}

export function forecastCommentary(crime: ForecastCrime, points: ForecastPoint[]): string {
  const forecastOnly = points.filter((p) => p.actual === null);
  const first = forecastOnly[0]?.forecast ?? 0;
  const last = forecastOnly[forecastOnly.length - 1]?.forecast ?? 0;
  const delta = last - first;
  if (delta > 6)
    return `${crime} counts are projected to exceed the upper confidence bound over the next 4 weeks — early warning triggered.`;
  if (delta < -3)
    return `${crime} counts trend downward within the forecast interval — no action required.`;
  return `${crime} counts remain within the expected confidence interval over the next 4 weeks.`;
}
