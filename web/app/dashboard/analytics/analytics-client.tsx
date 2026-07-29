"use client";

import { useMemo, useState, useEffect } from "react";
import { Table, type Column } from "@/components/ui";
import VerdictBadge from "@/components/VerdictBadge";
import type { Validation } from "@/lib/api";
import { getPpcAnalytics } from "@/lib/actions";

interface CampaignItem {
  id: string;
  name: string;
  type: string;
  spend: number;
  sales: number;
  acos: number;
  roas: number;
  status: string;
  wastage_risk: string;
}

export default function AnalyticsClient({
  validations,
}: {
  validations: Validation[];
}) {
  const [activeTab, setActiveTab] = useState<"overview" | "ppc">("overview");
  const [loading, setLoading] = useState(true);
  const [ppcError, setPpcError] = useState<string | null>(null);
  const [ppcData, setPpcData] = useState<any>(null);

  useEffect(() => {
    async function loadPpc() {
      try {
        setLoading(true);
        setPpcError(null);
        const res = await getPpcAnalytics();
        setPpcData(res ?? null);
      } catch (err) {
        console.error("Failed to load PPC analytics:", err);
        setPpcError(
          err instanceof Error ? err.message : "Could not reach the analytics service."
        );
      } finally {
        setLoading(false);
      }
    }
    loadPpc();
  }, []);

  // Ad metrics are only real once the Amazon Advertising API is authorized. Until
  // then the backend sends nulls and we render them as "—" rather than as zeroes,
  // which would read as "you spent nothing" instead of "we don't know".
  const adMetricsAvailable = Boolean(ppcData?.ad_metrics_available);
  const money = (v: number | null | undefined) =>
    typeof v === "number" ? `₹${v.toLocaleString("en-IN")}` : "—";
  const pct = (v: number | null | undefined) =>
    typeof v === "number" ? `${v}%` : "—";

  const stats = useMemo(() => {
    const total = validations.length;
    const uniqueAsins = new Set(validations.map((v) => v.asin)).size;
    const avgScore = total
      ? validations.reduce((sum, v) => sum + v.score, 0) / total
      : 0;

    const verdictCounts: Record<string, number> = {};
    for (const v of validations) {
      verdictCounts[v.verdict] = (verdictCounts[v.verdict] ?? 0) + 1;
    }

    return { total, uniqueAsins, avgScore, verdictCounts };
  }, [validations]);

  const campaignColumns: Column<CampaignItem>[] = [
    {
      key: "name",
      header: "Campaign Name",
      render: (c) => (
        <div>
          <span className="font-bold text-zinc-900 text-xs block">{c.name}</span>
          <span className="text-[10px] text-zinc-400 font-mono">{c.type}</span>
        </div>
      ),
    },
    {
      key: "spend",
      header: "Ad Spend",
      render: (c) => <span className="font-mono font-bold text-zinc-900">₹{c.spend.toLocaleString("en-IN")}</span>,
    },
    {
      key: "sales",
      header: "Ad Sales",
      render: (c) => <span className="font-mono font-bold text-emerald-700">₹{c.sales.toLocaleString("en-IN")}</span>,
    },
    {
      key: "acos",
      header: "ACoS %",
      render: (c) => (
        <span className={`font-mono font-bold px-2 py-0.5 rounded text-xs ${
          c.acos <= 20 ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-amber-50 text-amber-800 border border-amber-200"
        }`}>
          {c.acos}%
        </span>
      ),
    },
    {
      key: "roas",
      header: "ROAS",
      render: (c) => <span className="font-mono font-bold text-zinc-800">{c.roas}x</span>,
    },
    {
      key: "wastage_risk",
      header: "Wastage Risk",
      render: (c) => (
        <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
          c.wastage_risk === "High" ? "bg-red-50 text-red-600 border border-red-200" : "bg-zinc-100 text-zinc-600"
        }`}>
          {c.wastage_risk}
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header Controls */}
      <div className="flex items-center justify-between border-b border-black/5 pb-3">
        <div>
          <div className="text-[10px] font-bold tracking-widest text-emerald-600 uppercase">
            Stage 06 · Depth & Scale Analytics
          </div>
          <h2 className="text-xl font-bold text-zinc-900">Storefront Intelligence & PPC Performance</h2>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center gap-1 bg-zinc-100 p-1 rounded-xl">
          <button
            onClick={() => setActiveTab("ppc")}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeTab === "ppc" ? "bg-white text-zinc-900 shadow-sm" : "text-zinc-500 hover:text-zinc-900"
            }`}
          >
            🎯 PPC & Ads Intelligence
          </button>
          <button
            onClick={() => setActiveTab("overview")}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeTab === "overview" ? "bg-white text-zinc-900 shadow-sm" : "text-zinc-500 hover:text-zinc-900"
            }`}
          >
            📊 Product Sourcing Overview
          </button>
        </div>
      </div>

      {activeTab === "ppc" ? (
        <div className="space-y-6">
          {/* Status Notice Banner */}
          {loading ? (
            <div className="p-4 rounded-2xl bg-zinc-50 border border-zinc-200 text-xs font-medium text-zinc-500">
              Loading advertising status…
            </div>
          ) : ppcError ? (
            <div className="p-4 rounded-2xl bg-red-50 border border-red-200 flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <span className="text-xl">⚠️</span>
                <div>
                  <h4 className="text-xs font-bold text-red-900 uppercase tracking-wider">
                    Could not load advertising analytics
                  </h4>
                  <p className="text-xs text-red-800 mt-0.5 font-medium">{ppcError}</p>
                </div>
              </div>
              <button
                onClick={() => window.location.reload()}
                className="px-3.5 py-1.5 bg-red-900 text-white rounded-xl text-xs font-bold hover:bg-black transition shadow-sm shrink-0"
              >
                Retry
              </button>
            </div>
          ) : (
            <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <span className="text-xl">🔑</span>
                <div>
                  <h4 className="text-xs font-bold text-amber-900 uppercase tracking-wider">
                    Amazon Advertising API Authorization Status
                  </h4>
                  <p className="text-xs text-amber-800 mt-0.5 font-medium">
                    {ppcData?.status_message ?? "Advertising API not connected."}
                  </p>
                </div>
              </div>
              <a
                href="/dashboard/settings"
                className="px-3.5 py-1.5 bg-amber-900 text-white rounded-xl text-xs font-bold hover:bg-black transition shadow-sm shrink-0"
              >
                ⚙️ Manage API Credentials
              </a>
            </div>
          )}

          {/* PPC KPI Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-black/5 shadow-sm">
              <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider block">ACoS (Ad Cost of Sales)</span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-2xl font-extrabold text-zinc-900 font-mono">{pct(ppcData?.acos_pct)}</span>
                <span className="text-[11px] font-bold text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded">Target: 20%</span>
              </div>
              <span className="text-[11px] text-zinc-400 font-medium block mt-1">Ad Spend / Ad Sales</span>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-black/5 shadow-sm">
              <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider block">TACoS (Total Ad Cost of Sales)</span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-2xl font-extrabold text-emerald-700 font-mono">{pct(ppcData?.tacos_pct)}</span>
                <span className="text-[11px] font-bold text-zinc-500 bg-zinc-100 px-1.5 py-0.5 rounded">
                  {adMetricsAvailable ? "Live" : "Not connected"}
                </span>
              </div>
              <span className="text-[11px] text-zinc-400 font-medium block mt-1">Ad Spend / Total Storefront Revenue</span>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-black/5 shadow-sm">
              <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider block">Return on Ad Spend (ROAS)</span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-2xl font-extrabold text-zinc-900 font-mono">
                  {typeof ppcData?.roas === "number" ? `${ppcData.roas}x` : "—"}
                </span>
              </div>
              <span className="text-[11px] text-zinc-400 font-medium block mt-1">{money(ppcData?.total_ad_revenue)} Ad Revenue</span>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-black/5 shadow-sm">
              <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider block">Ad Spend</span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-2xl font-extrabold text-zinc-900 font-mono">{money(ppcData?.total_ad_spend)}</span>
              </div>
              <span className="text-[11px] text-zinc-400 font-medium block mt-1">Storefront Ad Spend</span>
            </div>
          </div>

          {!loading && !ppcError && !adMetricsAvailable && (
            <p className="text-[11px] text-zinc-500 bg-zinc-50 border border-zinc-200 rounded-xl px-4 py-3 leading-relaxed">
              <strong className="text-zinc-700">Why these read “—”:</strong> ad spend is only
              available from the Amazon Advertising API, which is a separate authorization
              from SP-API. Storefront sales data alone cannot tell ad-attributed revenue
              apart from organic revenue, so ACoS, TACoS and ROAS are shown as unknown
              rather than estimated.
            </p>
          )}

          {/* Real storefront figures from the nightly SP-API sync */}
          {!loading && !ppcError && ppcData?.order_count > 0 && (
            <div className="bg-white p-6 rounded-2xl border border-black/5 shadow-sm space-y-3">
              <h3 className="text-sm font-bold text-zinc-900">Storefront Sales (measured)</h3>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider block">Total Revenue</span>
                  <span className="text-xl font-extrabold text-emerald-700 font-mono">{money(ppcData.total_sales_amount)}</span>
                </div>
                <div>
                  <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider block">Units Sold</span>
                  <span className="text-xl font-extrabold text-zinc-900 font-mono">{ppcData.total_units?.toLocaleString("en-IN") ?? "—"}</span>
                </div>
                <div>
                  <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider block">Orders</span>
                  <span className="text-xl font-extrabold text-zinc-900 font-mono">{ppcData.order_count?.toLocaleString("en-IN") ?? "—"}</span>
                </div>
              </div>
            </div>
          )}

          {/* Campaign Table or Connection Required State */}
          <div className="bg-white p-6 rounded-2xl border border-black/5 shadow-sm space-y-4">
            <h3 className="text-sm font-bold text-zinc-900">Sponsored Products Campaign Audit</h3>
            {ppcData.campaigns && ppcData.campaigns.length > 0 ? (
              <Table rows={ppcData.campaigns as CampaignItem[]} columns={campaignColumns} rowKey={(c) => c.id} />
            ) : (
              <div className="p-8 text-center bg-zinc-50 rounded-xl border border-dashed border-zinc-200 space-y-2">
                <span className="text-3xl block">📡</span>
                <h4 className="text-sm font-bold text-zinc-900">No Live Ad Campaigns Linked</h4>
                <p className="text-xs text-zinc-500 max-w-md mx-auto">
                  Amazon Advertising API self-serve authorization (Case #21243620901) is pending Amazon Dev Support approval. Connect your Sponsored Products OAuth credentials in Settings to sync live campaign metrics.
                </p>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-black/5 shadow-sm">
              <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider block">Total Validations</span>
              <span className="text-2xl font-extrabold text-zinc-900 font-mono mt-1 block">{stats.total}</span>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-black/5 shadow-sm">
              <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider block">Unique Products</span>
              <span className="text-2xl font-extrabold text-zinc-900 font-mono mt-1 block">{stats.uniqueAsins}</span>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-black/5 shadow-sm">
              <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider block">Average Score</span>
              <span className="text-2xl font-extrabold text-zinc-900 font-mono mt-1 block">{stats.avgScore.toFixed(1)}</span>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-black/5 shadow-sm">
              <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider block">Pursue Ratio</span>
              <span className="text-2xl font-extrabold text-emerald-700 font-mono mt-1 block">
                {stats.total ? Math.round(((stats.verdictCounts["PURSUE"] || 0) / stats.total) * 100) : 0}%
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
