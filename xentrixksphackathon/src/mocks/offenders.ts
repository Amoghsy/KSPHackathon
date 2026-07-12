import { ALL_FIRS } from "./firs";
import { int, pick, resetSeed } from "./rng";

export interface Offender {
  id: string;
  name: string;
  age: number;
  linkedCases: number;
  riskScore: number; // 0-100
  risk: "Low" | "Medium" | "High";
  modusOperandi: string[];
  aliases: string[];
  lastKnown: string;
  factors: { label: string; value: number }[];
}

const MO_TAGS = [
  "Vehicle-borne",
  "Nighttime",
  "Group of 3+",
  "Weapon: knife",
  "Cyber-enabled",
  "Insider info",
  "Repeat station",
  "Impersonation",
  "Drug-linked",
];

export function generateOffenders(count = 48): Offender[] {
  resetSeed(777);
  return Array.from({ length: count }, (_, i) => {
    const score = int(15, 95);
    const risk = score > 70 ? "High" : score > 45 ? "Medium" : "Low";
    const name = ALL_FIRS[i % ALL_FIRS.length].accused[0]?.name ?? "Unknown";
    return {
      id: `OFF${i + 1}`,
      name,
      age: int(19, 55),
      linkedCases: int(1, 9),
      riskScore: score,
      risk,
      modusOperandi: Array.from({ length: int(2, 4) }, () => pick(MO_TAGS)),
      aliases: [name.split(" ")[0]],
      lastKnown: pick([
        "Bengaluru Urban",
        "Mysuru",
        "Mangaluru",
        "Belagavi",
        "Kalaburagi",
      ]),
      factors: [
        { label: "Prior convictions", value: int(20, 90) },
        { label: "Case severity", value: int(30, 95) },
        { label: "Repeat locations", value: int(10, 80) },
        { label: "Network density", value: int(20, 85) },
      ],
    };
  });
}

export const ALL_OFFENDERS = generateOffenders();
