export interface AuditRow {
  id: string;
  ts: string;
  user: string;
  role: string;
  action: string;
  query: string;
  rows: number;
}

export const AUDIT_ROWS: AuditRow[] = Array.from({ length: 60 }, (_, i) => {
  const d = new Date();
  d.setMinutes(d.getMinutes() - i * 27);
  const samples = [
    "SELECT * FROM firs WHERE crime_head = 'Theft' AND district = 'Bengaluru Urban'",
    "SELECT accused_id, COUNT(*) FROM fir_accused GROUP BY accused_id HAVING COUNT(*) >= 3",
    "SELECT * FROM firs WHERE date >= CURRENT_DATE - INTERVAL '30 days'",
    "SELECT district, COUNT(*) FROM firs WHERE crime_head = 'Robbery' GROUP BY district",
    "SELECT * FROM offenders WHERE risk_score > 70",
  ];
  const users = [
    { u: "Insp. Arjun Rao", r: "Investigator" },
    { u: "Priya Kulkarni", r: "Analyst" },
    { u: "SP Ramesh Iyer", r: "Supervisor" },
    { u: "Dr. Anitha Menon", r: "Policymaker" },
  ];
  const p = users[i % users.length];
  return {
    id: `AU-${9000 + i}`,
    ts: d.toISOString(),
    user: p.u,
    role: p.r,
    action: "NL_QUERY",
    query: samples[i % samples.length],
    rows: 3 + ((i * 7) % 120),
  };
});
