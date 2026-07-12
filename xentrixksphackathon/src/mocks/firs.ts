import { int, pick, resetSeed } from "./rng";

export const DISTRICTS = [
  "Bengaluru Urban",
  "Bengaluru Rural",
  "Mysuru",
  "Mangaluru",
  "Belagavi",
  "Kalaburagi",
  "Hubballi-Dharwad",
  "Tumakuru",
  "Shivamogga",
  "Ballari",
  "Vijayapura",
  "Udupi",
  "Chitradurga",
  "Hassan",
];

export const STATIONS = [
  "Whitefield PS",
  "Koramangala PS",
  "MG Road PS",
  "Jayanagar PS",
  "Yeshwanthpur PS",
  "Mysuru North PS",
  "Mangaluru Central PS",
  "Belagavi City PS",
  "Kalaburagi PS",
  "Hubballi East PS",
];

export const CRIME_HEADS = [
  "Theft",
  "Robbery",
  "Burglary",
  "Assault",
  "Cheating",
  "Cybercrime",
  "Narcotics",
  "Vehicle Theft",
  "Kidnapping",
  "Fraud",
];

export const STATUSES = [
  "Under Investigation",
  "Charge Sheeted",
  "Closed",
  "Undetected",
] as const;

export const GRAVITY = ["Low", "Medium", "High", "Grievous"] as const;

const FIRST_NAMES = [
  "Arjun", "Priya", "Ravi", "Suresh", "Meera", "Karthik", "Divya", "Rahul",
  "Anitha", "Manoj", "Lakshmi", "Vikram", "Sneha", "Rajesh", "Kavya",
  "Prakash", "Deepa", "Shreya", "Ganesh", "Nithya", "Harish", "Sunitha",
  "Vinay", "Rohit", "Anusha", "Basava", "Chetan", "Mahesh",
];
const LAST_NAMES = [
  "Kumar", "Rao", "Shetty", "Reddy", "Naik", "Patil", "Gowda", "Iyer",
  "Hegde", "Bhat", "Kulkarni", "Murthy", "Nayak", "Singh", "Prasad",
];

export function firNumber(i: number, year = 2026) {
  // Format similar to sample: 1044300062026NNNNN
  const stationCode = String(1044300 + int(0, 99)).padStart(7, "0");
  const seq = String(i + 1).padStart(5, "0");
  return `${stationCode}06${year}${seq}`;
}

export function fullName() {
  return `${pick(FIRST_NAMES)} ${pick(LAST_NAMES)}`;
}

export interface FIR {
  id: string;
  crimeNo: string;
  caseNo: string;
  date: string;
  station: string;
  district: string;
  crimeHead: string;
  status: (typeof STATUSES)[number];
  gravity: (typeof GRAVITY)[number];
  complainant: string;
  accused: { id: string; name: string; age: number }[];
  victims: { name: string; age: number }[];
  actsSections: string[];
  arrests: { name: string; date: string }[];
  chargesheet: string | null;
  narrative: string;
  timeline: { label: string; date: string; done: boolean }[];
}

function isoDaysAgo(d: number) {
  const t = new Date();
  t.setDate(t.getDate() - d);
  return t.toISOString().slice(0, 10);
}

export function generateFIRs(count = 120): FIR[] {
  resetSeed(101);
  const items: FIR[] = [];
  for (let i = 0; i < count; i++) {
    const daysAgo = int(0, 240);
    const status = pick(STATUSES);
    const accusedCount = int(1, 4);
    const accused = Array.from({ length: accusedCount }, (_, k) => ({
      id: `A${1000 + i * 10 + k}`,
      name: fullName(),
      age: int(19, 55),
    }));
    const arrests =
      status !== "Undetected" && status !== "Under Investigation"
        ? accused.slice(0, int(1, accusedCount)).map((a) => ({
            name: a.name,
            date: isoDaysAgo(int(0, daysAgo)),
          }))
        : [];
    items.push({
      id: `FIR${i + 1}`,
      crimeNo: firNumber(i),
      caseNo: `CC/${2000 + i}/2026`,
      date: isoDaysAgo(daysAgo),
      station: pick(STATIONS),
      district: pick(DISTRICTS),
      crimeHead: pick(CRIME_HEADS),
      status,
      gravity: pick(GRAVITY),
      complainant: fullName(),
      accused,
      victims: Array.from({ length: int(1, 3) }, () => ({
        name: fullName(),
        age: int(15, 65),
      })),
      actsSections: ["IPC 379", "IPC 411"].slice(0, int(1, 2)),
      arrests,
      chargesheet:
        status === "Charge Sheeted" ? `CS/${3000 + i}/2026 dated ${isoDaysAgo(int(0, 30))}` : null,
      narrative:
        "Complainant reported the incident at the local police station. Investigation is being conducted as per procedure under the applicable sections.",
      timeline: [
        { label: "FIR Registered", date: isoDaysAgo(daysAgo), done: true },
        { label: "Investigation Assigned", date: isoDaysAgo(daysAgo - 1), done: true },
        {
          label: "Arrest",
          date: arrests[0]?.date ?? "",
          done: arrests.length > 0,
        },
        {
          label: "Chargesheet Filed",
          date: status === "Charge Sheeted" ? isoDaysAgo(int(0, 30)) : "",
          done: status === "Charge Sheeted",
        },
        { label: "Court Proceedings", date: "", done: false },
      ],
    });
  }
  return items;
}

export const ALL_FIRS = generateFIRs(120);
