"use client";

import { useMemo, useState } from "react";
import { Table, Select, EmptyState, ProductDetailDrawer } from "@/components/ui";
import type { Alert } from "@/lib/api";
import { updateWatchlistNotes } from "@/lib/actions";

const ALERT_TYPE_LABELS: Record<Alert["alert_type"], string> = {
  price_change: "Price change",
  entered_top3: "Entered top 3",
  rank_climbing: "Rank climbing",
  rank_sliding: "Rank sliding",
  review_surge: "Review surge",
  dropped_from_list: "Dropped from list",
};

export default function AlertsClient({ alerts = [] }: { alerts: Alert[] }) {
  const [searchQuery, setSearchQuery] = useState("");
  const [severityFilter, setSeverityFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");

  // Selected product details drawer state
  const [selectedProduct, setSelectedProduct] = useState<any>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const types = useMemo(
    () => Array.from(new Set(alerts.map((a) => a.alert_type))).sort(),
    [alerts]
  );

  // Filter alerts
  const filtered = useMemo(() => {
    return alerts.filter((a) => {
      const matchesSearch = 
        a.asin.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (a.title && a.title.toLowerCase().includes(searchQuery.toLowerCase()));
      const matchesSeverity = !severityFilter || a.severity === severityFilter;
      const matchesType = !typeFilter || a.alert_type === typeFilter;
      return matchesSearch && matchesSeverity && matchesType;
    });
  }, [alerts, searchQuery, severityFilter, typeFilter]);

  const handleUpdateNotes = async (asin: string, newNotes: string) => {
    try {
      await updateWatchlistNotes(asin, newNotes);
      setSelectedProduct((prev: any) => prev ? { ...prev, notes: newNotes } : null);
    } catch (err) {
      // handle error
    }
  };

  const handleRowClick = (row: Alert) => {
    // An alert row carries only the ASIN, title, category and a message. It
    // has no score, margin, rating or review count -- this used to invent all
    // of them (score 75, buy price = 60% of a price scraped out of the alert
    // text, rating 4.2, 95 reviews) and present them as this product's real
    // figures. Pass through only what the alert actually knows; the drawer
    // renders "—" for the rest.
    const priceMatch = row.message.match(/₹\s?([\d,]+)/);
    const price = priceMatch ? Number(priceMatch[1].replace(/,/g, "")) : undefined;

    setSelectedProduct({
      asin: row.asin,
      title: row.title || row.asin,
      category: row.category,
      price,
      sell_price: price,
      notes: "",
    });
    setIsDrawerOpen(true);
  };

  if (!alerts.length) {
    return (
      <div className="bg-white p-8 rounded-xl border border-black/5 shadow-sm">
        <EmptyState text="No alerts yet — alerts need at least two nightly collection runs for a watched ASIN before there's anything to compare. Run the Validator on a few ASINs, then check back tomorrow." />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Disclaimer Caveat Box */}
      <div className="caveat-box bg-zinc-50 border border-black/5 rounded-xl p-4 text-xs text-zinc-500 leading-relaxed">
        <strong>⚠️ Information Note:</strong> &quot;Dropped from list&quot; means the ASIN fell out of that category&apos;s top-30 ranked page. ScoutVeda reads the public bestseller/new-releases list, not live inventory, so it can&apos;t tell a real stock-out apart from just losing rank. Treat it as a sourcing indicator to review, not confirmed stock exhaustion.
      </div>

      {/* Search and Filters Toolbar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 bg-white p-4 rounded-xl border border-black/5 shadow-sm">
        <div className="flex items-center gap-3 flex-1 max-w-sm">
          <input
            type="text"
            placeholder="Search alerts by ASIN or title..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input py-1.5 text-xs"
          />
        </div>

        <div className="flex flex-wrap gap-2.5">
          {/* Severity Filter */}
          <Select
            value={severityFilter}
            onChange={setSeverityFilter}
            placeholder="All Severities"
            options={["high", "medium", "low"].map((s) => ({ value: s, label: s.toUpperCase() }))}
          />

          {/* Type Filter */}
          <Select
            value={typeFilter}
            onChange={setTypeFilter}
            placeholder="All Alert Types"
            options={types.map((t) => ({ value: t, label: ALERT_TYPE_LABELS[t] }))}
          />
        </div>
      </div>

      {/* Alerts Table */}
      <div className="bg-transparent overflow-hidden">
        <Table
          columns={[
            {
              key: "severity",
              header: "Severity",
              render: (a) => (
                <span className={`text-[10px] font-bold tracking-wider px-2 py-0.5 rounded-md border uppercase ${
                  a.severity === "high"
                    ? "bg-red-50 text-red-700 border-red-200/60"
                    : a.severity === "medium"
                    ? "bg-amber-55/80 text-amber-700 border-amber-200/60"
                    : "bg-blue-50 text-blue-700 border-blue-200/60"
                }`}>
                  {a.severity}
                </span>
              ),
            },
            {
              key: "alert_type",
              header: "Alert Type",
              cellClassName: "text-zinc-500 font-semibold text-xs",
              render: (a) => ALERT_TYPE_LABELS[a.alert_type],
            },
            {
              key: "title",
              header: "Product Title",
              cellClassName: "max-w-md truncate text-zinc-900 font-semibold",
              render: (a) => a.title || a.asin,
            },
            {
              key: "category",
              header: "Category",
              cellClassName: "text-zinc-500 font-semibold text-xs",
              render: (a) => a.category ?? "—",
            },
            {
              key: "message",
              header: "Details",
              cellClassName: "text-zinc-700 font-semibold text-xs",
              render: (a) => a.message,
            },
            {
              key: "detected_at",
              header: "Detected",
              cellClassName: "text-zinc-500 font-medium text-xs",
              render: (a) =>
                new Date(a.detected_at).toLocaleString("en-IN", {
                  dateStyle: "medium",
                  timeStyle: "short",
                }),
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
                  className="text-[10px] font-bold text-zinc-700 bg-zinc-50 border border-black/10 hover:bg-zinc-100 px-2 py-1 rounded transition-colors cursor-pointer"
                >
                  Analyze
                </button>
              ),
            },
          ]}
          rows={filtered}
          rowKey={(a) => `${a.asin}-${a.alert_type}-${a.detected_at}`}
        />
      </div>

      <div className="text-xs font-semibold text-zinc-500 pl-1">
        {filtered.length} of {alerts.length} activity alerts shown.
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
