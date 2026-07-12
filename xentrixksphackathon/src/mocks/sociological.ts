import { int, resetSeed } from "./rng";

export interface SociologicalInsights {
  byAge: { band: string; count: number }[];
  byGender: { gender: string; count: number }[];
  bySocioEconomic: { district: string; sei: number; crimeRate: number }[];
  callouts: { title: string; detail: string }[];
}

export function generateSociological(): SociologicalInsights {
  resetSeed(9021);
  const byAge = [
    { band: "<18", count: int(120, 180) },
    { band: "18–25", count: int(600, 800) },
    { band: "26–35", count: int(800, 1000) },
    { band: "36–45", count: int(500, 700) },
    { band: "46–60", count: int(250, 380) },
    { band: "60+", count: int(60, 120) },
  ];
  const byGender = [
    { gender: "Male", count: int(2400, 2700) },
    { gender: "Female", count: int(320, 480) },
    { gender: "Other / Undisclosed", count: int(20, 45) },
  ];
  const districts = [
    "Bengaluru Urban",
    "Mysuru",
    "Mangaluru",
    "Belagavi",
    "Kalaburagi",
    "Hubballi-Dharwad",
    "Tumakuru",
    "Shivamogga",
    "Ballari",
    "Vijayapura",
  ];
  const bySocioEconomic = districts.map((d) => ({
    district: d,
    sei: int(35, 88),
    crimeRate: int(22, 96),
  }));
  const callouts = [
    {
      title: "Urban migration → property crime",
      detail:
        "Districts with >15% inbound migration show 18% higher property-crime rate; Bengaluru Urban and Mangaluru lead.",
    },
    {
      title: "Youth unemployment correlation",
      detail:
        "Sub-districts with youth unemployment above 12% correlate with a 24% uplift in petty theft FIRs.",
    },
    {
      title: "Digital literacy gap",
      detail:
        "Cyber-fraud victimisation is 2.1× higher in senior-citizen cohorts in tier-2 districts.",
    },
    {
      title: "Nightlife density",
      detail:
        "Assault FIRs cluster within 500m of licensed nightlife venues on Fri–Sat between 22:00–02:00.",
    },
  ];
  return { byAge, byGender, bySocioEconomic, callouts };
}
