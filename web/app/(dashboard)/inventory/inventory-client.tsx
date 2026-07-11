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
  
  // Daily sales velocity estimation - mock defaults to 5 units/day or calculated
  const getVelocity = (p: MyProduct) => {
    // If the BSR is low (good), sales velocity is high
    return 5; 
  };

  const lowStockCount = products.filter((p) => {
    const velocity = getVelocity(p);
    const daysRemaining = p.current_stock / velocity;
    return daysRemaining <= p.lead_time_days;
  }).length;

  const avgLeadTime = totalSkus
    ? products.reduce((acc, p) => acc + p.lead_time_days, 0) / totalSkus
    : 0;

  const columns = [
    {
      key: "asin",
      header: "ASIN",
      render: (p: MyProduct) => <span className="font-mono text-xs font-semibold text-zinc-900">{p.asin}</span>,
    },
    {
      key: "sku",
      header: "SKU",
      render: (p: MyProduct) => <span className="font-mono text-[11px] font-medium text-zinc-500">{p.sku || "—"}</span>,
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
              className="w-16 border border-zinc-300 rounded p-1 text-xs outline-none focus:border-zinc-500 font-semibold"
            />
          );
        }
        const velocity = getVelocity(p);
        const daysRemaining = p.current_stock / velocity;
        const isLow = daysRemaining <= p.lead_time_days;
        return (
          <span className={`font-bold ${isLow ? "text-red-700 font-extrabold" : "text-zinc-900"}`}>
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
              className="w-16 border border-zinc-300 rounded p-1 text-xs outline-none focus:border-zinc-500 font-semibold"
            />
          );
        }
        return <span className="font-semibold text-zinc-700">{p.lead_time_days} days</span>;
      },
    },
    {
      key: "days_remaining",
      header: "Stock Cover",
      render: (p: MyProduct) => {
        const velocity = getVelocity(p);
        const daysRemaining = Math.ceil(p.current_stock / velocity);
        const isLow = daysRemaining <= p.lead_time_days;
        return (
          <span
            className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
              isLow
                ? "bg-red-50 text-red-800 border-red-100 animate-pulse"
                : "bg-emerald-50 text-emerald-800 border-emerald-100"
            }`}
          >
            {daysRemaining} days remaining
          </span>
        );
      },
    },
    {
      key: "reorder_date",
      header: "Re-order Forecast",
      render: (p: MyProduct) => {
        const velocity = getVelocity(p);
        const daysRemaining = Math.ceil(p.current_stock / velocity);
        const reorderInDays = daysRemaining - p.lead_time_days;
        
        if (reorderInDays <= 0) {
          return (
            <span className="text-[10px] font-extrabold text-red-700 uppercase tracking-wide">
              ⚠️ Order Immediately
            </span>
          );
        }
        
        const reorderDate = new Date();
        reorderDate.setDate(reorderDate.getDate() + reorderInDays);
        return (
          <span className="font-semibold text-zinc-800">
            {reorderDate.toLocaleDateString("en-IN", { month: "short", day: "numeric", year: "numeric" })}
            <span className="text-[10px] text-zinc-400 font-semibold ml-1.5">(in {reorderInDays}d)</span>
          </span>
        );
      },
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
                className="text-[10px] font-bold text-white bg-zinc-900 hover:bg-zinc-950 px-2 py-1 rounded transition-colors cursor-pointer"
              >
                Save
              </button>
              <button
                onClick={() => setEditingAsin(null)}
                className="text-[10px] font-bold text-zinc-600 bg-zinc-100 hover:bg-zinc-200 px-2 py-1 rounded border border-zinc-200 transition-colors cursor-pointer"
              >
                Cancel
              </button>
            </div>
          );
        }
        return (
          <button
            onClick={() => handleStartEdit(p)}
            className="text-[10px] font-bold text-zinc-700 bg-white hover:bg-zinc-50 border border-zinc-200 px-2 py-1 rounded transition-colors cursor-pointer shadow-sm"
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
          label="Reorder Warnings"
          value={lowStockCount.toString()}
        />
      </div>

      {/* Main Table Panel */}
      <div className="bg-white border border-zinc-200/80 rounded-xl p-5 shadow-sm space-y-4">
        <div className="text-sm font-semibold text-zinc-950">Active Stock Audits</div>
        {isPending ? (
          <div className="flex flex-col items-center justify-center py-16 space-y-3">
            <div className="w-6 h-6 border-2 border-zinc-950 border-t-transparent rounded-full animate-spin"></div>
            <div className="text-xs text-zinc-400 font-semibold">Updating stock analytics...</div>
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
