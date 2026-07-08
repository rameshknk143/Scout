import { Suspense } from "react";
import { api } from "@/lib/api";
import TrendRadarClient from "./trend-radar-client";

// This is personal, password-gated, live data -- never statically
// prerendered. Without this, `next build` tries to prerender the page by
// calling the live Render API at build time, which is both a pointless
// stale snapshot to bake in and a real failure mode if that endpoint isn't
// up yet during the build (see the /alerts build failure this fixed).
export const dynamic = "force-dynamic";

// Header renders immediately; the digest fetch (Render cold-start prone)
// streams in behind it instead of blocking the whole page.
async function TrendRadarData() {
  const digest = await api.digest();
  return <TrendRadarClient digest={digest} />;
}

export default function TrendRadarPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold tracking-tight mb-1">Trend Radar</h1>
      <p className="text-muted text-sm mb-6">
        Broad discovery across all 31 Amazon India categories — new entrants,
        climbers, cross-category hits.
      </p>
      <Suspense fallback={<div className="text-muted text-sm">Loading trend data…</div>}>
        <TrendRadarData />
      </Suspense>
    </div>
  );
}
