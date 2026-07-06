import { api } from "@/lib/api";
import TrendRadarClient from "./trend-radar-client";

export default async function TrendRadarPage() {
  const digest = await api.digest();

  return (
    <div>
      <h1 className="text-2xl font-bold tracking-tight mb-1">Trend Radar</h1>
      <p className="text-muted text-sm mb-6">
        Broad discovery across 11 categories — new entrants, climbers,
        cross-category hits.
      </p>
      <TrendRadarClient digest={digest} />
    </div>
  );
}
