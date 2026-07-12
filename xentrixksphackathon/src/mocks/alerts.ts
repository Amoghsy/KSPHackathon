export interface AlertItem {
  id: string;
  severity: "Info" | "Warning" | "Critical";
  title: string;
  area: string;
  detail: string;
  ts: string;
}

export const ALERTS: AlertItem[] = [
  {
    id: "AL-1041",
    severity: "Critical",
    title: "Repeat offender re-arrested",
    area: "Whitefield, Bengaluru Urban",
    detail: "Accused A12 (5 prior FIRs) apprehended in connection with FIR 1044300062026 00087.",
    ts: "2026-06-30T09:14:00Z",
  },
  {
    id: "AL-1040",
    severity: "Warning",
    title: "Spike in vehicle theft",
    area: "Whitefield zone",
    detail: "38% increase in two-wheeler theft in the last 7 days vs. prior 4-week average.",
    ts: "2026-06-29T18:02:00Z",
  },
  {
    id: "AL-1039",
    severity: "Warning",
    title: "Cybercrime cluster detected",
    area: "Mangaluru",
    detail: "12 UPI-fraud FIRs share common beneficiary account patterns.",
    ts: "2026-06-28T12:20:00Z",
  },
  {
    id: "AL-1038",
    severity: "Info",
    title: "New MO tag emerging",
    area: "Mysuru",
    detail: "Impersonation-based bank frauds show consistent script; 6 FIRs this month.",
    ts: "2026-06-27T08:47:00Z",
  },
  {
    id: "AL-1037",
    severity: "Critical",
    title: "Narcotics network activity",
    area: "Belagavi-Vijayapura corridor",
    detail: "Coordinated seizures suggest active supply chain; further surveillance recommended.",
    ts: "2026-06-25T22:11:00Z",
  },
];
