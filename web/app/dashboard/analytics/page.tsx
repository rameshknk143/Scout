import { Suspense } from "react";
import { api } from "@/lib/api";
import AnalyticsClient from "./analytics-client";

// See (dashboard)/page.tsx for why: never statically prerendered.
export const dynamic = "force-dynamic";

async function AnalyticsData() {
  const { validations } = await api.watchlist();
  return <AnalyticsClient validations={validations} />;
}

export default function AnalyticsPage() {
  return (
    <div>
      <h1 className="text-xl font-bold tracking-tight text-zinc-900 mb-1 font-sans">Analytics</h1>
      <p className="text-zinc-400 text-xs font-medium mt-1 mb-6">
        Patterns across everything you&apos;ve run through the Opportunity
        Scorer so far.
      </p>
      <Suspense fallback={<div className="text-muted text-sm">Loading analytics…</div>}>
        <AnalyticsData />
      </Suspense>
    </div>
  );
}
