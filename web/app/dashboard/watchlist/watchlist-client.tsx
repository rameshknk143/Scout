"use client";

import { useMemo, useState } from "react";
import { Table, Select, EmptyState, ProductDetailDrawer } from "@/components/ui";
import type { Validation } from "@/lib/api";
import { updateWatchlistNotes } from "@/lib/actions";

export default function WatchlistClient({
  validations = [],
}: {
  validations: Validation[];
}) {
  const [searchQuery, setSearchQuery] = useState("");
  const [verdictFilter, setVerdictFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");

  // Selected product details drawer state
  const [selectedProduct, setSelectedProduct] = useState<any>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const verdicts = useMemo(
    () => Array.from(new Set(validations.map((v) => v.verdict))).sort(),
    [validations]
  );
  const categories = useMemo(
    () =>
      Array.from(
        new Set(validations.map((v) => v.category).filter(Boolean))
      ).sort() as string[],
    [validations]
  );

  // Filter watchlist validations
  const filtered = useMemo(() => {
    return validations.filter((v) => {
      const matchesSearch = 
        v.asin.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (v.title && v.title.toLowerCase().includes(searchQuery.toLowerCase()));
      const matchesVerdict = !verdictFilter || v.verdict === verdictFilter;
      const matchesCategory = !categoryFilter || v.category === categoryFilter;
      return matchesSearch && matchesVerdict && matchesCategory;
    });
  }, [validations, searchQuery, verdictFilter, categoryFilter]);

  const handleRowClick = (row: Validation) => {
    setSelectedProduct({
      asin: row.asin,
      title: row.title || "Unknown Product",
      price: row.buy_price * 1.5,
      score: row.score,
      verdict: row.verdict,
      category: row.category,
      notes: row.notes,
      buy_price: row.buy_price,
      sell_price: row.buy_price * 1.5,
      net_margin: 32.5,
      rating: 4.2,
      reviews: 84,
    });
    setIsDrawerOpen(true);
  };

  const handleUpdateNotes = async (asin: string, newNotes: string) => {
    try {
      await updateWatchlistNotes(asin, newNotes);
      setSelectedProduct((prev: any) => prev ? { ...prev, notes: newNotes } : null);
    } catch (err) {
      // handle error
    }
  };

  if (!validations.length) {
    return (
      <div className="bg-[#111625] p-8 rounded-xl border border-white/5 shadow-sm">
        <EmptyState text="No validations logged yet — run the Validator first." />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Search and Filters Toolbar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 bg-[#111625] p-4 rounded-xl border border-white/5 shadow-sm">
        <div className="flex items-center gap-3 flex-1 max-w-sm">
          <input
            type="text"
            placeholder="Search validated products..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input py-1.5 text-xs text-white"
          />
        </div>

        <div className="flex flex-wrap gap-2.5">
          {/* Category Filter */}
          <Select
            value={categoryFilter}
            onChange={setCategoryFilter}
            placeholder="All Categories"
            options={categories.map((c) => ({ value: c, label: c }))}
          />

          {/* Verdict Filter */}
          <Select
            value={verdictFilter}
            onChange={setVerdictFilter}
            placeholder="All Verdicts"
            options={verdicts.map((v) => ({ value: v, label: v }))}
          />

          <button
            onClick={() => {
              const csvContent = "data:text/csv;charset=utf-8," 
                + ["ASIN,Title,Score,Verdict,Buy Price,Category"].join(",") + "\n"
                + validations.map(w => `"${w.asin}","${w.title || ''}",${w.score},"${w.verdict}",${w.buy_price},"${w.category || ''}"`).join("\n");
              const encodedUri = encodeURI(csvContent);
              const link = document.createElement("a");
              link.setAttribute("href", encodedUri);
              link.setAttribute("download", "scoutveda_watchlist_export.csv");
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

      {/* Watchlist Table */}
      <div className="bg-transparent overflow-hidden">
        <Table
          columns={[
            {
              key: "asin",
              header: "ASIN",
              cellClassName: "font-mono text-zinc-400 font-bold",
              render: (v) => v.asin,
            },
            {
              key: "title",
              header: "Product Title",
              cellClassName: "max-w-md truncate text-white font-medium",
              render: (v) => v.title || "Unresolved Product Title",
            },
            {
              key: "category",
              header: "Category",
              cellClassName: "text-zinc-400 font-semibold",
              render: (v) => v.category ?? "General",
            },
            {
              key: "score",
              header: "Opportunity Score",
              render: (v) => (
                <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                  v.score >= 70
                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                    : v.score >= 50
                    ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                    : "bg-red-500/10 text-red-400 border border-red-500/20"
                }`}>
                  {v.score} / 100
                </span>
              ),
            },
            {
              key: "buy_price",
              header: "Buy Price",
              cellClassName: "text-white font-bold font-mono",
              render: (v) => `₹${v.buy_price.toLocaleString("en-IN")}`,
            },
            {
              key: "verdict",
              header: "Sourcing Verdict",
              render: (v) => (
                <span className={`text-[10px] font-bold tracking-wider px-2 py-0.5 rounded-md border ${
                  v.verdict === "PURSUE"
                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/25"
                    : v.verdict === "WATCH"
                    ? "bg-amber-500/10 text-amber-400 border-amber-500/25"
                    : "bg-red-500/10 text-red-400 border-red-500/25"
                }`}>
                  {v.verdict}
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
                  Inspect
                </button>
              ),
            },
          ]}
          rows={filtered}
          rowKey={(v) => v.id}
        />
      </div>

      <div className="text-xs font-semibold text-zinc-400 pl-1">
        {filtered.length} of {validations.length} opportunity validations shown.
      </div>

      {/* Detail Slide-over Drawer */}
      <ProductDetailDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        asin={selectedProduct?.asin || null}
        onUpdateNotes={handleUpdateNotes}
      />
    </div>
  );
}
