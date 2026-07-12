import { ALL_FIRS, DISTRICTS } from "./firs";

export function generateDashboard() {
  const monthlyTrend = Array.from({ length: 12 }, (_, i) => {
    const month = new Date();
    month.setMonth(month.getMonth() - (11 - i));
    const key = month.toLocaleString("en", { month: "short" });
    return {
      month: key,
      Theft: 40 + Math.floor(Math.sin(i / 2) * 15) + i * 2,
      Robbery: 15 + Math.floor(Math.cos(i / 3) * 6) + Math.floor(i / 2),
      Cybercrime: 8 + i * 3 + Math.floor(Math.sin(i) * 4),
      Assault: 22 + Math.floor(Math.cos(i / 2) * 8),
    };
  });

  const districtCounts = DISTRICTS.map((d) => ({
    district: d,
    cases: ALL_FIRS.filter((f) => f.district === d).length,
  }))
    .sort((a, b) => b.cases - a.cases)
    .slice(0, 5);

  const statusBreakdown = ["Under Investigation", "Charge Sheeted", "Closed", "Undetected"].map(
    (s) => ({
      name: s,
      value: ALL_FIRS.filter((f) => f.status === s).length,
    }),
  );

  return {
    kpis: [
      { label: "Total Open Cases", value: 1284, delta: -2.4 },
      { label: "Cases This Month", value: 187, delta: 4.1 },
      { label: "Arrests This Week", value: 42, delta: 12.5 },
      { label: "Charge-Sheeted Cases", value: 96, delta: -1.2 },
      { label: "Repeat Offenders Flagged", value: 71, delta: 6.7 },
    ],
    monthlyTrend,
    districtCounts,
    statusBreakdown,
  };
}
