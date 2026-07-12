import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { PageHeader } from "@/components/app/primitives";
import { MockBadge } from "@/components/app/mock-badge";
import { getAudit } from "@/services/api";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { format } from "date-fns";

export const Route = createFileRoute("/_app/audit")({
  head: () => ({ meta: [{ title: "Audit Log — Crime Intelligence Assistant" }] }),
  component: AuditPage,
});

const PAGE_SIZE = 20;

function AuditPage() {
  const { data, isLoading } = useQuery({ queryKey: ["audit"], queryFn: getAudit });
  const [page, setPage] = useState(1);
  const rows = data ?? [];
  const start = (page - 1) * PAGE_SIZE;
  const paged = rows.slice(start, start + PAGE_SIZE);
  const totalPages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));

  return (
    <div className="p-6 max-w-[1400px] mx-auto">
      <PageHeader
        title="Audit Log"
        subtitle="Read-only record of every query executed against the crime database."
        actions={<MockBadge />}
      />

      <div className="rounded-xl glass overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="bg-muted/60 border-b border-border">
              <tr>
                <th className="text-left px-3 py-2 font-medium">Timestamp</th>
                <th className="text-left px-3 py-2 font-medium">User</th>
                <th className="text-left px-3 py-2 font-medium">Role</th>
                <th className="text-left px-3 py-2 font-medium">Action</th>
                <th className="text-left px-3 py-2 font-medium">Query</th>
                <th className="text-right px-3 py-2 font-medium">Rows</th>
              </tr>
            </thead>
            <tbody>
              {isLoading &&
                Array.from({ length: 10 }).map((_, i) => (
                  <tr key={i} className="border-b border-border">
                    <td colSpan={6} className="p-2">
                      <Skeleton className="h-6" />
                    </td>
                  </tr>
                ))}
              {paged.map((r) => (
                <tr key={r.id} className="border-b border-border hover:bg-accent/40">
                  <td className="px-3 py-2 whitespace-nowrap tabular-nums">
                    {format(new Date(r.ts), "d MMM · HH:mm:ss")}
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap">{r.user}</td>
                  <td className="px-3 py-2">
                    <Badge variant="outline" className="text-[10px]">
                      {r.role}
                    </Badge>
                  </td>
                  <td className="px-3 py-2 font-mono text-[11px]">{r.action}</td>
                  <td className="px-3 py-2 font-mono text-[11px] text-muted-foreground max-w-xl truncate">
                    {r.query}
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums">{r.rows}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="flex items-center justify-between px-3 py-2 border-t border-border text-xs text-muted-foreground">
          <span>
            Showing {start + 1}–{Math.min(start + PAGE_SIZE, rows.length)} of {rows.length}
          </span>
          <div className="flex gap-1">
            <Button size="sm" variant="outline" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>
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
