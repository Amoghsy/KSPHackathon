import { QueryClient } from "@tanstack/react-query";
import { createRouter } from "@tanstack/react-router";
import { routeTree } from "./routeTree.gen";

// ─── Global QueryClient ──────────────────────────────────────────────────────
// Configured with:
//  - 3 auto-retries (exponential back-off, capped at 30s)
//  - 5 min stale time so data is re-used across navigations
//  - 10 min garbage-collection window
//  - No aggressive window-focus refetching for a police console (avoid noise)

export function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 5 * 60 * 1000, // 5 min
        gcTime: 10 * 60 * 1000, // 10 min
        retry: (failureCount, error: unknown) => {
          // Don't retry on 401 / 403 / 404
          const status = (error as { response?: { status?: number } })?.response?.status;
          if (status && [401, 403, 404].includes(status)) return false;
          return failureCount < 2;
        },
        retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 30_000),
        refetchOnWindowFocus: false,
        refetchOnReconnect: true,
      },
      mutations: {
        retry: 0,
      },
    },
  });
}

export const getRouter = () => {
  const queryClient = makeQueryClient();

  const router = createRouter({
    routeTree,
    context: { queryClient },
    scrollRestoration: true,
    defaultPreloadStaleTime: 0,
  });

  return router;
};
