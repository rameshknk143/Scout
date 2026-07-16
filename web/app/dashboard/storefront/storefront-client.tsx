"use client";

import { useState, useTransition } from "react";
import { Card, ChartCard, EmptyState, Table, MiniStat } from "@/components/ui";
import { syncStorefrontData } from "@/lib/actions";
import type { StorefrontSalesMetric, StorefrontOrder } from "@/lib/api";

interface ConnectedAccount {
  selling_partner_id: string;
  marketplace_id: string;
  connected_at: string;
}

interface StorefrontClientProps {
  connected: boolean;
  accounts: ConnectedAccount[];
  initialMetrics: StorefrontSalesMetric[];
  initialOrders: StorefrontOrder[];
}

export default function StorefrontClient({
  connected,
  accounts,
  initialMetrics,
  initialOrders,
}: StorefrontClientProps) {
  const [metrics, setMetrics] = useState<StorefrontSalesMetric[]>(initialMetrics);
  const [orders, setOrders] = useState<StorefrontOrder[]>(initialOrders);
  const [syncStatus, setSyncStatus] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const handleSync = () => {
    setSyncStatus("🕒 Synchronizing with Amazon Seller Central...");
    startTransition(async () => {
      try {
        const res = await syncStorefrontData();
        if (res.ok) {
          setSyncStatus("✅ Sync completed successfully! Reloading metrics...");
          // We can reload the page or fetch updated data. Let's do a window reload after a small timeout.
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

  const MARKETPLACE_NAMES: Record<string, string> = {
    "A21TJRUUN4KGV": "Amazon India",
    "ATVPDKIKX0DER": "Amazon USA",
    "A1F83G8C2ARO7P": "Amazon UK",
  };

  // 1. If not connected, show empty/setup state
  if (!connected) {
    return (
      <div className="glass-panel p-8 text-center text-zinc-400 text-sm flex flex-col items-center justify-center space-y-4">
        <div className="text-3xl">🔌</div>
        <p>No Amazon account linked. Please link your storefront in Settings first to enable sales and orders tracking.</p>
        <a
          href="/dashboard/settings"
          className="btn-primary inline-block w-auto px-6 py-2.5 text-xs font-bold uppercase tracking-wider mt-2"
        >
          Link Amazon Seller Account
        </a>
      </div>
    );
  }

  // 2. Format metrics for Recharts
  const chartData = metrics.map((m) => {
    const date = new Date(m.interval_start);
    const dayLabel = date.toLocaleDateString("en-IN", { month: "short", day: "numeric" });
    return {
      day: dayLabel,
      "Sales Revenue": m.total_sales_amount,
      "Orders Count": m.order_count,
    };
  });

  // Calculate totals and averages
  const currency = metrics[0]?.currency || "INR";
  const symbol = currency === "USD" ? "$" : (currency === "GBP" ? "£" : "₹");
  
  const totalRevenue = metrics.reduce((sum, m) => sum + m.total_sales_amount, 0);
  const totalOrders = metrics.reduce((sum, m) => sum + m.order_count, 0);
  const totalUnits = metrics.reduce((sum, m) => sum + m.unit_count, 0);
  const avgOrderValue = totalOrders > 0 ? totalRevenue / totalOrders : 0;

  const formatCurrency = (val: number) => {
    return `${symbol}${val.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
  };

  const columns = [
    {
      key: "amazon_order_id",
      header: "Amazon Order ID",
      render: (o: StorefrontOrder) => (
        <span className="font-mono text-xs font-semibold text-zinc-300 select-all">{o.amazon_order_id}</span>
      ),
    },
    {
      key: "purchase_date",
      header: "Purchase Date",
      render: (o: StorefrontOrder) => {
        const date = new Date(o.purchase_date);
        return (
          <span className="text-zinc-400 font-medium text-xs font-mono">
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
          "Shipped": "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
          "Unshipped": "text-blue-400 bg-blue-500/10 border-blue-500/20",
          "Pending": "text-amber-400 bg-amber-500/10 border-amber-500/20",
          "Cancelled": "text-zinc-500 bg-zinc-500/10 border-zinc-500/20",
        };
        const colorClass = statusColors[o.order_status] || "text-zinc-300 bg-zinc-500/10";
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
        <span className="text-zinc-300 font-semibold text-xs font-mono">{o.items_count} unit(s)</span>
      ),
    },
    {
      key: "amount",
      header: "Order Total",
      render: (o: StorefrontOrder) => {
        const ordCurrency = o.currency || "INR";
        const ordSymbol = ordCurrency === "USD" ? "$" : (ordCurrency === "GBP" ? "£" : "₹");
        return (
          <span className="font-semibold text-white font-mono">
            {o.amount ? `${ordSymbol}${o.amount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}` : "—"}
          </span>
        );
      },
    },
  ];

  return (
    <div className="space-y-6">
      {/* Synchronization Panel */}
      <div className="glass-panel p-5 bg-[#111625]/60 border border-white/5 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-sm">
            🔌
          </div>
          <div>
            <div className="text-xs font-bold text-white uppercase tracking-wider">Connected Account</div>
            <div className="text-[11px] text-zinc-400 font-semibold mt-0.5">
              SP-API: <span className="font-mono text-zinc-300">{accounts[0]?.selling_partner_id}</span> ({MARKETPLACE_NAMES[accounts[0]?.marketplace_id] || accounts[0]?.marketplace_id})
            </div>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row items-center gap-4 w-full md:w-auto">
          {syncStatus && (
            <div className="text-[10px] font-bold text-zinc-300 bg-[#161a29] border border-white/5 px-3 py-1.5 rounded-lg w-full sm:w-auto text-center font-mono">
              {syncStatus}
            </div>
          )}
          <button
            onClick={handleSync}
            disabled={isPending}
            className="btn-primary w-full sm:w-auto px-5 py-2 text-xs font-bold uppercase tracking-wider cursor-pointer disabled:opacity-50"
          >
            {isPending ? "Syncing..." : "🔄 Sync Storefront Now"}
          </button>
        </div>
      </div>

      {/* Metrics Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MiniStat label="Total Storefront Revenue (14d)" value={formatCurrency(totalRevenue)} />
        <MiniStat label="Total Orders Processed" value={totalOrders.toString()} />
        <MiniStat label="Total Units Ordered" value={totalUnits.toString()} />
        <MiniStat label="Average Order Value" value={formatCurrency(avgOrderValue)} />
      </div>

      {/* Charts Grid */}
      {metrics.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ChartCard
            title={`Sales Revenue Trend (${symbol})`}
            data={chartData}
            xKey="day"
            dataKey="Sales Revenue"
            barColor="#10b981"
          />
          <ChartCard
            title="Orders Volume Trend"
            data={chartData}
            xKey="day"
            dataKey="Orders Count"
            barColor="#3b82f6"
          />
        </div>
      ) : (
        <Card className="p-8 text-center text-zinc-400 text-xs font-medium border border-white/5 bg-[#111625]/20">
          No metrics synchronized yet. Please click the sync button above to fetch sales metrics.
        </Card>
      )}

      {/* Recent Orders List */}
      <div className="space-y-3.5">
        <h2 className="text-sm font-bold tracking-wider text-zinc-400 uppercase font-mono">Recent Storefront Transactions</h2>
        {orders.length > 0 ? (
          <Table columns={columns} rows={orders} rowKey={(o) => o.id} />
        ) : (
          <Card className="p-8 text-center text-zinc-400 text-xs font-medium border border-white/5 bg-[#111625]/20">
            No storefront orders synced yet. Try clicking "Sync Storefront Now" above to load recent customer transactions.
          </Card>
        )}
      </div>
    </div>
  );
}
