"use client";

import { useEffect, useState, useTransition } from "react";
import Link from "next/link";
import { Table, ProductDetailDrawer } from "@/components/ui";
import { searchProductDatabase, updateWatchlistNotes } from "@/lib/actions";
import { CATEGORIES } from "@/lib/constants";
import type { SnapshotRow } from "@/lib/api";

export default function ProductDatabaseClient() {
  const [products, setProducts] = useState<SnapshotRow[]>([]);
  const [total, setTotal] = useState(0);
  const [isPending, startTransition] = useTransition();

  // Search & Filter state
  const [q, setQ] = useState("");
  const [category, setCategory] = useState("");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [minRank, setMinRank] = useState("");
  const [maxRank, setMaxRank] = useState("");
  
  // Applied filters state for queries
  const [appliedFilters, setAppliedFilters] = useState({
    q: "",
    category: "",
    minPrice: "",
    maxPrice: "",
    minRank: "",
    maxRank: "",
  });

  const [limit] = useState(25);
  const [offset, setOffset] = useState(0);

  // Selected product details drawer state
  const [selectedProduct, setSelectedProduct] = useState<any>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  useEffect(() => {
    startTransition(async () => {
      try {
        const res = await searchProductDatabase({
          q: appliedFilters.q || undefined,
          category: appliedFilters.category || undefined,
          min_price: appliedFilters.minPrice ? parseFloat(appliedFilters.minPrice) : undefined,
          max_price: appliedFilters.maxPrice ? parseFloat(appliedFilters.maxPrice) : undefined,
          min_rank: appliedFilters.minRank ? parseInt(appliedFilters.minRank, 10) : undefined,
          max_rank: appliedFilters.maxRank ? parseInt(appliedFilters.maxRank, 10) : undefined,
          limit,
          offset,
        });
        setProducts(res.products);
        setTotal(res.total);
      } catch (err) {
        console.error("Failed to query product database:", err);
      }
    });
  }, [appliedFilters, limit, offset]);

  const handleApplyFilters = (e: React.FormEvent) => {
    e.preventDefault();
    setOffset(0);
    setAppliedFilters({ q, category, minPrice, maxPrice, minRank, maxRank });
  };

  const handleClearFilters = () => {
    setQ("");
    setCategory("");
    setMinPrice("");
    setMaxPrice("");
    setMinRank("");
    setMaxRank("");
    setOffset(0);
    setAppliedFilters({ q: "", category: "", minPrice: "", maxPrice: "", minRank: "", maxRank: "" });
  };

  const handleRowClick = (row: SnapshotRow) => {
    setSelectedProduct({
      asin: row.asin,
      title: row.title || "Unknown Product",
      price: row.price || 0,
      score: 50, // default neutral placeholder
      verdict: "WATCH",
      category: row.category,
      notes: "",
      buy_price: (row.price || 0) * 0.7,
      sell_price: row.price || 0,
      net_margin: 30.0,
      rating: row.rating || 0.0,
      reviews: row.review_count || 0,
    });
    setIsDrawerOpen(true);
  };

  const handleUpdateNotes = async (asin: string, newNotes: string) => {
    try {
      await updateWatchlistNotes(asin, newNotes);
      setSelectedProduct((prev: any) => (prev ? { ...prev, notes: newNotes } : null));
    } catch (err) {
      console.error(err);
    }
  };

  const page = Math.floor(offset / limit) + 1;
  const totalPages = Math.ceil(total / limit) || 1;

  const columns = [
    {
      key: "asin",
      header: "ASIN",
      render: (p: SnapshotRow) => (
        <span className="font-mono text-xs font-semibold text-zinc-300 bg-[#181d2c] px-1.5 py-0.5 rounded border border-white/5">
          {p.asin}
        </span>
      ),
    },
    {
      key: "title",
      header: "Product Title",
      render: (p: SnapshotRow) => (
        <span
          onClick={() => handleRowClick(p)}
          className="font-medium text-white hover:text-white hover:underline cursor-pointer max-w-md truncate block"
          title={p.title || p.asin}
        >
          {p.title || "(no title)"}
        </span>
      ),
    },
    {
      key: "category",
      header: "Category",
      render: (p: SnapshotRow) => (
        <span className="text-zinc-400 font-medium">{p.category || "—"}</span>
      ),
    },
    {
      key: "rank",
      header: "BSR Rank",
      render: (p: SnapshotRow) => (
        <span className="font-semibold text-white font-mono">
          {p.rank != null ? `#${p.rank.toLocaleString("en-IN")}` : "—"}
        </span>
      ),
    },
    {
      key: "price",
      header: "Price",
      render: (p: SnapshotRow) => (
        <span className="font-semibold text-white font-mono">
          {p.price != null ? `₹${p.price.toLocaleString("en-IN")}` : "—"}
        </span>
      ),
    },
    {
      key: "reviews",
      header: "Reviews",
      render: (p: SnapshotRow) => (
        <div className="flex items-center gap-1.5">
          <span className="font-semibold text-zinc-300 font-mono">
            {p.review_count != null ? p.review_count.toLocaleString("en-IN") : "—"}
          </span>
          {p.rating != null && (
            <span className="text-[10px] bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded px-1 font-bold">
              {p.rating} ⭐
            </span>
          )}
        </div>
      ),
    },
    {
      key: "action",
      header: "Actions",
      render: (p: SnapshotRow) => (
        <Link
          href={`/dashboard/validator?asin=${p.asin}`}
          className="text-[10px] font-bold text-zinc-300 bg-[#181d2c] border border-white/10 hover:bg-white/5 px-2 py-1.5 rounded transition-colors"
        >
          Validate Opportunity
        </Link>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Search and Filters panel */}
      <form onSubmit={handleApplyFilters} className="glass-panel p-5 bg-[#111625] space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div className="md:col-span-2">
            <label className="block text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-1">
              Search Title or ASIN
            </label>
            <input
              type="text"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="e.g. kick scooter, B0D4DZ7WL2..."
              className="input text-xs text-white bg-[#181d2c]"
            />
          </div>
          <div>
            <label className="block text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-1">
              Category
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="input text-xs cursor-pointer text-white bg-[#181d2c] border-white/10"
            >
              <option value="">All Categories</option>
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-end gap-2">
            <button type="submit" className="btn-primary w-full text-xs py-2">
              Apply Filters
            </button>
            <button
              type="button"
              onClick={handleClearFilters}
              className="text-xs font-bold text-zinc-300 bg-[#181d2c] border border-white/10 hover:bg-white/5 px-3 py-2 rounded-lg transition-colors"
            >
              Clear
            </button>
          </div>
        </div>

        {/* Detailed limits sliders / numeric overrides */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-3 border-t border-white/5">
          <div>
            <label className="block text-[9px] font-bold text-zinc-500 uppercase tracking-wider mb-0.5">
              Min Price (₹)
            </label>
            <input
              type="number"
              value={minPrice}
              onChange={(e) => setMinPrice(e.target.value)}
              placeholder="0"
              className="input text-xs py-1"
            />
          </div>
          <div>
            <label className="block text-[9px] font-bold text-zinc-500 uppercase tracking-wider mb-0.5">
              Max Price (₹)
            </label>
            <input
              type="number"
              value={maxPrice}
              onChange={(e) => setMaxPrice(e.target.value)}
              placeholder="99999"
              className="input text-xs py-1"
            />
          </div>
          <div>
            <label className="block text-[9px] font-bold text-zinc-500 uppercase tracking-wider mb-0.5">
              Min BSR Rank
            </label>
            <input
              type="number"
              value={minRank}
              onChange={(e) => setMinRank(e.target.value)}
              placeholder="1"
              className="input text-xs py-1"
            />
          </div>
          <div>
            <label className="block text-[9px] font-bold text-zinc-500 uppercase tracking-wider mb-0.5">
              Max BSR Rank
            </label>
            <input
              type="number"
              value={maxRank}
              onChange={(e) => setMaxRank(e.target.value)}
              placeholder="10000"
              className="input text-xs py-1"
            />
          </div>
        </div>
      </form>

      {/* Database Listing Card */}
      <div className="glass-panel p-5 shadow-sm space-y-4 bg-[#111625]/20 border border-white/5">
        <div className="flex items-center justify-between">
          <div className="text-sm font-semibold text-white">
            Search Results ({total.toLocaleString("en-IN")} products found)
          </div>
          
          {/* Pagination status */}
          <div className="text-xs text-zinc-500 font-semibold font-mono">
            Page {page} of {totalPages}
          </div>
        </div>

        {isPending ? (
          <div className="flex flex-col items-center justify-center py-16 space-y-3">
            <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            <div className="text-xs text-zinc-500 font-semibold">Querying database snapshots...</div>
          </div>
        ) : (
          <Table
            columns={columns}
            rows={products}
            rowKey={(p) => p.asin}
            emptyText="No products matching the active filters were found in your nightly database."
          />
        )}

        {/* Pagination controls */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between pt-4 border-t border-white/5">
            <button
              onClick={() => setOffset(Math.max(0, offset - limit))}
              disabled={offset === 0 || isPending}
              className="text-xs font-bold text-zinc-300 bg-[#181d2c] border border-white/10 px-3 py-2 rounded-lg hover:bg-white/5 disabled:opacity-50 cursor-pointer transition-colors"
            >
              ← Previous Page
            </button>
            <button
              onClick={() => setOffset(offset + limit)}
              disabled={offset + limit >= total || isPending}
              className="text-xs font-bold text-zinc-300 bg-[#181d2c] border border-white/10 px-3 py-2 rounded-lg hover:bg-white/5 disabled:opacity-50 cursor-pointer transition-colors"
            >
              Next Page →
            </button>
          </div>
        )}
      </div>

      {/* Selected Product Detail Drawer */}
      {selectedProduct && (
        <ProductDetailDrawer
          isOpen={isDrawerOpen}
          onClose={() => setIsDrawerOpen(false)}
          asin={selectedProduct.asin}
          onUpdateNotes={handleUpdateNotes}
        />
      )}
    </div>
  );
}
