import { Suspense } from "react";
import { api } from "@/lib/api";
import WatchlistClient from "./watchlist-client";

// Header renders immediately; the watchlist fetch streams in behind it
// instead of blocking the whole page.
async function WatchlistData() {
  const { validations } = await api.watchlist();
  return <WatchlistClient validations={validations} />;
}

export default function WatchlistPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold tracking-tight mb-1">Watchlist</h1>
      <p className="text-muted text-sm mb-6">Every Validator run, logged.</p>
      <Suspense fallback={<div className="text-muted text-sm">Loading watchlist…</div>}>
        <WatchlistData />
      </Suspense>
    </div>
  );
}
