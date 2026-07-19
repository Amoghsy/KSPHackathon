import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { PageHeader } from "@/components/app/primitives";
import { listFIRs, getCasesMetadata } from "@/services/api";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/stores/auth";
import { hasPermission, PERMISSIONS } from "@/lib/rbac";
import { MaskField, PermissionCard, RestrictedButton } from "@/components/rbac/permission";

const STATUSES = ["Under Investigation", "Charge Sheeted", "Closed", "Undetected"] as const;

const DISTRICTS = [
  "Bengaluru Urban", "Bengaluru Rural", "Mysuru", "Mangaluru", "Belagavi",
  "Kalaburagi", "Hubballi-Dharwad", "Tumakuru", "Shivamogga", "Ballari",
  "Vijayapura", "Udupi", "Chitradurga", "Hassan",
];

export const Route = createFileRoute("/_app/cases/")({
  head: () => ({ meta: [{ title: "Case Search — Crime Intelligence Assistant" }] }),
  component: CasesPage,
});

function statusBadge(s: string) {
  switch (s) {
    case "Under Investigation":
      return "bg-info/15 text-info border-info/30";
    case "Charge Sheeted":
      return "bg-success/15 text-success border-success/30";
    case "Closed":
      return "bg-muted text-muted-foreground border-border";
    case "Undetected":
      return "bg-destructive/10 text-destructive border-destructive/30";
    default:
      return "bg-muted";
  }
}

function CasesPage() {
  const user = useAuthStore((s) => s.user);
  const canSeeSensitive = hasPermission(user, PERMISSIONS.SENSITIVE_CASE_ACCESS);
  const hideVictimColumn = user?.role === "POLICY_MAKER";

  const { data: metadata } = useQuery({
    queryKey: ["casesMetadata"],
    queryFn: getCasesMetadata,
    staleTime: Infinity,
  });

  const districtsList = metadata?.districts ?? DISTRICTS;
  const statusesList = metadata?.statuses ?? STATUSES;

  const districtOptions = user?.assignedDistricts?.length ? user.assignedDistricts : districtsList;
  const [q, setQ] = useState("");
  const [status, setStatus] = useState<string>("All");
  const [district, setDistrict] = useState<string>("All");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["firs", { q, status, district, page }],
    queryFn: () => listFIRs({ q, status, district, page, pageSize: 15 }),
  });

  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / 15));

  return (
    <div className="p-6 max-w-[1600px] mx-auto">
      <PageHeader
        title="Case Search"
        subtitle={`${total.toLocaleString()} FIRs indexed - scoped to ${user?.assignedDistricts?.length ? user.assignedDistricts.join(", ") : "authorized Karnataka districts"}.`}
        actions={
          <RestrictedButton size="sm" variant="outline" permissions={[PERMISSIONS.EXPORT_DATA]}>
            Export
          </RestrictedButton>
        }
      />

      <div className="flex flex-wrap items-end gap-3 mb-4">
        <div className="flex-1 min-w-64">
          <Input
            placeholder="Search Crime No, station, district, complainant…"
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              setPage(1);
            }}
          />
        </div>
        <div className="w-48">
          <Select
            value={status}
            onValueChange={(v) => {
              setStatus(v);
              setPage(1);
            }}
          >
            <SelectTrigger>
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="All">All statuses</SelectItem>
              {statusesList.map((s) => (
                <SelectItem key={s} value={s}>
                  {s}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="w-56">
          <Select
            value={district}
            onValueChange={(v) => {
              setDistrict(v);
              setPage(1);
            }}
          >
            <SelectTrigger>
              <SelectValue placeholder="District" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="All">All districts</SelectItem>
              {districtOptions.map((d) => (
                <SelectItem key={d} value={d}>
                  {d}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="rounded-xl glass overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="bg-muted/60 border-b border-border">
              <tr>
                <th className="text-left px-3 py-2 font-medium">Crime No.</th>
                <th className="text-left px-3 py-2 font-medium">Case No.</th>
                <th className="text-left px-3 py-2 font-medium">Date</th>
                {!hideVictimColumn && <th className="text-left px-3 py-2 font-medium">Victim</th>}
                <th className="text-left px-3 py-2 font-medium">Station</th>
                <th className="text-left px-3 py-2 font-medium">District</th>
                <th className="text-left px-3 py-2 font-medium">Crime Head</th>
                <th className="text-left px-3 py-2 font-medium">Status</th>
                <th className="text-left px-3 py-2 font-medium">Gravity</th>
              </tr>
            </thead>
            <tbody>
              {isLoading &&
                Array.from({ length: 8 }).map((_, i) => (
                  <tr key={i} className="border-b border-border">
                    <td colSpan={hideVictimColumn ? 8 : 9} className="p-2">
                      <Skeleton className="h-6" />
                    </td>
                  </tr>
                ))}
              {!isLoading && data?.items.length === 0 && (
                <tr>
                  <td colSpan={hideVictimColumn ? 8 : 9} className="p-8">
                    <PermissionCard
                      moduleName="Assigned Investigations"
                      reason={q || status !== "All" || district !== "All" ? "No assigned investigations match the current filters." : "You currently have no assigned investigations in your permitted scope."}
                      className="mx-auto max-w-xl text-left"
                    />
                  </td>
                </tr>
              )}
              {data?.items.map((f) => (
                <tr key={f.id} className="border-b border-border hover:bg-accent/40 cursor-pointer">
                  <td className="px-3 py-2">
                    <Link
                      to="/cases/$firId"
                      params={{ firId: f.id }}
                      className="font-mono text-primary hover:underline"
                    >
                      {f.crimeNo}
                    </Link>
                  </td>
                  <td className="px-3 py-2 font-mono text-[11px]">{f.caseNo}</td>
                  <td className="px-3 py-2 whitespace-nowrap">{f.date}</td>
                  {!hideVictimColumn && (
                    <td className="px-3 py-2">
                      <MaskField
                        value={(f as any).victimName ?? (f as any).complainant ?? "Victim record"}
                        permission={PERMISSIONS.SENSITIVE_CASE_ACCESS}
                        kind="name"
                      />
                      {!canSeeSensitive && (
                        <span className="ml-2 text-[10px] text-muted-foreground">masked</span>
                      )}
                    </td>
                  )}
                  <td className="px-3 py-2">{f.station}</td>
                  <td className="px-3 py-2">{f.district}</td>
                  <td className="px-3 py-2">{f.crimeHead}</td>
                  <td className="px-3 py-2">
                    <Badge
                      variant="outline"
                      className={cn("border font-medium", statusBadge(f.status))}
                    >
                      {f.status}
                    </Badge>
                  </td>
                  <td className="px-3 py-2">{f.gravity}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="flex items-center justify-between px-3 py-2 border-t border-border text-xs text-muted-foreground">
          <span>
            Page {page} of {totalPages}
          </span>
          <div className="flex gap-1">
            <Button
              size="sm"
              variant="outline"
              disabled={page === 1}
              onClick={() => setPage((p) => p - 1)}
            >
              Prev
            </Button>
            <Button
              size="sm"
              variant="outline"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
