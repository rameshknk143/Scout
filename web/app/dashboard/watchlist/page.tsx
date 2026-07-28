import { Suspense } from "react";
import { api } from "@/lib/api";
import WatchlistClient from "./watchlist-client";

// See (dashboard)/page.tsx for why: never statically prerendered.
export const dynamic = "force-dynamic";

// Header renders immediately; the watchlist fetch streams in behind it
// instead of blocking the whole page.
async function WatchlistData() {
  const { validations } = await api.watchlist();
  return <WatchlistClient validations={validations} />;
}

export default function WatchlistPage() {
  return (
    <div>
      <h1 className="text-xl font-bold tracking-tight text-zinc-900 font-sans">Trend Explorer & Watchlist</h1>
      <p className="text-zinc-400 text-xs font-medium mt-1 mb-6">Every ASIN validation and product opportunity tracked.</p>
      <Suspense fallback={<div className="text-muted text-sm">Loading watchlist…</div>}>
        <WatchlistData />
      </Suspense>
    </div>
  );
}
