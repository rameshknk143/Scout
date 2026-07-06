import { api } from "@/lib/api";
import WatchlistClient from "./watchlist-client";

export default async function WatchlistPage() {
  const { validations } = await api.watchlist();

  return (
    <div>
      <h1 className="text-2xl font-bold tracking-tight mb-1">Watchlist</h1>
      <p className="text-muted text-sm mb-6">Every Validator run, logged.</p>
      <WatchlistClient validations={validations} />
    </div>
  );
}
