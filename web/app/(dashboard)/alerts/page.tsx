import { Suspense } from "react";
import { api } from "@/lib/api";
import AlertsClient from "./alerts-client";

// This build broke once already: `next build` tried to statically
// prerender this page by calling the live Render API, and lost the race
// against Render's own redeploy of the new /alerts endpoint. See
// (dashboard)/page.tsx for the fuller explanation -- same fix everywhere.
export const dynamic = "force-dynamic";

async function AlertsData() {
  const { alerts } = await api.alerts();
  return <AlertsClient alerts={alerts} />;
}

export default function AlertsPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold tracking-tight mb-1">Alerts</h1>
      <p className="text-muted text-sm mb-6">
        Price, rank, and review-count changes on every ASIN you&apos;ve run through the Validator.
      </p>
      <Suspense fallback={<div className="text-muted text-sm">Loading alerts…</div>}>
        <AlertsData />
      </Suspense>
    </div>
  );
}
