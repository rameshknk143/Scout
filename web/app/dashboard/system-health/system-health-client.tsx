"use client";

// System Health -- the dashboard that shows the scraping platform behind
// the product data. Every panel is a frosted glass card with depth; the
// whole page sits on a perspective grid. The phone-tunnel card and the
// scrape-yield card have their own 3D flourishes: a 3D conic ring for
// tunnel uptime, and a 3D bar chart for scrape history.

import { useState } from "react";
import type { OpsStatus, Pipelines, TunnelHistory } from "@/lib/api";
import PerspectiveGrid from "@/components/3d/PerspectiveGrid";
import GlassPanel from "@/components/3d/GlassPanel";
import TunnelRing from "@/components/3d/TunnelRing";
import Bar3D from "@/components/3d/Bar3D";

type Props = {
  status: OpsStatus | null;
  pipelines: Pipelines | null;
  tunnelHistory: TunnelHistory | null;
};

const DOT_GREEN = "bg-emerald-500";
const DOT_RED = "bg-red-500";
const DOT_AMBER = "bg-amber-500";
const DOT_GRAY = "bg-zinc-300";

function dotFor(status: string | undefined): string {
  if (status === "ok") return DOT_GREEN;
  if (status === "error") return DOT_RED;
  if (status === "warn") return DOT_AMBER;
  return DOT_GRAY;
}

function Stat({
  label,
  value,
  dot,
}: {
  label: React.ReactNode;
  value: React.ReactNode;
  dot?: string;
}) {
  return (
    <div className="flex items-center justify-between py-1">
      <span className="flex items-center gap-2 text-sm text-zinc-600">
        {dot && <span className={`w-2 h-2 rounded-full inline-block ${dot}`} aria-hidden />}
        {label}
      </span>
      <span className="text-sm font-semibold text-zinc-900 text-right font-mono">{value}</span>
    </div>
  );
}

function ComponentLabel({ name }: { name: string }) {
  const labels: Record<string, string> = {
    "vm-health": "VM Watchdog",
    "vm-scrape": "Scraper (2×/day)",
    "vm-push": "Data Pusher (hourly)",
    "vm-keepwarm": "API Keep-Warm",
    "vm-maintain": "Nightly Maintenance",
    deadman: "Dead-Man's Switch",
  };
  return <>{labels[name] ?? name}</>;
}

