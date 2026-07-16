import { Suspense } from "react";
import { getAmazonStatus, getStorefrontSalesData, getStorefrontOrdersData } from "@/lib/actions";
import StorefrontClient from "./storefront-client";

export const dynamic = "force-dynamic";

export const metadata = {
  title: "Storefront Performance | ScoutVeda Reseller OS",
  description: "Track live sales, unit volume, and recent orders from your connected Amazon seller account.",
};

async function StorefrontDataLoader() {
  const [status, salesRes, ordersRes] = await Promise.all([
    getAmazonStatus().catch(() => ({ connected: false, accounts: [] })),
    getStorefrontSalesData().catch(() => ({ metrics: [] })),
    getStorefrontOrdersData().catch(() => ({ orders: [] })),
  ]);

  return (
    <StorefrontClient
      connected={status.connected}
      accounts={status.accounts || []}
      initialMetrics={salesRes.metrics || []}
      initialOrders={ordersRes.orders || []}
    />
  );
}

export default function StorefrontPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-4 border-b border-white/5">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Storefront Performance</h1>
          <p className="text-xs text-zinc-400 font-medium mt-1">
            Monitor real-time sales volume, revenue growth, and live order processing status.
          </p>
        </div>
      </div>

      <Suspense fallback={<div className="text-zinc-400 text-xs font-semibold py-8 text-center bg-[#111625] rounded-xl border border-white/5 shadow-sm">Loading storefront data stream...</div>}>
        <StorefrontDataLoader />
      </Suspense>
    </div>
  );
}
