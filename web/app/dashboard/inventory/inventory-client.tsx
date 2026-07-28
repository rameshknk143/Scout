"use client";

import { useEffect, useState, useTransition } from "react";
import { Table, MiniStat } from "@/components/ui";
import { getMyProducts, saveMyProduct } from "@/lib/actions";
import type { MyProduct } from "@/lib/api";

export default function InventoryClient() {
  const [products, setProducts] = useState<MyProduct[]>([]);
  const [isPending, startTransition] = useTransition();

  // Edit stock state
  const [editingAsin, setEditingAsin] = useState<string | null>(null);
  const [editStock, setEditStock] = useState("");
  const [editLeadTime, setEditLeadTime] = useState("");

  const fetchProducts = () => {
    startTransition(async () => {
      try {
        const res = await getMyProducts();
        setProducts(res.products);
      } catch (err) {
        console.error("Failed to fetch inventory catalog:", err);
      }
    });
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  const handleStartEdit = (p: MyProduct) => {
    setEditingAsin(p.asin);
    setEditStock(p.current_stock.toString());
    setEditLeadTime(p.lead_time_days.toString());
  };

  const handleSaveEdit = async (p: MyProduct) => {
    try {
      await saveMyProduct({
        asin: p.asin,
        title: p.title,
        sku: p.sku,
        supplier_cost: p.supplier_cost,
        shipping_fee: p.shipping_fee,
        target_margin: p.target_margin,
        supplier_details: p.supplier_details,
        current_stock: parseInt(editStock, 10) || 0,
        lead_time_days: parseInt(editLeadTime, 10) || 0,
      });
      setEditingAsin(null);
      fetchProducts();
    } catch (err) {
      console.error(err);
    }
  };

  // Compute stats
  const totalSkus = products.length;

  // Stock cover and re-order forecasting both need per-ASIN sales velocity, which
  // requires order-item level data we do not sync yet (storefront_orders carries no
  // ASIN, and storefront_sales_metrics is aggregate-only). Until that lands we show
  // an explicit "not available" state rather than an estimate.
  const totalUnits = products.reduce((acc, p) => acc + p.current_stock, 0);

  const avgLeadTime = totalSkus
    ? products.reduce((acc, p) => acc + p.lead_time_days, 0) / totalSkus
    : 0;

  const unavailable = (
    <span
      className="text-[10px] font-bold px-2 py-0.5 rounded border font-mono bg-zinc-500/10 text-zinc-400 border-zinc-500/20"
      title="Needs per-ASIN sales velocity. Amazon order-item sync is not connected yet."
    >
      Needs sales data
    </span>
  );

  const columns = [
    {
      key: "asin",
      header: "ASIN",
      render: (p: MyProduct) => <span className="font-mono text-xs font-semibold text-zinc-300">{p.asin}</span>,
    },
    {
      key: "sku",
      header: "SKU",
      render: (p: MyProduct) => <span className="font-mono text-[11px] font-medium text-zinc-400">{p.sku || "—"}</span>,
    },
    {
      key: "title",
      header: "Product / Niche",
      render: (p: MyProduct) => (
        <span className="font-medium text-zinc-900 max-w-xs truncate block" title={p.title || p.asin}>
          {p.title || "—"}
        </span>
      ),
    },
    {
      key: "current_stock",
      header: "Current Stock",
      render: (p: MyProduct) => {
        if (editingAsin === p.asin) {
          return (
            <input
              type="number"
              value={editStock}
              onChange={(e) => setEditStock(e.target.value)}
              className="w-16 border border-white/10 rounded p-1 text-xs outline-none focus:border-zinc-500 font-semibold bg-[#181d2c] text-white font-mono"
            />
          );
        }
        return (
          <span className="font-bold font-mono text-zinc-900">
            {p.current_stock} units
          </span>
        );
      },
    },
    {
      key: "lead_time_days",
      header: "Lead Time (Days)",
      render: (p: MyProduct) => {
        if (editingAsin === p.asin) {
          return (
            <input
              type="number"
              value={editLeadTime}
              onChange={(e) => setEditLeadTime(e.target.value)}
              className="w-16 border border-white/10 rounded p-1 text-xs outline-none focus:border-zinc-500 font-semibold bg-[#181d2c] text-white font-mono"
            />
          );
        }
        return <span className="font-semibold text-zinc-300 font-mono">{p.lead_time_days} days</span>;
      },
    },
    {
      key: "days_remaining",
      header: "Stock Cover",
      render: () => unavailable,
    },
    {
      key: "reorder_date",
      header: "Re-order Forecast",
      render: () => unavailable,
    },
    {
      key: "action",
      header: "Actions",
      render: (p: MyProduct) => {
        if (editingAsin === p.asin) {
          return (
            <div className="flex gap-1">
              <button
                onClick={() => handleSaveEdit(p)}
                className="btn-primary text-[10px] py-1 px-2.5"
              >
                Save
              </button>
              <button
                onClick={() => setEditingAsin(null)}
                className="text-[10px] font-bold text-zinc-300 bg-[#181d2c] border border-white/10 hover:bg-white/5 px-2 py-1 rounded transition-colors cursor-pointer"
              >
                Cancel
              </button>
            </div>
          );
        }
        return (
          <button
            onClick={() => handleStartEdit(p)}
            className="text-[10px] font-bold text-zinc-300 bg-[#181d2c] border border-white/10 hover:bg-white/5 px-2 py-1 rounded transition-colors cursor-pointer shadow-sm"
          >
            Update Levels
          </button>
        );
      },
    },
  ];

  return (
    <div className="space-y-6">
      {/* Metrics Card Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MiniStat label="Total Active SKUs" value={totalSkus.toString()} />
        <MiniStat
          label="Average Lead Time"
          value={totalSkus ? `${avgLeadTime.toFixed(1)} days` : "—"}
        />
        <MiniStat
          label="Total Units in Stock"
          value={totalSkus ? totalUnits.toLocaleString("en-IN") : "—"}
        />
      </div>

      <div className="text-[11px] text-zinc-400 bg-zinc-500/5 border border-black/5 rounded-xl px-4 py-3 leading-relaxed">
        <strong className="text-zinc-300">Stock cover and re-order forecasting are not live yet.</strong>{" "}
        Both need per-ASIN sales velocity. The nightly storefront sync currently returns
        aggregate revenue and unit counts only — no ASIN breakdown — so there is no honest
        way to compute days-of-cover per SKU. These columns will populate once order-item
        level sync is connected.
      </div>

      <div className="glass-panel p-5 bg-white border border-black/5 rounded-xl shadow-sm space-y-4">
        <div className="text-sm font-semibold text-zinc-900">Active Stock Audits</div>
        {isPending ? (
          <div className="flex flex-col items-center justify-center py-16 space-y-3">
            <div className="w-6 h-6 border-2 border-zinc-700 border-t-transparent rounded-full animate-spin"></div>
            <div className="text-xs text-zinc-500 font-semibold font-mono">Updating stock analytics...</div>
          </div>
        ) : (
          <Table
            columns={columns}
            rows={products}
            rowKey={(p) => p.asin}
            emptyText="No active products logged in your catalog. Add products in the 'My Products' tab first to audit inventory."
          />
        )}
      </div>
    </div>
  );
}
