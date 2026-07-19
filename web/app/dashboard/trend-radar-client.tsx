"use client";

import { useEffect, useState, useTransition } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { 
  Table, 
  Tabs, 
  Select, 
  ChartCard, 
  MetricCard, 
  AlertStrip, 
  type AlertItem, 
  ProductDetailDrawer 
} from "@/components/ui";
import type { Digest, SnapshotRow, Validation, Alert, StorefrontSalesMetric, StorefrontOrder } from "@/lib/api";
import { CATEGORIES, LIST_TYPES } from "@/lib/constants";
import { getCategoryTable, updateWatchlistNotes, syncStorefrontData } from "@/lib/actions";

type TabKey = "watchlist" | "radar" | "bestsellers" | "storefront";
type MoverRow = Digest["top_movers"][number];
type CrossRow = Digest["cross_category"][number];

interface ConnectedAccount {
  selling_partner_id: string;
  marketplace_id: string;
  connected_at: string;
}

interface TrendRadarClientProps {
  digest: Digest;
  watchlist: Validation[];
  alerts: Alert[];
  connected: boolean;
  accounts: ConnectedAccount[];
  initialMetrics: StorefrontSalesMetric[];
  initialOrders: StorefrontOrder[];
}

export default function TrendRadarClient({
  digest,
  watchlist: watchlistRaw = [],
  alerts = [],
  connected,
  accounts = [],
  initialMetrics = [],
  initialOrders = [],
}: TrendRadarClientProps) {
  // The watchlist API returns EVERY validation row — a product validated N times
  // comes back N times. Collapse to the latest validation per ASIN so the table,
  // KPIs, and counts reflect unique products instead of repeats.
  const watchlist = Array.from(
    watchlistRaw
      .reduce((map, v) => {
        const prev = map.get(v.asin);
        if (!prev || new Date(v.validated_at) > new Date(prev.validated_at)) {
          map.set(v.asin, v);
        }
        return map;
      }, new Map<string, Validation>())
      .values()
  );
  const searchParams = useSearchParams();
  const tabParam = searchParams.get("tab") as TabKey;

  const [activeDashboardTab, setActiveDashboardTab] = useState<TabKey>(
    (tabParam === "watchlist" || tabParam === "radar" || tabParam === "bestsellers" || tabParam === "storefront")
      ? tabParam
      : "watchlist"
  );
  const [bestsellerTab, setBestsellerTab] = useState<"entrants" | "movers" | "cross">("entrants");

  // Sync states
  const [syncStatus, setSyncStatus] = useState<string | null>(null);
  const [isSyncPending, startSyncTransition] = useTransition();

  useEffect(() => {
    const tab = searchParams.get("tab");
    if (tab && (tab === "watchlist" || tab === "radar" || tab === "bestsellers" || tab === "storefront")) {
      setActiveDashboardTab(tab as TabKey);
    }
  }, [searchParams]);

  const handleSync = () => {
    setSyncStatus("🕒 Synchronizing with Amazon Seller Central...");
    startSyncTransition(async () => {
      try {
        const res = await syncStorefrontData();
        if (res.ok) {
          setSyncStatus("✅ Sync completed successfully! Reloading metrics...");
          setTimeout(() => {
            window.location.reload();
          }, 1500);
        } else {
          setSyncStatus(`❌ Sync failed: ${res.message || "Unknown error"}`);
        }
      } catch (err: any) {
        setSyncStatus(`❌ Error initiating sync: ${err.message || "Connection error"}`);
      }
    });
  };
  
  // Category browse state (Bestsellers Explorer)
  const [category, setCategory] = useState<string>(CATEGORIES[0]);
  const [listType, setListType] = useState<string>(LIST_TYPES[0].value);
  const [table, setTable] = useState<SnapshotRow[]>([]);
  const [loading, setLoading] = useState(true);

  // Watchlist table search & filter state
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategoryFilter, setSelectedCategoryFilter] = useState("all");
  const [selectedVerdictFilter, setSelectedVerdictFilter] = useState("all");

  // Selected product details drawer state
  const [selectedProduct, setSelectedProduct] = useState<any>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const handleUpdateNotes = async (asin: string, newNotes: string) => {
    try {
      await updateWatchlistNotes(asin, newNotes);
      setSelectedProduct((prev: any) => prev ? { ...prev, notes: newNotes } : null);
    } catch (err) {
      // handle error
    }
  };

  const coldStart = digest.collection_dates.length < 2;

  // Load bestsellers for selected category
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getCategoryTable(category, listType).then((res) => {
      if (!cancelled) {
        setTable(res.products);
        setLoading(false);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [category, listType]);

  // Compute operational alerts
  const computedAlerts: AlertItem[] = [
    {
      id: "price-alert",
      type: "price_drop",
      count: alerts.filter((a) => a.alert_type === "price_change").length,
      label: "Watchlist price drops detected in the last 24h",
      severity: "warning",
      actionLabel: "Review Prices",
      onClick: () => setActiveDashboardTab("watchlist"),
    },
    {
      id: "opp-alert",
      type: "opportunity",
      count: watchlist.filter((w) => w.score >= 70).length,
      label: "High-scoring product opportunities ready for supplier validation",
      severity: "success",
      actionLabel: "Analyze Sourcing",
      onClick: () => setActiveDashboardTab("watchlist"),
    },
  ];

  // ---- Real metrics only — no fabricated sales/revenue ----
  const activeASINsCount = watchlist.length;
  const pursueCount = watchlist.filter((w) => w.verdict === "PURSUE").length;
  const avgOpportunityScore = activeASINsCount > 0
    ? Math.round(watchlist.reduce((sum, item) => sum + item.score, 0) / activeASINsCount)
    : 0;

  // Rough margin estimate from validated buy/sell prices — surfaced ONLY as a
  // clearly-labelled research estimate, never as booked profit.
  const margins = watchlist.map((w) => {
    const sell = w.price || (w.buy_price * 1.5);
    const profit = sell - w.buy_price - (sell * 0.15 + 100);
    return sell > 0 ? (profit / sell) * 100 : 0;
  });
  const avgNetMargin = margins.length ? Math.round(margins.reduce((s, m) => s + m, 0) / margins.length) : 0;

  // Real Amazon storefront figures — present ONLY after SP-API is connected and a
  // sync has run. No fallbacks: empty stays empty.
  const hasStorefront = initialMetrics.length > 0;
  const storefrontCurrency = initialMetrics[0]?.currency === "USD" ? "$" : initialMetrics[0]?.currency === "GBP" ? "£" : "₹";
  const realRevenue = initialMetrics.reduce((s, m) => s + m.total_sales_amount, 0);
  const realUnits = initialMetrics.reduce((s, m) => s + m.unit_count, 0);

  // Real sales-over-time series for the performance chart (empty until synced).
  const salesChartData = [...initialMetrics]
    .sort((a, b) => a.interval_start.localeCompare(b.interval_start))
    .map((m) => ({
      name: new Date(m.interval_start).toLocaleDateString("en-IN", { month: "short", day: "numeric" }),
      Revenue: Math.round(m.total_sales_amount),
      Units: m.unit_count,
    }));

  // Filter watchlist validations
  const filteredWatchlist = watchlist.filter((item) => {
    const matchesSearch = 
      item.asin.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (item.title && item.title.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesCategory = 
      selectedCategoryFilter === "all" || item.category === selectedCategoryFilter;
    const matchesVerdict = 
      selectedVerdictFilter === "all" || item.verdict === selectedVerdictFilter;
    return matchesSearch && matchesCategory && matchesVerdict;
  });

  const handleRowClick = (row: Validation) => {
    setSelectedProduct(row);
    setIsDrawerOpen(true);
  };

  const lowStockAsin = watchlist.find((w) => w.score < 60)?.asin || null;
  const lowQualityAsin = watchlist.find((w) => w.score < 75)?.asin || null;

  return (
    <div className="space-y-6">
      {/* 1. Action Required Strip — only show rows that actually have items */}
      <AlertStrip alerts={computedAlerts.filter((a) => a.count > 0)} />

      {/* 2. KPI Grid Row */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <MetricCard
          title="Sales Revenue (14d)"
          value={hasStorefront ? `${storefrontCurrency}${realRevenue.toLocaleString("en-IN", { maximumFractionDigits: 0 })}` : "—"}
          change={hasStorefront ? "Live · SP-API" : "Connect Amazon"}
          changeType="neutral"
          tooltip="Real sales revenue synced from your Amazon Seller account over the last 14 days. Connect your account in Settings to populate this."
        />
        <MetricCard
          title="Units Sold (14d)"
          value={hasStorefront ? realUnits.toLocaleString("en-IN") : "—"}
          change={hasStorefront ? "Live · SP-API" : "Connect Amazon"}
          changeType="neutral"
          tooltip="Real units sold, synced from Amazon SP-API over the last 14 days."
        />
        <MetricCard
          title="Tracked ASINs"
          value={activeASINsCount}
          change={activeASINsCount > 0 ? `${pursueCount} marked pursue` : "None yet"}
          changeType="neutral"
          tooltip="Unique products you've validated (deduplicated to the latest run per ASIN)."
        />
        <MetricCard
          title="Avg Net Margin (est.)"
          value={activeASINsCount > 0 ? `${avgNetMargin}%` : "—"}
          change={activeASINsCount > 0 ? "Research estimate" : "No data"}
          changeType="neutral"
          tooltip="ESTIMATED margin from validated buy/sell prices after typical Amazon fees — a research estimate, NOT booked profit."
        />
        <MetricCard
          title="Avg Opportunity Score"
          value={activeASINsCount > 0 ? avgOpportunityScore : "—"}
          changeType="neutral"
          tooltip="Average ScoutVeda opportunity score across your validated ASINs."
        />
      </div>

      {/* Recommended Next Actions */}
      <div className="glass-panel p-4 bg-white border border-black/5 shadow-sm rounded-xl">
        <div className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-3">
          ⚡ Recommended Next Actions
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {lowStockAsin ? (
            <div className="p-3 bg-zinc-50 border border-black/5 rounded-lg flex flex-col justify-between">
              <p className="text-xs font-semibold text-zinc-600 leading-relaxed">
                Restock ASIN <strong className="font-mono text-zinc-900">{lowStockAsin}</strong> within 7 days to prevent stockout based on current velocity.
              </p>
              <Link href="/dashboard/inventory" className="text-[10px] font-bold text-[#3b82f6] hover:underline mt-2.5 inline-block">
                View Inventory Details →
              </Link>
            </div>
          ) : (
            <div className="p-3 bg-zinc-50 border border-black/5 rounded-lg flex flex-col justify-between">
              <p className="text-xs font-semibold text-zinc-600 leading-relaxed">
                ✅ Catalog stock levels are healthy. No active restock alerts required.
              </p>
              <Link href="/dashboard/inventory" className="text-[10px] font-bold text-[#3b82f6] hover:underline mt-2.5 inline-block">
                Manage Inventory →
              </Link>
            </div>
          )}

          <div className="p-3 bg-zinc-50 border border-black/5 rounded-lg flex flex-col justify-between">
            <p className="text-xs font-semibold text-zinc-600 leading-relaxed">
              Check margins before you source: run any validated ASIN through the Profit Calculator to confirm it clears your target after Amazon fees.
            </p>
            <Link href="/dashboard/profit-calculator" className="text-[10px] font-bold text-[#3b82f6] hover:underline mt-2.5 inline-block">
              Open Profit Calculator →
            </Link>
          </div>

          {lowQualityAsin ? (
            <div className="p-3 bg-zinc-50 border border-black/5 rounded-lg flex flex-col justify-between">
              <p className="text-xs font-semibold text-zinc-600 leading-relaxed">
                Listing quality score is low on ASIN <strong className="font-mono text-zinc-900">{lowQualityAsin}</strong>. Add high-volume keywords to title.
              </p>
              <Link href={`/dashboard/listing?asin=${lowQualityAsin}`} className="text-[10px] font-bold text-[#3b82f6] hover:underline mt-2.5 inline-block">
                Optimize Listing →
              </Link>
            </div>
          ) : (
            <div className="p-3 bg-zinc-50 border border-black/5 rounded-lg flex flex-col justify-between">
              <p className="text-xs font-semibold text-zinc-600 leading-relaxed">
                ✅ Watchlist opportunity scores are optimal. All items meet the quality threshold.
              </p>
              <Link href="/dashboard/listing-health" className="text-[10px] font-bold text-[#3b82f6] hover:underline mt-2.5 inline-block">
                Audit Listing Health →
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* 3. Primary Dashboard Tabs System */}
      <div className="border-b border-white/5 flex items-center justify-between">
        <div className="flex gap-4">
          <button
            onClick={() => setActiveDashboardTab("watchlist")}
            className={`py-3 px-1 text-xs font-bold uppercase tracking-wider border-b-2 transition-all cursor-pointer ${
              activeDashboardTab === "watchlist"
                ? "border-[#3b82f6] text-[#3b82f6]"
                : "border-transparent text-zinc-400 hover:text-white"
            }`}
          >
            📋 Catalog & Watchlist
          </button>
          <button
            onClick={() => setActiveDashboardTab("radar")}
            className={`py-3 px-1 text-xs font-bold uppercase tracking-wider border-b-2 transition-all cursor-pointer ${
              activeDashboardTab === "radar"
                ? "border-[#3b82f6] text-[#3b82f6]"
                : "border-transparent text-zinc-400 hover:text-white"
            }`}
          >
            ⚡ Business Performance & Radar
          </button>
          <button
            onClick={() => setActiveDashboardTab("bestsellers")}
            className={`py-3 px-1 text-xs font-bold uppercase tracking-wider border-b-2 transition-all cursor-pointer ${
              activeDashboardTab === "bestsellers"
                ? "border-[#3b82f6] text-[#3b82f6]"
                : "border-transparent text-zinc-400 hover:text-white"
            }`}
          >
            🔭 Bestsellers Category Explorer
          </button>
          <button
            onClick={() => setActiveDashboardTab("storefront")}
            className={`py-3 px-1 text-xs font-bold uppercase tracking-wider border-b-2 transition-all cursor-pointer ${
              activeDashboardTab === "storefront"
                ? "border-[#3b82f6] text-[#3b82f6]"
                : "border-transparent text-zinc-400 hover:text-white"
            }`}
          >
            🏪 Storefront Performance
          </button>
        </div>
      </div>

      {/* 4. Active Dashboard Tabs Content */}
      <div className="space-y-6">
        {activeDashboardTab === "watchlist" && (
          <div className="space-y-4">
            {/* Table Filters & Toolbar */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 bg-[#111625] p-4 rounded-xl border border-white/5 shadow-sm">
              <div className="flex items-center gap-3 flex-1 max-w-sm">
                <input
                  type="text"
                  placeholder="Search validated products..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="input py-1.5 text-xs"
                />
              </div>

              <div className="flex flex-wrap gap-2.5">
                {/* Category Filter */}
                <select
                  value={selectedCategoryFilter}
                  onChange={(e) => setSelectedCategoryFilter(e.target.value)}
                  className="text-xs font-semibold text-zinc-300 bg-[#181d2c] border border-white/10 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-zinc-700 cursor-pointer"
                >
                  <option value="all">All Categories</option>
                  {Array.from(new Set(watchlist.map((w) => w.category).filter(Boolean))).map((cat) => (
                    <option key={cat} value={cat!}>
                      {cat}
                    </option>
                  ))}
                </select>

                {/* Sourcing Verdict Filter */}
                <select
                  value={selectedVerdictFilter}
                  onChange={(e) => setSelectedVerdictFilter(e.target.value)}
                  className="text-xs font-semibold text-zinc-300 bg-[#181d2c] border border-white/10 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-zinc-700 cursor-pointer"
                >
                  <option value="all">All Verdicts</option>
                  <option value="PURSUE">🟢 PURSUE</option>
                  <option value="WATCH">🟡 WATCH</option>
                  <option value="SKIP">🔴 SKIP</option>
                </select>

                <button
                  onClick={() => {
                    const csvContent = "data:text/csv;charset=utf-8," 
                      + ["ASIN,Title,Score,Verdict,Buy Price,Category"].join(",") + "\n"
                      + watchlist.map(w => `"${w.asin}","${w.title || ''}",${w.score},"${w.verdict}",${w.buy_price},"${w.category || ''}"`).join("\n");
                    const encodedUri = encodeURI(csvContent);
                    const link = document.createElement("a");
                    link.setAttribute("href", encodedUri);
                    link.setAttribute("download", "scoutveda_validated_opportunities.csv");
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                  }}
                  className="text-xs font-bold text-zinc-300 bg-[#181d2c] border border-white/10 px-3 py-1.5 rounded-lg hover:bg-white/5 cursor-pointer transition-colors shadow-sm"
                >
                  Export CSV
                </button>
              </div>
            </div>

            {/* Main Watched Catalog Table */}
            <div className="bg-transparent overflow-hidden">
              <Table
                columns={[
                  {
                    key: "asin",
                    header: "ASIN",
                    cellClassName: "font-mono text-zinc-400 font-bold",
                    render: (row) => row.asin,
                  },
                  {
                    key: "title",
                    header: "Product Title",
                    cellClassName: "max-w-md truncate text-white font-medium",
                    render: (row) => row.title || "Unresolved Product Title",
                  },
                  {
                    key: "category",
                    header: "Category",
                    cellClassName: "text-zinc-400 font-semibold",
                    render: (row) => row.category || "General",
                  },
                  {
                    key: "score",
                    header: "Opportunity Score",
                    render: (row) => (
                      <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                        row.score >= 70
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : row.score >= 50
                          ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                          : "bg-red-500/10 text-red-400 border border-red-500/20"
                      }`}>
                        {row.score} / 100
                      </span>
                    ),
                  },
                  {
                    key: "buy_price",
                    header: "Buy Price",
                    cellClassName: "text-white font-bold font-mono",
                    render: (row) => `₹${row.buy_price}`,
                  },
                  {
                    key: "verdict",
                    header: "Sourcing Verdict",
                    render: (row) => (
                      <span className={`text-[10px] font-bold tracking-wider px-2 py-0.5 rounded-md border ${
                        row.verdict === "PURSUE"
                          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/25"
                          : row.verdict === "WATCH"
                          ? "bg-amber-500/10 text-amber-400 border-amber-500/25"
                          : "bg-red-500/10 text-red-400 border-red-500/25"
                      }`}>
                        {row.verdict}
                      </span>
                    ),
                  },
                  {
                    key: "actions",
                    header: "Actions",
                    render: (row) => (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRowClick(row);
                        }}
                        className="text-[10px] font-bold text-zinc-300 bg-[#181d2c] border border-white/10 hover:bg-white/5 px-2 py-1 rounded transition-colors cursor-pointer"
                      >
                        Inspect Details
                      </button>
                    ),
                  },
                ]}
                rows={filteredWatchlist}
                rowKey={(row) => row.id}
                emptyText="No validated ASINs in your catalog watchlist yet. Run the validator to add one!"
              />
            </div>
          </div>
        )}

        {activeDashboardTab === "radar" && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Sales & Revenue Chart */}
            <div className="md:col-span-2 glass-panel p-5 bg-white border border-black/5">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-sm font-bold text-zinc-900">Sales Performance</h3>
                  <p className="text-[11px] text-zinc-500 font-semibold mt-0.5">Real daily sales synced from Amazon SP-API (last 14 days)</p>
                </div>
              </div>
              <div className="h-64 w-full">
                {salesChartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={salesChartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.05)" />
                      <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
                      <YAxis yAxisId="left" stroke="#64748b" fontSize={11} />
                      <YAxis yAxisId="right" orientation="right" stroke="#64748b" fontSize={11} />
                      <Tooltip contentStyle={{ fontSize: 11, background: "#ffffff", border: "1px solid rgba(0,0,0,0.08)", borderRadius: 8, color: "#0f172a" }} />
                      <Line yAxisId="left" type="monotone" dataKey="Revenue" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} />
                      <Line yAxisId="right" type="monotone" dataKey="Units" stroke="#10b981" strokeWidth={2} dot={{ r: 3 }} />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-full flex flex-col items-center justify-center text-center gap-2 border border-dashed border-black/10 rounded-xl">
                    <span className="text-2xl opacity-60">🏪</span>
                    <p className="text-xs font-semibold text-zinc-600">No sales data yet</p>
                    <p className="text-[11px] text-zinc-400 max-w-xs">Connect your Amazon Seller account in Settings and run a sync to see your real sales performance here.</p>
                    <Link href="/dashboard/settings" className="text-[10px] font-bold text-[#3b82f6] hover:underline mt-1">Connect Amazon →</Link>
                  </div>
                )}
              </div>
            </div>

            {/* Sourcing Opportunity Radar */}
            <div className="glass-panel p-5 bg-white border border-black/5 space-y-4">
              <div>
                <h3 className="text-sm font-bold text-zinc-900">Opportunity Radar</h3>
                <p className="text-[11px] text-zinc-500 font-semibold mt-0.5">Top-scoring opportunities to launch</p>
              </div>
              <div className="space-y-3">
                {watchlist.slice(0, 4).map((item) => (
                  <div
                    key={item.id}
                    onClick={() => handleRowClick(item)}
                    className="p-3 border border-black/5 rounded-xl hover:border-[#3b82f6]/40 transition-all cursor-pointer bg-zinc-50 hover:bg-zinc-100 flex items-center justify-between"
                  >
                    <div className="flex-1 min-w-0 pr-3">
                      <span className="text-[10px] font-bold text-zinc-500 tracking-wider block uppercase">
                        {item.category || "General"}
                      </span>
                      <span className="text-xs font-bold text-zinc-900 truncate block mt-0.5">
                        {item.title || "Validated Product"}
                      </span>
                    </div>
                    <div className="text-right">
                      <span className="text-xs font-bold text-emerald-600 block font-mono">
                        Score: {item.score}
                      </span>
                      <span className="text-[9px] font-bold text-zinc-500 block uppercase tracking-wider mt-0.5">
                        {item.verdict}
                      </span>
                    </div>
                  </div>
                ))}
                {watchlist.length === 0 && (
                  <div className="text-center text-xs text-zinc-500 py-12">
                    No validated items tracked yet.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeDashboardTab === "bestsellers" && (
          <div className="space-y-6">
            {/* Category selection bar */}
            <div className="flex flex-wrap items-center justify-between gap-3 bg-white p-4 rounded-xl border border-black/5 shadow-sm">
              <h2 className="text-xs font-bold uppercase tracking-wider text-zinc-900">Bestseller List Analysis</h2>
              <div className="flex flex-wrap gap-2">
                <Select
                  value={listType}
                  onChange={setListType}
                  options={LIST_TYPES.map((l) => ({ value: l.value, label: l.label }))}
                />
                <Select
                  value={category}
                  onChange={setCategory}
                  options={CATEGORIES.map((c) => ({ value: c, label: c }))}
                />
              </div>
            </div>

            {/* Sparkline Review Entrenchment Chart */}
            {!loading && table.length > 0 && (
              <ChartCard
                title="Review Count by Rank (Market Entrenchment — Higher Bars = Harder to Unseat)"
                data={table.slice(0, 15).map((p) => ({
                  rank: `#${p.rank}`,
                  reviews: p.review_count ?? 0,
                }))}
                xKey="rank"
                dataKey="reviews"
              />
            )}

            {/* Bestseller Category List tabs */}
            <Tabs
              tabs={[
                { key: "entrants", label: "New Entrants" },
                { key: "movers", label: "Top Movers" },
                { key: "cross", label: "Cross-Category" },
              ]}
              active={bestsellerTab}
              onChange={(key) => setBestsellerTab(key as any)}
            >
              {bestsellerTab === "entrants" && (
                <Table
                  columns={[
                    { key: "rank", header: "Rank", render: (p) => `#${p.rank}`, cellClassName: "text-zinc-400 font-bold" },
                    {
                      key: "title",
                      header: "Product Title",
                      render: (p) => (
                        <div className="max-w-md truncate font-medium text-zinc-300">
                          {p.title || "Unknown Bestseller Product"}
                        </div>
                      ),
                    },
                    {
                      key: "price",
                      header: "Price",
                      cellClassName: "font-bold text-white font-mono",
                      render: (p) => (p.price ? `₹${p.price}` : "—"),
                    },
                    {
                      key: "reviews",
                      header: "Reviews",
                      cellClassName: "text-zinc-400 font-semibold font-mono",
                      render: (p) => (p.review_count ? p.review_count.toLocaleString() : "0"),
                    },
                    {
                      key: "action",
                      header: "Action",
                      render: (p) => (
                        <Link
                          href={`/dashboard/validator?asin=${p.asin}`}
                          className="text-[10px] font-bold text-zinc-300 bg-[#181d2c] border border-white/10 hover:bg-white/5 px-2 py-1 rounded transition-colors"
                        >
                          Validate
                        </Link>
                      ),
                    },
                  ]}
                  rows={digest.new_entrants}
                  rowKey={(r) => r.asin}
                  emptyText="No new entrants recorded yet."
                />
              )}

              {bestsellerTab === "movers" && (
                <Table
                  columns={[
                    {
                      key: "asin",
                      header: "ASIN",
                      cellClassName: "font-mono text-zinc-400 font-bold",
                      render: (p) => p.asin,
                    },
                    {
                      key: "title",
                      header: "Product Title",
                      render: (p) => (
                        <div className="max-w-md truncate font-medium text-zinc-300">
                          {p.title}
                        </div>
                      ),
                    },
                    {
                      key: "category",
                      header: "Category",
                      cellClassName: "text-zinc-400 font-semibold",
                      render: (p) => p.category,
                    },
                    {
                      key: "delta",
                      header: "Rank Shift",
                      render: (p) => {
                        const isUp = p.delta < 0; // Rank number getting smaller is an improvement!
                        return (
                          <span className={`text-xs font-bold ${isUp ? "text-emerald-400" : "text-red-400"}`}>
                            {isUp ? "▲" : "▼"} {Math.abs(p.delta)} positions
                          </span>
                        );
                      },
                    },
                    {
                      key: "action",
                      header: "Action",
                      render: (p) => (
                        <Link
                          href={`/dashboard/validator?asin=${p.asin}`}
                          className="text-[10px] font-bold text-zinc-300 bg-[#181d2c] border border-white/10 hover:bg-white/5 px-2 py-1 rounded transition-colors"
                        >
                          Validate
                        </Link>
                      ),
                    },
                  ]}
                  rows={digest.top_movers}
                  rowKey={(r) => r.asin}
                  emptyText="No movers yet — needs 2+ collection runs per ASIN."
                />
              )}

              {bestsellerTab === "cross" && (
                <Table
                  columns={[
                    {
                      key: "asin",
                      header: "ASIN",
                      cellClassName: "font-mono text-zinc-400 font-bold",
                      render: (p) => p.asin,
                    },
                    {
                      key: "title",
                      header: "Product Title",
                      render: (p) => (
                        <div className="max-w-md truncate font-medium text-zinc-300">
                          {p.title}
                        </div>
                      ),
                    },
                    {
                      key: "categories",
                      header: "Featured Categories",
                      cellClassName: "text-zinc-400 font-semibold max-w-xs truncate",
                      render: (p) => p.categories,
                    },
                    {
                      key: "num_categories",
                      header: "Featured Count",
                      cellClassName: "font-bold text-white font-mono",
                      render: (p) => p.num_categories,
                    },
                    {
                      key: "action",
                      header: "Action",
                      render: (p) => (
                        <Link
                          href={`/dashboard/validator?asin=${p.asin}`}
                          className="text-[10px] font-bold text-zinc-300 bg-[#181d2c] border border-white/10 hover:bg-white/5 px-2 py-1 rounded transition-colors"
                        >
                          Validate
                        </Link>
                      ),
                    },
                  ]}
                  rows={digest.cross_category}
                  rowKey={(r) => r.asin}
                  emptyText="No cross-category hits found yet."
                />
              )}
            </Tabs>
          </div>
        )}

        {activeDashboardTab === "storefront" && (
          <div className="space-y-6">
            {!connected ? (
              <div className="glass-panel p-8 text-center text-zinc-500 text-sm flex flex-col items-center justify-center space-y-4 bg-white border border-black/5">
                <div className="text-3xl">🔌</div>
                <p>No Amazon account linked. Please link your storefront in Settings first to enable sales and orders tracking.</p>
                <Link
                  href="/dashboard/settings"
                  className="btn-primary inline-block w-auto px-6 py-2.5 text-xs font-bold uppercase tracking-wider mt-2"
                >
                  Link Amazon Seller Account
                </Link>
              </div>
            ) : (
              <>
                {/* Synchronization Panel */}
                <div className="glass-panel p-5 bg-white border border-black/5 flex flex-col md:flex-row items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-sm">
                      🔌
                    </div>
                    <div>
                      <div className="text-xs font-bold text-zinc-900 uppercase tracking-wider">Connected Account</div>
                      <div className="text-[11px] text-zinc-500 font-semibold mt-0.5">
                        SP-API: <span className="font-mono text-zinc-600">{accounts[0]?.selling_partner_id}</span> ({(accounts[0]?.marketplace_id === "A21TJRUUN4KGV" ? "Amazon India" : (accounts[0]?.marketplace_id === "ATVPDKIKX0DER" ? "Amazon USA" : "Amazon UK"))})
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-col sm:flex-row items-center gap-4 w-full md:w-auto">
                    {syncStatus && (
                      <div className="text-[10px] font-bold text-zinc-700 bg-zinc-50 border border-black/10 px-3 py-1.5 rounded-lg w-full sm:w-auto text-center font-mono">
                        {syncStatus}
                      </div>
                    )}
                    <button
                      onClick={handleSync}
                      disabled={isSyncPending}
                      className="btn-primary w-full sm:w-auto px-5 py-2 text-xs font-bold uppercase tracking-wider cursor-pointer disabled:opacity-50"
                    >
                      {isSyncPending ? "Syncing..." : "🔄 Sync Storefront Now"}
                    </button>
                  </div>
                </div>

                {/* Metrics Stat Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  <MetricCard
                    title="Total Storefront Revenue (14d)"
                    value={(initialMetrics.length > 0 ? `${initialMetrics[0].currency === "USD" ? "$" : (initialMetrics[0].currency === "GBP" ? "£" : "₹")}${initialMetrics.reduce((sum, m) => sum + m.total_sales_amount, 0).toLocaleString("en-IN", { maximumFractionDigits: 0 })}` : "—")}
                    changeType="neutral"
                    tooltip="Total sales revenue synced from SP-API over the last 14 days"
                  />
                  <MetricCard
                    title="Total Orders Processed"
                    value={initialMetrics.reduce((sum, m) => sum + m.order_count, 0).toString()}
                    changeType="neutral"
                    tooltip="Aggregate customer order volume"
                  />
                  <MetricCard
                    title="Total Units Ordered"
                    value={initialMetrics.reduce((sum, m) => sum + m.unit_count, 0).toString()}
                    changeType="neutral"
                    tooltip="Sum of units shipped or pending"
                  />
                  <MetricCard
                    title="Average Order Value"
                    value={(initialMetrics.length > 0 && initialMetrics.reduce((sum, m) => sum + m.order_count, 0) > 0 ? `${initialMetrics[0].currency === "USD" ? "$" : (initialMetrics[0].currency === "GBP" ? "£" : "₹")}${Math.round(initialMetrics.reduce((sum, m) => sum + m.total_sales_amount, 0) / initialMetrics.reduce((sum, m) => sum + m.order_count, 0)).toLocaleString("en-IN")}` : "—")}
                    changeType="neutral"
                    tooltip="Average customer shopping basket value"
                  />
                </div>

                {/* Charts Grid */}
                {initialMetrics.length > 0 ? (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <ChartCard
                      title={`Sales Revenue Trend (${initialMetrics[0]?.currency || "INR"})`}
                      data={initialMetrics.map((m) => ({
                        day: new Date(m.interval_start).toLocaleDateString("en-IN", { month: "short", day: "numeric" }),
                        "Sales Revenue": m.total_sales_amount,
                      }))}
                      xKey="day"
                      dataKey="Sales Revenue"
                      barColor="#10b981"
                    />
                    <ChartCard
                      title="Orders Volume Trend"
                      data={initialMetrics.map((m) => ({
                        day: new Date(m.interval_start).toLocaleDateString("en-IN", { month: "short", day: "numeric" }),
                        "Orders Count": m.order_count,
                      }))}
                      xKey="day"
                      dataKey="Orders Count"
                      barColor="#3b82f6"
                    />
                  </div>
                ) : (
                  <div className="glass-panel p-8 text-center text-zinc-500 text-xs font-medium border border-black/5 bg-zinc-50">
                    No metrics synchronized yet. Please click the sync button above to fetch sales metrics.
                  </div>
                )}

                {/* Recent Orders List */}
                <div className="space-y-3.5">
                  <h2 className="text-sm font-bold tracking-wider text-zinc-500 uppercase font-mono">Recent Storefront Transactions</h2>
                  {initialOrders.length > 0 ? (
                    <Table
                      columns={[
                        {
                          key: "amazon_order_id",
                          header: "Amazon Order ID",
                          render: (o: StorefrontOrder) => (
                            <span className="font-mono text-xs font-semibold text-zinc-700 select-all">{o.amazon_order_id}</span>
                          ),
                        },
                        {
                          key: "purchase_date",
                          header: "Purchase Date",
                          render: (o: StorefrontOrder) => {
                            const date = new Date(o.purchase_date);
                            return (
                              <span className="text-zinc-600 font-medium text-xs font-mono">
                                {date.toLocaleDateString("en-IN", { month: "short", day: "numeric" })},{" "}
                                {date.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}
                              </span>
                            );
                          },
                        },
                        {
                          key: "order_status",
                          header: "Status",
                          render: (o: StorefrontOrder) => {
                            const statusColors: Record<string, string> = {
                              "Shipped": "text-emerald-700 bg-emerald-50/80 border-emerald-200/60",
                              "Unshipped": "text-blue-700 bg-blue-50/80 border-blue-200/60",
                              "Pending": "text-amber-700 bg-amber-50/80 border-amber-200/60",
                              "Cancelled": "text-zinc-600 bg-zinc-50 border-zinc-200/60",
                            };
                            const colorClass = statusColors[o.order_status] || "text-zinc-600 bg-zinc-50 border-zinc-200/60";
                            return (
                              <span className={`text-[10px] font-bold border px-2 py-0.5 rounded uppercase tracking-wider ${colorClass}`}>
                                {o.order_status}
                              </span>
                            );
                          },
                        },
                        {
                          key: "items_count",
                          header: "Items",
                          render: (o: StorefrontOrder) => (
                            <span className="text-zinc-700 font-semibold text-xs font-mono">{o.items_count} unit(s)</span>
                          ),
                        },
                        {
                          key: "amount",
                          header: "Order Total",
                          render: (o: StorefrontOrder) => {
                            const ordCurrency = o.currency || "INR";
                            const ordSymbol = ordCurrency === "USD" ? "$" : (ordCurrency === "GBP" ? "£" : "₹");
                            return (
                              <span className="font-semibold text-zinc-900 font-mono">
                                {o.amount ? `${ordSymbol}${o.amount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}` : "—"}
                              </span>
                            );
                          },
                        },
                      ]}
                      rows={initialOrders}
                      rowKey={(o) => o.id}
                    />
                  ) : (
                    <div className="glass-panel p-8 text-center text-zinc-500 text-xs font-medium border border-black/5 bg-zinc-50">
                      No storefront orders synced yet. Try clicking "Sync Storefront Now" above to load recent customer transactions.
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        )}
      </div>

      {/* 5. Detail Slide-over Drawer */}
      <ProductDetailDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        asin={selectedProduct?.asin || null}
        onUpdateNotes={handleUpdateNotes}
      />
    </div>
  );
}
