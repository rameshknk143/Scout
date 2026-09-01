"use client";

import { useState } from "react";
import type { OpsStatus, Pipelines } from "@/lib/api";

// Everything on this page is designed to be read at a glance by Ram:
// green dot = fine, red dot = needs attention, plain-English labels,
// exact numbers (not adjectives), IST times everywhere.

type Props = {
  status: OpsStatus | null;
  pipelines: Pipelines | null;
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

function Card({
  title,
  children,
  className = "",
}: {
  title: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`bg-white rounded-xl border border-black/5 p-4 shadow-sm ${className}`}
    >
      <h2 className="text-xs font-bold uppercase tracking-wide text-zinc-400 mb-3">
        {title}
      </h2>
      {children}
    </div>
  );
}

function Row({
  label,
  value,
  dot,
}: {
  label: React.ReactNode;
  value: React.ReactNode;
  dot?: string;
}) {
  return (
    <div className="flex items-center justify-between py-1.5">
      <span className="flex items-center gap-2 text-sm text-zinc-600">
        {dot && (
          <span className={`w-2 h-2 rounded-full inline-block ${dot}`} aria-hidden />
        )}
        {label}
      </span>
      <span className="text-sm font-semibold text-zinc-900 text-right">
        {value}
      </span>
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

export default function SystemHealthClient({ status, pipelines }: Props) {
  const [showAllEvents, setShowAllEvents] = useState(false);

  if (!status) {
    return (
      <div className="bg-white rounded-xl border border-red-200 p-6 text-sm text-red-600">
        Could not load system status right now. The Render API may be waking up —
        refresh in a minute.
      </div>
    );
  }

  const beats = status.heartbeats ?? [];
  const events = status.recent_events ?? [];

  // Tunnel facts come from the vm-health heartbeat detail (added 2 Sep 2026).
  const vmHealth = beats.find((b) => b.component === "vm-health");
  const hd = (vmHealth?.detail as Record<string, any> | null)?.detail ?? {};
  const tunnelListener = hd.tunnel_listener;
  const tunnelFlow = hd.tunnel_flow;
  const tunnelExitIp = hd.tunnel_exit_ip;
  const tunnelSamples = hd.tunnel_uptime_samples;

  const scrape = beats.find((b) => b.component === "vm-scrape");
  const scrapeStatus = scrape?.status;
  const scrapeHd = (scrape?.detail as Record<string, any> | null)?.detail ?? {};

  const vm = beats.find((b) => b.component === "vm-health");
  const diskPct = hd.disk_pct;
  const memAvail = hd.mem_available_mb;
  const dataAgeH = hd.data_age_hours;
  const timersActive = hd.timers_active;

  const scrapePipe = pipelines?.vm_watchlist;
  const collectorPipe = pipelines?.nightly_collector;
  const maxunPipe = pipelines?.laptop_maxun;

  const eventsToShow = showAllEvents ? events : events.slice(0, 6);

  return (
    <div className="space-y-4">
      {/* Row 1: the three headline cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Phone Tunnel */}
        <Card title="Phone Tunnel (residential IP)">
          <Row
            label="State"
            value={
              tunnelFlow === "ok"
                ? "UP — flowing"
                : tunnelFlow === "dead"
                  ? "WEDGED — restart phone proxy"
                  : tunnelListener === "down"
                    ? "DOWN — phone offline"
                    : "unknown"
            }
            dot={
              tunnelFlow === "ok"
                ? DOT_GREEN
                : tunnelFlow === "dead" || tunnelListener === "down"
                  ? DOT_RED
                  : DOT_GRAY
            }
          />
          <Row label="Exit IP (your carrier)" value={tunnelExitIp ?? "—"} />
          <Row label="Last hour (5-min samples)" value={tunnelSamples ?? "—"} />
          <p className="text-[11px] text-zinc-400 mt-3 leading-relaxed">
            Your phone lends its mobile IP so Amazon stops blocking scrapes. If
            this shows DOWN, check the phone: Termux + Every Proxy running,
            battery unrestricted.
          </p>
        </Card>

        {/* Scrape Yield */}
        <Card title="Last Scrape (watchlist)">
          <Row
            label="Result"
            value={
              scrapePipe
                ? `${scrapePipe.last_pass_asins ?? "?"} of ${scrapePipe.targets ?? 12} ASINs`
                : "—"
            }
            dot={
              scrapePipe && (scrapePipe.last_pass_asins ?? 0) >= (scrapePipe.targets ?? 12) / 2
                ? DOT_GREEN
                : DOT_RED
            }
          />
          <Row
            label="Scraper state"
            value={scrapeStatus === "ok" ? "healthy" : scrapeStatus ?? "—"}
            dot={dotFor(scrapeStatus)}
          />
          <Row
            label="Last run"
            value={scrape ? `${scrape.age_minutes} min ago` : "—"}
          />
          <p className="text-[11px] text-zinc-400 mt-3 leading-relaxed">
            Runs twice daily (11:50 &amp; 20:50 IST). 6+ of 12 is healthy;
            below that Amazon is usually blocking the VM&apos;s datacenter IP —
            the phone tunnel is the fix.
          </p>
        </Card>

        {/* VM health */}
        <Card title="Scraping VM (Oracle)">
          <Row
            label="Watchdog"
            value={vm?.status === "ok" ? "all clear" : (hd.message as string) ?? "—"}
            dot={dotFor(vm?.status)}
          />
          <Row label="Disk used" value={`${diskPct ?? "—"}%`} />
          <Row label="Memory free" value={`${memAvail ?? "—"} MB`} />
          <Row label="Timers active" value={`${timersActive ?? "—"} of 5`} />
          <Row
            label="Newest local data"
            value={dataAgeH != null ? `${dataAgeH}h ago` : "—"}
          />
        </Card>
      </div>

      {/* Row 2: pipelines */}
      <Card title="Data Pipelines (all rows in the product database)">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-zinc-400 text-xs uppercase tracking-wide border-b border-black/5">
                <th className="py-2 pr-4 font-semibold">Pipeline</th>
                <th className="py-2 pr-4 font-semibold">Rows</th>
                <th className="py-2 pr-4 font-semibold">Last pass</th>
                <th className="py-2 font-semibold">Health</th>
              </tr>
            </thead>
            <tbody>
              {[
                {
                  key: "vm_watchlist",
                  name: "VM watchlist (12 ASINs, 2×/day)",
                  pipe: scrapePipe,
                },
                {
                  key: "nightly_collector",
                  name: "Category collector (nightly, GitHub)",
                  pipe: collectorPipe,
                },
                {
                  key: "laptop_maxun",
                  name: "Maxun robots (laptop, manual)",
                  pipe: maxunPipe,
                },
              ].map(({ key, name, pipe }) => (
                <tr key={key} className="border-b border-black/5 last:border-0">
                  <td className="py-2.5 pr-4 text-zinc-700">{name}</td>
                  <td className="py-2.5 pr-4 font-semibold">
                    {pipe?.rows?.toLocaleString() ?? "—"}
                  </td>
                  <td className="py-2.5 pr-4 text-zinc-500">
                    {pipe ? `${pipe.age_hours.toFixed(1)}h ago` : "—"}
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
                          ? `${pipe.last_pass_asins ?? "?"}/${pipe.targets ?? 12} ASINs`
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
      </Card>

      {/* Row 3: heartbeats + events */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card title="Components">
          <div className="divide-y divide-black/5">
            {beats.map((b) => (
              <Row
                key={b.component}
                label={<ComponentLabel name={b.component} />}
                value={`${b.age_minutes}m ago`}
                dot={dotFor(b.status)}
              />
            ))}
          </div>
          <p className="text-[11px] text-zinc-400 mt-3">
            Times are when each component last said &quot;alive&quot;.
          </p>
        </Card>

        <Card title="Recent Events (48h)">
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
                        <span className="font-semibold text-zinc-800">
                          {e.event}
                        </span>
                      </span>
                      <span className="text-[11px] text-zinc-400 whitespace-nowrap">
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
                  className="mt-3 text-xs font-semibold text-blue-600 hover:text-blue-800"
                >
                  {showAllEvents ? "Show less" : `Show all ${events.length} events`}
                </button>
              )}
            </>
          )}
        </Card>
      </div>

      <p className="text-[11px] text-zinc-400 text-right">
        Generated {status.generated_at_ist} · refreshes every minute
      </p>
    </div>
  );
}
