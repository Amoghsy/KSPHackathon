import { Database } from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

export function MockBadge({ className }: { className?: string }) {
  return (
    <TooltipProvider delayDuration={200}>
      <Tooltip>
        <TooltipTrigger asChild>
          <span
            className={cn(
              "inline-flex items-center gap-1 rounded-full border border-dashed border-border bg-muted/60 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-muted-foreground cursor-help",
              className,
            )}
          >
            <Database className="h-3 w-3" />
            Preview data
          </span>
        </TooltipTrigger>
        <TooltipContent side="bottom" className="text-xs max-w-xs">
          This view is powered by mock data pending live database integration.
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