export default function SystemHealthClient({
  status,
  pipelines,
  tunnelHistory,
}: Props) {
  const [showAllEvents, setShowAllEvents] = useState(false);

  if (!status) {
    return (
      <GlassPanel depth="high" className="border-red-200">
        <p className="text-sm text-red-600">
          Could not load system status. The Render API may be waking up —
          refresh in a minute.
        </p>
      </GlassPanel>
    );
  }

  const beats = status.heartbeats ?? [];
  const events = status.recent_events ?? [];

  const vmHealth = beats.find((b) => b.component === "vm-health");
  const hd = (vmHealth?.detail as Record<string, any> | null)?.detail ?? {};
  const tunnelListener = hd.tunnel_listener;
  const tunnelFlow = hd.tunnel_flow;
  const tunnelExitIp = hd.tunnel_exit_ip;
  const tunnelSamples = hd.tunnel_uptime_samples;

  const scrape = beats.find((b) => b.component === "vm-scrape");
  const scrapeStatus = scrape?.status;
  const scrapeHd = (scrape?.detail as Record<string, any> | null)?.detail ?? {};

  const diskPct = hd.disk_pct;
  const memAvail = hd.mem_available_mb;
  const dataAgeH = hd.data_age_hours;
  const timersActive = hd.timers_active;

  const scrapePipe = pipelines?.vm_watchlist;
  const collectorPipe = pipelines?.nightly_collector;
  const maxunPipe = pipelines?.laptop_maxun;

  // Convert "12/12" -> 1.0
  let samplePct = 0;
  if (typeof tunnelSamples === "string") {
    const m = tunnelSamples.match(/^(\d+)\/(\d+)$/);
    if (m) samplePct = Number(m[1]) / Number(m[2]);
  }
  const tunnelTone =
    tunnelFlow === "ok" ? "ok" : tunnelFlow === "dead" || tunnelListener === "down" ? "error" : "warn";
  const tunnelCaption = samplePct >= 0.99 ? "last hour" : "last hour (flapping)";

  // 7-day chart data: pick one bucket per day, 7 most recent. The API returns
  // hourly; aggregate up to daily for the chart by averaging same-day buckets.
  const hist = (tunnelHistory?.history ?? []).slice();
  const dailyMap = new Map<string, { sum: number; n: number; samples: number }>();
  for (const b of hist) {
    const day = b.hour.slice(0, 10);
    const entry = dailyMap.get(day) ?? { sum: 0, n: 0, samples: 0 };
    entry.sum += b.up_pct;
    entry.n += 1;
    entry.samples += b.samples;
    dailyMap.set(day, entry);
  }
  const daily = Array.from(dailyMap.entries())
    .map(([day, e]) => ({
      day,
      pct: e.n ? e.sum / e.n : 0,
      samples: e.samples,
    }))
    .sort((a, b) => a.day.localeCompare(b.day))
    .slice(-7);
  const chartData = daily.map((d) => ({
    label: d.day.slice(5), // MM-DD
    value: Math.round(d.pct),
  }));
  // Overall tunnel health as one number
  const overallTunnelPct =
    daily.length > 0
      ? daily.reduce((a, b) => a + b.pct, 0) / daily.length
      : samplePct * 100;

  const eventsToShow = showAllEvents ? events : events.slice(0, 6);

  return (
    <div className="relative">
      {/* Animated perspective grid behind the page (same one used on the
          public landing) -- the dashboard now sits in the same 3D world. */}
      <PerspectiveGrid />

      <div className="relative" style={{ perspective: "1600px" }}>
        <div
          className="grid grid-cols-1 md:grid-cols-3 gap-4"
          style={{ transformStyle: "preserve-3d" }}
        >
          {/* --- Phone Tunnel card --- */}
          <GlassPanel
            title="Phone Tunnel"
            subtitle="Residential IP — Amazon stops blocking"
            depth="high"
            className="hover:translate-z-2"
          >
            <div className="flex items-center gap-4">
              <TunnelRing
                fill={overallTunnelPct / 100}
                center={`${Math.round(overallTunnelPct)}%`}
                caption="7-day uptime"
                tone={tunnelTone as "ok" | "warn" | "error"}
                size={124}
              />
              <div className="flex-1 min-w-0">
                <div className="text-[10px] uppercase tracking-wider text-zinc-400">
                  State
                </div>
                <div
                  className="text-base font-bold"
                  style={{
                    color:
                      tunnelTone === "ok"
                        ? "#059669"
                        : tunnelTone === "error"
                          ? "#dc2626"
                          : "#d97706",
                  }}
                >
                  {tunnelFlow === "ok"
                    ? "UP — flowing"
                    : tunnelFlow === "dead"
                      ? "WEDGED"
                      : tunnelListener === "down"
                        ? "DOWN"
                        : "—"}
                </div>
                <div className="text-[11px] text-zinc-500 mt-1.5 font-mono truncate">
                  IP: {tunnelExitIp ?? "—"}
                </div>
                <div className="text-[11px] text-zinc-500 font-mono">
                  {tunnelSamples ?? "—"} samples
                </div>
              </div>
            </div>
            <p className="text-[11px] text-zinc-400 mt-3 leading-relaxed">
              Your phone lends its mobile IP. If this shows WEDGED or DOWN,
              check the phone: Termux + Every Proxy (or v2 supervisor) running,
              battery unrestricted.
            </p>
          </GlassPanel>

          {/* --- Last Scrape card --- */}
          <GlassPanel
            title="Last Scrape"
            subtitle="Watchlist — 12 ASINs, 2×/day"
            depth="high"
          >
            <div className="flex items-baseline justify-between">
              <div>
                <div
                  className="text-4xl font-bold font-mono tracking-tight"
                  style={{
                    color:
                      (scrapePipe?.last_pass_asins ?? 0) >=
                      (scrapePipe?.targets ?? 12) / 2
                        ? "#059669"
                        : "#dc2626",
                  }}
                >
                  {scrapePipe?.last_pass_asins ?? "—"}
                  <span className="text-zinc-400 text-2xl">
                    /{scrapePipe?.targets ?? 12}
                  </span>
                </div>
                <div className="text-[11px] text-zinc-500 mt-1">
                  ASINs landed
                </div>
              </div>
              <div className="text-right">
                <Stat
                  label="Scraper"
                  value={scrapeStatus ?? "—"}
                  dot={dotFor(scrapeStatus)}
                />
                <Stat
                  label="Last run"
                  value={scrape ? `${scrape.age_minutes}m` : "—"}
                />
              </div>
            </div>
            <p className="text-[11px] text-zinc-400 mt-3 leading-relaxed">
              Runs at 11:50 &amp; 20:50 IST. 6+ of 12 is healthy; below that
              the VM&apos;s datacenter IP is being blocked — the phone tunnel is
              the fix.
            </p>
          </GlassPanel>

          {/* --- VM health card --- */}
          <GlassPanel
            title="Scraping VM"
            subtitle="Oracle free tier (956 MB)"
            depth="high"
          >
            <Stat
              label="Watchdog"
              value={vmHealth?.status === "ok" ? "all clear" : (hd.message as string) ?? "—"}
              dot={dotFor(vmHealth?.status)}
            />
            <Stat label="Disk" value={`${diskPct ?? "—"}%`} />
            <Stat label="Mem free" value={`${memAvail ?? "—"} MB`} />
            <Stat label="Timers" value={`${timersActive ?? "—"} / 5`} />
            <Stat label="Newest data" value={dataAgeH != null ? `${dataAgeH}h` : "—"} />
          </GlassPanel>
        </div>

        {/* --- 3D bar chart: 7-day tunnel uptime per day --- */}
        {chartData.length > 0 && (
          <div className="mt-4">
            <GlassPanel
              title="Tunnel Uptime — last 7 days"
              subtitle="Bars = % of 5-min samples in `up` state, per day"
              depth="middle"
            >
              <Bar3D
                data={chartData}
                title=""
                yLabel="% UP"
                max={100}
                tone={
                  overallTunnelPct > 90
                    ? "ok"
                    : overallTunnelPct > 70
                      ? "warn"
                      : "error"
                }
                unit="%"
              />
            </GlassPanel>
          </div>
        )}

        {/* --- Pipelines table --- */}
        <div className="mt-4">
          <GlassPanel
            title="Data Pipelines"
            subtitle="All sources feeding the product database"
            depth="middle"
          >
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-zinc-400 text-xs uppercase tracking-wide border-b border-black/5">
                    <th className="py-2 pr-4 font-semibold">Pipeline</th>
                    <th className="py-2 pr-4 font-semibold">Rows</th>
                    <th className="py-2 pr-4 font-semibold">Last</th>
                    <th className="py-2 font-semibold">Health</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { key: "vm_watchlist", name: "VM watchlist (12 ASINs, 2×/day)", pipe: scrapePipe },
                    { key: "nightly_collector", name: "Category collector (nightly)", pipe: collectorPipe },
                    { key: "laptop_maxun", name: "Maxun robots (laptop, manual)", pipe: maxunPipe },
                  ].map(({ key, name, pipe }) => (
                    <tr key={key} className="border-b border-black/5 last:border-0">
                      <td className="py-2.5 pr-4 text-zinc-700">{name}</td>
                      <td className="py-2.5 pr-4 font-mono font-semibold">
                        {pipe?.rows?.toLocaleString() ?? "—"}
                      </td>
                      <td className="py-2.5 pr-4 text-zinc-500 font-mono">
                        {pipe ? `${pipe.age_hours.toFixed(1)}h` : "—"}
                      </td>
                      <td className="py-2.5">
                        <span className="flex items-center gap-2">
                          <span
                            className={`w-2 h-2 rounded-full inline-block ${
                              !pipe
                                ? DOT_GRAY
                                : key === "vm_watchlist"
                                  ? (pipe.last_pass_asins ?? 0) >= (pipe.targets ?? 12) / 2
                                    ? DOT_GREEN
                                    : DOT_RED
                                  : pipe.age_hours < 48
                                    ? DOT_GREEN
                                    : DOT_AMBER
                            }`}
                            aria-hidden
                          />
                          <span className="text-zinc-500 text-xs">
                            {key === "vm_watchlist" && pipe
                              ? `${pipe.last_pass_asins ?? "?"}/${pipe.targets ?? 12}`
                              : key === "nightly_collector"
                                ? pipe && pipe.age_hours < 48
                                  ? "fresh"
                                  : "stale"
                                : pipe
                                  ? pipe.age_hours < 168
                                    ? "recent"
                                    : "idle"
                                  : "no data"}
                          </span>
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </GlassPanel>
        </div>

        {/* --- Bottom row: components + events --- */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
          <GlassPanel title="Components" depth="middle">
            <div className="divide-y divide-black/5">
              {beats.map((b) => (
                <Stat
                  key={b.component}
                  label={<ComponentLabel name={b.component} />}
                  value={`${b.age_minutes}m`}
                  dot={dotFor(b.status)}
                />
              ))}
            </div>
            <p className="text-[11px] text-zinc-400 mt-3">
              Minutes since each component said &quot;alive&quot;.
            </p>
          </GlassPanel>

          <GlassPanel title="Recent Events (48h)" depth="middle">
            {events.length === 0 ? (
              <p className="text-sm text-zinc-500">
                Nothing to report — no warnings or errors in the last 48 hours.
              </p>
            ) : (
              <>
                <div className="divide-y divide-black/5">
                  {eventsToShow.map((e, i) => (
                    <div key={i} className="py-2">
                      <div className="flex items-center justify-between gap-2">
                        <span className="flex items-center gap-2 text-sm">
                          <span
                            className={`w-2 h-2 rounded-full inline-block ${
                              e.severity === "error"
                                ? DOT_RED
                                : e.severity === "warn"
                                  ? DOT_AMBER
                                  : "bg-sky-500"
                            }`}
                            aria-hidden
                          />
                          <span className="font-semibold text-zinc-800">{e.event}</span>
                        </span>
                        <span className="text-[11px] text-zinc-400 whitespace-nowrap font-mono">
                          {e.created_at_ist}
                        </span>
                      </div>
                      <p className="text-xs text-zinc-500 mt-1 leading-relaxed">
                        {e.message}
                      </p>
                    </div>
                  ))}
                </div>
                {events.length > 6 && (
                  <button
                    onClick={() => setShowAllEvents(!showAllEvents)}
                    className="mt-3 text-xs font-semibold text-amber-600 hover:text-amber-800"
                  >
                    {showAllEvents
                      ? "Show less"
                      : `Show all ${events.length} events`}
                  </button>
                )}
              </>
            )}
          </GlassPanel>
        </div>

        <p className="text-[11px] text-zinc-400 text-right mt-4 font-mono">
          Generated {status.generated_at_ist} · refreshes every minute
        </p>
      </div>
    </div>
  );
}
