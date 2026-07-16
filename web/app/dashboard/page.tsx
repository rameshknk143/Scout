import { Suspense } from "react";
import { api } from "@/lib/api";
import TrendRadarClient from "./trend-radar-client";

// This is personal, password-gated, live data -- never statically
// prerendered. Without this, `next build` tries to prerender the page by
// calling the live Render API at build time, which is both a pointless
// stale snapshot to bake in and a real failure mode if that endpoint isn't
// up yet during the build (see the /alerts build failure this fixed).
export const dynamic = "force-dynamic";

import Link from "next/link";

// Header renders immediately; the digest, watchlist, and alert fetches (Render cold-start prone)
// stream in behind it instead of blocking the whole page.
async function TrendRadarData() {
  const [digest, watchlistData, alertsData] = await Promise.all([
    api.digest(),
    api.watchlist().catch(() => ({ validations: [] })),
    api.alerts().catch(() => ({ alerts: [] })),
  ]);
  return (
    <TrendRadarClient
      digest={digest}
      watchlist={watchlistData.validations}
      alerts={alertsData.alerts}
    />
  );
}

export default function TrendRadarPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-4 border-b border-white/5">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Good evening, Ram</h1>
          <p className="text-xs text-zinc-400 font-medium mt-1">
            Your Amazon India reseller business at a glance.
          </p>
        </div>
        <div className="mt-3 sm:mt-0">
          <Link
            href="/validator"
            className="btn-primary w-auto text-xs py-2 px-4 shadow-sm flex items-center gap-1.5"
          >
            <span>+</span> Validate New ASIN
          </Link>
        </div>
      </div>
      <Suspense fallback={<div className="text-zinc-400 text-xs font-semibold py-8 text-center bg-[#111625] rounded-xl border border-white/5 shadow-sm">Loading business dashboard intelligence...</div>}>
        <TrendRadarData />
      </Suspense>
    </div>
  );
}
