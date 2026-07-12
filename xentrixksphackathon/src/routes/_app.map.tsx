import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { PageHeader } from "@/components/app/primitives";
import { MockBadge } from "@/components/app/mock-badge";
import { getHotspots } from "@/services/api";
import { DISTRICTS, CRIME_HEADS, GRAVITY } from "@/mocks/firs";
import { KARNATAKA_PATH } from "@/mocks/karnataka-map";

import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_app/map")({
  head: () => ({ meta: [{ title: "Crime Map — Crime Intelligence Assistant" }] }),
  component: MapPage,
});

function intensityColor(v: number) {
  // 0..100 → warm gradient
  if (v > 75) return "rgba(192,80,77,0.85)";
  if (v > 55) return "rgba(212,144,80,0.8)";
  if (v > 35) return "rgba(212,192,80,0.75)";
  return "rgba(80,144,192,0.65)";
}

function MapPage() {
  const { data, isLoading } = useQuery({ queryKey: ["hotspots"], queryFn: getHotspots });
  const [selected, setSelected] = useState<string | null>(null);

  const sel = data?.find((h) => h.district === selected);

  return (
    <div className="flex flex-col h-full">
      <div className="px-6 pt-6">
        <PageHeader
          title="Crime Hotspot Map"
          subtitle="Heat clusters over Karnataka districts. Click a cluster for details."
          actions={<MockBadge />}
        />
      </div>

      <div className="flex flex-1 gap-4 px-6 pb-6 min-h-0">
        {/* Filters */}
        <aside className="w-64 shrink-0 rounded-xl glass p-4 space-y-4 self-start">
          <div className="text-[11px] uppercase tracking-wider text-muted-foreground font-medium">
            Filters
          </div>
          <div className="space-y-2">
            <Label>Crime type</Label>
            <Select defaultValue="All">
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="All">All types</SelectItem>
                {CRIME_HEADS.map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Date range</Label>
            <Select defaultValue="30">
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="7">Last 7 days</SelectItem>
                <SelectItem value="30">Last 30 days</SelectItem>
                <SelectItem value="90">Last 90 days</SelectItem>
                <SelectItem value="365">Last 1 year</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>District</Label>
            <Select defaultValue="All">
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="All">All districts</SelectItem>
                {DISTRICTS.map((d) => <SelectItem key={d} value={d}>{d}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Gravity</Label>
            <Select defaultValue="All">
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="All">All</SelectItem>
                {GRAVITY.map((g) => <SelectItem key={g} value={g}>{g}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>

          <div className="border-t border-border pt-3">
            <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium mb-2">
              Intensity
            </div>
            <div className="flex items-center gap-2 text-[11px]">
              <div className="flex-1 h-2 rounded-full bg-gradient-to-r from-[rgba(80,144,192,0.6)] via-[rgba(212,192,80,0.75)] to-[rgba(192,80,77,0.85)]" />
            </div>
            <div className="flex justify-between text-[10px] text-muted-foreground mt-1">
              <span>Low</span><span>High</span>
            </div>
          </div>
        </aside>

        {/* Map canvas */}
        <div className="flex-1 relative rounded-xl glass overflow-hidden min-h-[500px]">
          {isLoading || !data ? (
            <Skeleton className="absolute inset-4" />
          ) : (
            <svg viewBox="0 0 100 120" className="w-full h-full" preserveAspectRatio="xMidYMid meet">
              {/* Karnataka state outline (simplified from GADM boundary) */}
              <path
                d={KARNATAKA_PATH}
                fill="var(--color-muted)"
                stroke="var(--color-primary)"
                strokeWidth="0.35"
                strokeLinejoin="round"
              />

              {/* Hotspot circles */}
              {data.map((h) => (
                <g key={h.district} className="cursor-pointer" onClick={() => setSelected(h.district)}>
                  <circle
                    cx={h.x}
                    cy={h.y}
                    r={2 + (h.intensity / 100) * 5}
                    fill={intensityColor(h.intensity)}
                    stroke={selected === h.district ? "var(--color-primary)" : "transparent"}
                    strokeWidth="0.4"
                    className="transition-all hover:opacity-80"
                  />
                  <text
                    x={h.x}
                    y={h.y + 8}
                    fontSize="2"
                    textAnchor="middle"
                    fill="var(--color-foreground)"
                    className="pointer-events-none select-none"
                  >
                    {h.district}
                  </text>
                </g>
              ))}
            </svg>
          )}

          {sel && (
            <div className="absolute top-4 right-4 w-64 rounded-xl glass shadow-lg p-3 animate-in fade-in duration-200">
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">
                {sel.district}
              </div>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="text-2xl font-semibold tabular-nums">{sel.cases}</span>
                <span className="text-xs text-muted-foreground">cases (30d)</span>
              </div>
              <div className="text-xs mt-1">
                Dominant: <span className="font-medium">{sel.dominant}</span>
              </div>
              <div className={cn("text-xs mt-0.5 font-medium", sel.trend >= 0 ? "text-destructive" : "text-success")}>
                {sel.trend >= 0 ? "▲" : "▼"} {Math.abs(sel.trend)}% vs prior period
              </div>
              <button
                onClick={() => setSelected(null)}
                className="mt-2 text-[11px] text-muted-foreground hover:text-foreground"
              >
                Close
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
