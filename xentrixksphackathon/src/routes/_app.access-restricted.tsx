import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { ArrowLeft, Send } from "lucide-react";
import { AccessDenied } from "@/routes/-access-denied";
import { Button } from "@/components/ui/button";

type AccessSearch = {
  module?: string;
  required?: string;
  from?: string;
};

export const Route = createFileRoute("/_app/access-restricted")({
  validateSearch: (search: Record<string, unknown>): AccessSearch => ({
    module: typeof search.module === "string" ? search.module : undefined,
    required: typeof search.required === "string" ? search.required : undefined,
    from: typeof search.from === "string" ? search.from : undefined,
  }),
  head: () => ({ meta: [{ title: "Access Restricted - Crime Intelligence Assistant" }] }),
  component: AccessRestrictedPage,
});

function AccessRestrictedPage() {
  const navigate = useNavigate();
  const search = Route.useSearch();

  return (
    <div className="flex min-h-full items-center justify-center p-6">
      <AccessDenied
        moduleName={search.module ?? "this module"}
        requiredRole={search.required}
        reason="This module is outside your assigned permissions. The rest of your workspace remains available from the navigation menu."
        actions={
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" onClick={() => navigate({ to: "/" })}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Return to workspace
            </Button>
            <Button variant="secondary" disabled title="Connects to access workflow when enabled">
              <Send className="mr-2 h-4 w-4" />
              Request access
            </Button>
          </div>
        }
      />
    </div>
  );
}
