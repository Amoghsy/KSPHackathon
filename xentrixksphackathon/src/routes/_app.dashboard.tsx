import { createFileRoute } from "@tanstack/react-router";
import { DynamicDashboard } from "@/components/app/DynamicDashboard";

export const Route = createFileRoute("/_app/dashboard")({
  head: () => ({ meta: [{ title: "Dashboard — Crime Intelligence Assistant" }] }),
  component: () => <DynamicDashboard />,
});
