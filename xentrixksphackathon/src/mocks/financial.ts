import { int, resetSeed } from "./rng";

export type FinNodeKind = "accused" | "account" | "case" | "location";
export interface FinNode {
  id: string;
  label: string;
  kind: FinNodeKind;
  bank?: string;
}
export interface FinLink {
  source: string;
  target: string;
  label?: string;
  amount?: number;
  suspicious?: boolean;
  reason?: string;
}

export function generateFinancialNetwork(): { nodes: FinNode[]; links: FinLink[] } {
  resetSeed(7717);
  const nodes: FinNode[] = [];
  const links: FinLink[] = [];

  const accused = ["A12", "A19", "A22", "A27", "A31", "A44"];
  accused.forEach((id) => nodes.push({ id, label: `Accused ${id}`, kind: "accused" }));

  const banks = ["SBI", "HDFC", "ICICI", "Kotak", "Axis"];
  const accounts = Array.from({ length: 10 }, (_, i) => {
    const id = `ACC-${5000 + i}`;
    const bank = banks[i % banks.length];
    nodes.push({ id, label: `${bank} ••${1000 + i * 37}`, kind: "account", bank });
    return id;
  });

  const cases = ["C201", "C204", "C219", "C231"];
  cases.forEach((id) => nodes.push({ id, label: id, kind: "case" }));

  const locs = ["L-Whitefield", "L-Mangaluru"];
  locs.forEach((id) => nodes.push({ id, label: id.slice(2), kind: "location" }));

  // Accused → account ownership
  accused.forEach((a, i) => {
    links.push({ source: a, target: accounts[i], label: "owns" });
    links.push({ source: a, target: accounts[(i + 3) % accounts.length], label: "signatory" });
  });

  // Account → account transactions
  for (let i = 0; i < accounts.length; i++) {
    for (let j = 0; j < accounts.length; j++) {
      if (i === j) continue;
      if (Math.random() > 0.72) {
        const amount = int(15000, 850000);
        const suspicious = amount > 500000 || Math.random() > 0.85;
        const reasons = [
          "Amount above ₹5L structuring threshold",
          "Rapid round-trip (< 60s)",
          "Beneficiary shared with 3 prior fraud FIRs",
          "Same-day layering across 4 accounts",
        ];
        links.push({
          source: accounts[i],
          target: accounts[j],
          label: "transfer",
          amount,
          suspicious,
          reason: suspicious ? reasons[int(0, reasons.length - 1)] : undefined,
        });
      }
    }
  }

  // Accounts linked to cases + locations
  cases.forEach((c, i) => {
    links.push({ source: accounts[i], target: c, label: "linked" });
    links.push({ source: c, target: locs[i % locs.length] });
  });

  return { nodes, links };
}
