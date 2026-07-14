"use client";

import { useEffect, useState, useTransition } from "react";
import { Table, Card, Field, MiniStat } from "@/components/ui";
import { getMyProducts, saveMyProduct, deleteMyProduct } from "@/lib/actions";
import type { MyProduct } from "@/lib/api";

export default function MyProductsClient() {
  const [products, setProducts] = useState<MyProduct[]>([]);
  const [isPending, startTransition] = useTransition();

  // Form states
  const [asin, setAsin] = useState("");
  const [sku, setSku] = useState("");
  const [title, setTitle] = useState("");
  const [supplierCost, setSupplierCost] = useState("150");
  const [shippingFee, setShippingFee] = useState("20");
  const [targetMargin, setTargetMargin] = useState("30");
  const [supplierDetails, setSupplierDetails] = useState("");

  const [formError, setFormError] = useState<string | null>(null);

  const fetchProducts = () => {
    startTransition(async () => {
      try {
        const res = await getMyProducts();
        setProducts(res.products);
      } catch (err) {
        console.error("Failed to fetch active products:", err);
      }
    });
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  const handleAddProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!asin.trim()) {
      setFormError("ASIN is required.");
      return;
    }

    try {
      await saveMyProduct({
        asin: asin.trim().toUpperCase(),
        sku: sku.trim() || null,
        title: title.trim() || null,
        supplier_cost: parseFloat(supplierCost) || 0,
        shipping_fee: parseFloat(shippingFee) || 0,
        target_margin: parseFloat(targetMargin) || 30,
        supplier_details: supplierDetails.trim(),
      });

      // Reset form
      setAsin("");
      setSku("");
      setTitle("");
      setSupplierCost("150");
      setShippingFee("20");
      setTargetMargin("30");
      setSupplierDetails("");

      // Refresh listing
      fetchProducts();
    } catch (err: any) {
      setFormError(err.message || "Failed to save product.");
    }
  };

  const handleDelete = async (targetAsin: string) => {
    if (!confirm(`Are you sure you want to remove ASIN ${targetAsin} from your active catalog?`)) {
      return;
    }
    try {
      await deleteMyProduct(targetAsin);
      fetchProducts();
    } catch (err) {
      console.error(err);
    }
  };

  // Compute stats
  const totalSkus = products.length;
  const avgCost = totalSkus
    ? products.reduce((acc, p) => acc + (p.supplier_cost + p.shipping_fee), 0) / totalSkus
    : 0;
  const avgMargin = totalSkus
    ? products.reduce((acc, p) => acc + p.target_margin, 0) / totalSkus
    : 0;

  const columns = [
    {
      key: "asin",
      header: "ASIN",
      render: (p: MyProduct) => <span className="font-mono text-xs font-semibold text-zinc-300">{p.asin}</span>,
    },
    {
      key: "sku",
      header: "Seller SKU",
      render: (p: MyProduct) => <span className="font-mono text-[11px] font-medium text-zinc-400">{p.sku || "—"}</span>,
    },
    {
      key: "title",
      header: "Product / Niche Name",
      render: (p: MyProduct) => (
        <span className="font-medium text-white max-w-xs truncate block" title={p.title || p.asin}>
          {p.title || "—"}
        </span>
      ),
    },
    {
      key: "supplier_cost",
      header: "Unit Cost",
      render: (p: MyProduct) => <span className="font-medium text-white font-mono">₹{p.supplier_cost.toLocaleString("en-IN")}</span>,
    },
    {
      key: "shipping_fee",
      header: "Shipping",
      render: (p: MyProduct) => <span className="font-medium text-zinc-400 font-mono">₹{p.shipping_fee.toLocaleString("en-IN")}</span>,
    },
    {
      key: "total_cost",
      header: "Total Cost",
      render: (p: MyProduct) => (
        <span className="font-semibold text-white font-mono">
          ₹{(p.supplier_cost + p.shipping_fee).toLocaleString("en-IN")}
        </span>
      ),
    },
    {
      key: "target_margin",
      header: "Target Margin",
      render: (p: MyProduct) => (
        <span className="font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded px-1.5 py-0.5 text-[10px]">
          {p.target_margin}%
        </span>
      ),
    },
    {
      key: "action",
      header: "Action",
      render: (p: MyProduct) => (
        <button
          onClick={() => handleDelete(p.asin)}
          className="text-[10px] font-bold text-red-400 bg-red-500/10 hover:bg-red-500/20 px-2 py-1 rounded transition-colors border border-red-500/20 cursor-pointer"
        >
          Remove
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Metrics Card Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MiniStat label="Total Active SKUs" value={totalSkus.toString()} />
        <MiniStat
          label="Average Landed Cost"
          value={totalSkus ? `₹${avgCost.toFixed(2)}` : "—"}
        />
        <MiniStat
          label="Avg Target Margin"
          value={totalSkus ? `${avgMargin.toFixed(1)}%` : "—"}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Sourcing Add Panel */}
        <div className="lg:col-span-4 bg-[#111625] border border-white/5 rounded-xl p-5 shadow-sm space-y-4 h-fit">
          <div className="text-sm font-semibold text-white">Add Catalog Listing</div>
          <form onSubmit={handleAddProduct} className="space-y-3.5">
            <div>
              <label className="block text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-1">
                Amazon ASIN *
              </label>
              <input
                type="text"
                value={asin}
                onChange={(e) => setAsin(e.target.value)}
                placeholder="e.g. B0D4DZ7WL2"
                required
                className="input font-mono uppercase text-xs"
              />
            </div>
            <div>
              <label className="block text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-1">
                Seller SKU (optional)
              </label>
              <input
                type="text"
                value={sku}
                onChange={(e) => setSku(e.target.value)}
                placeholder="e.g. CK-SIL-CASE-12"
                className="input font-mono text-xs"
              />
            </div>
            <div>
              <label className="block text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-1">
                Product Title / Niche Name
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. City Knights Silicone Case"
                className="input text-xs"
              />
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-1">
                  Supplier Cost (₹)
                </label>
                <input
                  type="number"
                  value={supplierCost}
                  onChange={(e) => setSupplierCost(e.target.value)}
                  className="input text-xs"
                />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-1">
                  Shipping Fee (₹)
                </label>
                <input
                  type="number"
                  value={shippingFee}
                  onChange={(e) => setShippingFee(e.target.value)}
                  className="input text-xs"
                />
              </div>
            </div>

            <div>
              <label className="block text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-1">
                Target Gross Margin (%)
              </label>
              <input
                type="number"
                value={targetMargin}
                onChange={(e) => setTargetMargin(e.target.value)}
                className="input text-xs"
              />
            </div>

            <div>
              <label className="block text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-1">
                Supplier Sourcing Details
              </label>
              <textarea
                value={supplierDetails}
                onChange={(e) => setSupplierDetails(e.target.value)}
                placeholder="e.g. Alibaba supplier Shenzhen Tech, lead time 15 days..."
                className="w-full h-20 border border-white/10 rounded-lg p-2.5 text-xs outline-none focus:border-zinc-500 text-white bg-[#181d2c] resize-none leading-relaxed"
              />
            </div>

            {formError && <div className="text-xs text-red-400 font-semibold">{formError}</div>}

            <button type="submit" className="btn-primary w-full text-xs py-2">
              Save Active Product
            </button>
          </form>
        </div>

        {/* Inventory Catalog Panel */}
        <div className="lg:col-span-8 bg-[#111625]/20 border border-white/5 rounded-xl p-5 shadow-sm space-y-4">
          <div className="text-sm font-semibold text-white">Active Catalog Trackings</div>
          {isPending ? (
            <div className="flex flex-col items-center justify-center py-16 space-y-3">
              <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              <div className="text-xs text-zinc-500 font-semibold">Updating catalog list...</div>
            </div>
          ) : (
            <Table
              columns={columns}
              rows={products}
              rowKey={(p) => p.asin}
              emptyText="No products logged in your active catalog yet. Register your first listing on the left!"
            />
          )}
        </div>
      </div>
    </div>
  );
}
