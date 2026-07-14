import { Shield, AlertTriangle } from "lucide-react";

export function Legend() {
  return (
    <div className="absolute bottom-4 right-4 z-[500] bg-card/90 backdrop-blur border border-border p-3.5 rounded-xl shadow-lg text-foreground max-w-xs space-y-2.5 animate-in fade-in duration-200">
      <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest border-b border-border pb-1">
        GIS Legend
      </div>

      <div className="space-y-2 text-xs">
        {/* Heatmap Density */}
        <div className="space-y-1">
          <div className="font-semibold text-muted-foreground text-[10px]">HEATMAP DENSITY</div>
          <div className="h-2 w-full rounded-sm bg-gradient-to-r from-yellow-500/20 via-orange-500/60 to-red-500" />
          <div className="flex justify-between text-[9px] text-muted-foreground">
            <span>Low</span>
            <span>Critical</span>
          </div>
        </div>

        {/* Crime Severity Scale */}
        <div className="space-y-1">
          <div className="font-semibold text-muted-foreground text-[10px]">CRIME SEVERITY BUBBLES</div>
          <div className="grid grid-cols-2 gap-1.5 text-[10px] font-medium">
            <div className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-emerald-500 block"></span>
              <span>Low</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-amber-500 block"></span>
              <span>Medium</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-orange-500 block"></span>
              <span>High</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-red-500 block"></span>
              <span>Critical</span>
            </div>
          </div>
        </div>

        {/* Entities */}
        <div className="space-y-1 border-t border-border pt-1.5">
          <div className="flex items-center gap-2">
            <div className="flex items-center justify-center w-5 h-5 rounded-full bg-blue-500/20 border border-blue-500">
              <Shield className="h-2.5 w-2.5 text-blue-400" />
            </div>
            <span className="text-[10px] font-medium text-foreground/80">Police Station</span>
          </div>
          
          <div className="flex items-center gap-2">
            <div className="flex items-center justify-center w-5 h-5 rounded-full bg-red-500/10 border border-red-500/40">
              <AlertTriangle className="h-2.5 w-2.5 text-red-500" />
            </div>
            <span className="text-[10px] font-medium text-foreground/80">DBSCAN Hotspot</span>
          </div>

          <div className="flex items-center gap-2">
            <div className="h-3 w-5 border border-dashed border-slate-500 rounded bg-slate-500/5" />
            <span className="text-[10px] font-medium text-foreground/80">District Boundary</span>
          </div>
        </div>
      </div>
    </div>
  );
}
export default Legend;
