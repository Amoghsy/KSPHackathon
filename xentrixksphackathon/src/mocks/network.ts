import { int, resetSeed } from "./rng";

export type NodeKind = "accused" | "victim" | "location" | "case";
export interface GraphNode {
  id: string;
  label: string;
  kind: NodeKind;
}
export interface GraphLink {
  source: string;
  target: string;
  label?: string;
}

export function generateNetwork(): { nodes: GraphNode[]; links: GraphLink[] } {
  resetSeed(3131);
  const nodes: GraphNode[] = [];
  const links: GraphLink[] = [];

  // Ring cluster around A12
  const ring = ["A12", "A15", "A19", "A22", "A27", "A31"];
  ring.forEach((id, i) =>
    nodes.push({ id, label: `Accused ${id}`, kind: "accused" }),
  );
  const cases = ["C201", "C204", "C219", "C231"];
  cases.forEach((id) => nodes.push({ id, label: id, kind: "case" }));
  const locs = ["L-Whitefield", "L-KRPuram", "L-Marathahalli"];
  locs.forEach((id) => nodes.push({ id, label: id.slice(2), kind: "location" }));
  const victims = ["V1", "V2", "V3", "V4"];
  victims.forEach((id) => nodes.push({ id, label: `Victim ${id}`, kind: "victim" }));

  // links inside ring
  for (let i = 0; i < ring.length; i++) {
    for (let j = i + 1; j < ring.length; j++) {
      if (Math.random() > 0.45)
        links.push({ source: ring[i], target: ring[j], label: "co-accused" });
    }
  }
  cases.forEach((c) => {
    const k = int(2, 4);
    for (let i = 0; i < k; i++) {
      links.push({ source: ring[i % ring.length], target: c });
    }
    links.push({ source: c, target: locs[int(0, locs.length - 1)] });
    links.push({ source: c, target: victims[int(0, victims.length - 1)] });
  });

  // Peripheral offenders
  for (let i = 0; i < 12; i++) {
    const id = `A${100 + i}`;
    nodes.push({ id, label: `Accused ${id}`, kind: "accused" });
    const target = Math.random() > 0.5 ? ring[int(0, ring.length - 1)] : cases[int(0, cases.length - 1)];
    links.push({ source: id, target });
  }

  return { nodes, links };
}
