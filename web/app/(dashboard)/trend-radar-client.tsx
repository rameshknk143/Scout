"use client";

import { useEffect, useState } from "react";
import StatCard from "@/components/StatCard";
import CaveatBox from "@/components/CaveatBox";
import { Table, Tabs, Select, ChartCard, type Column } from "@/components/ui";
import type { Digest, SnapshotRow } from "@/lib/api";
import { CATEGORIES } from "@/lib/constants";
import { getCategoryTable } from "@/lib/actions";

type TabKey = "entrants" | "movers" | "cross";
type MoverRow = Digest["top_movers"][number];
type CrossRow = Digest["cross_category"][number];

export default function TrendRadarClient({ digest }: { digest: Digest }) {
  const [tab, setTab] = useState<TabKey>("entrants");
  const [category, setCategory] = useState<string>(CATEGORIES[0]);
  const [table, setTable] = useState<SnapshotRow[]>([]);
  const [loading, setLoading] = useState(true);

  const coldStart = digest.collection_dates.length < 2;

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getCategoryTable(category).then((res) => {
      if (!cancelled) {
        setTable(res.products);
        setLoading(false);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [category]);

  const chartData = table.slice(0, 15).map((p) => ({
    rank: `#${p.rank}`,
    reviews: p.review_count ?? 0,
  }));

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          label="New Entrants (top 100)"
          value={digest.new_entrants.length}
          delay={0}
        />
        <StatCard label="Top Movers" value={digest.top_movers.length} delay={0.05} />
        <StatCard
          label="Cross-Category Hits"
          value={digest.cross_category.length}
          delay={0.1}
        />
      </div>

      {coldStart && (
        <CaveatBox>
          Cold start: with only one night of data so far, every product shows
          as a &quot;new entrant&quot; and there&apos;s no rank history yet for
          &quot;movers&quot; — that&apos;s expected, not a bug. Signals firm up
          after 1-2 weeks of nightly collection.
        </CaveatBox>
      )}

      <Tabs
        tabs={[
          { key: "entrants", label: "New Entrants" },
          { key: "movers", label: "Top Movers" },
          { key: "cross", label: "Cross-Category" },
        ]}
        active={tab}
        onChange={(key) => setTab(key as TabKey)}
      >
        {tab === "entrants" && (
          <Table
            columns={productColumns(true)}
            rows={digest.new_entrants}
            rowKey={(r) => r.asin}
            emptyText="No new entrants recorded yet."
          />
        )}
        {tab === "movers" && (
          <Table
            columns={moverColumns}
            rows={digest.top_movers}
            rowKey={(r) => r.asin}
            emptyText="No movers yet — needs 2+ collection runs per ASIN."
          />
        )}
        {tab === "cross" && (
          <Table
            columns={crossColumns}
            rows={digest.cross_category}
            rowKey={(r) => r.asin}
            emptyText="No cross-category hits found yet."
          />
        )}
      </Tabs>

      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Browse by category</h2>
          <Select
            value={category}
            onChange={setCategory}
            options={CATEGORIES.map((c) => ({ value: c, label: c }))}
          />
        </div>

        {!loading && chartData.length > 0 && (
          <ChartCard
            title="Review count by rank (entrenchment — higher bars = tougher to unseat)"
            data={chartData}
            xKey="rank"
            dataKey="reviews"
          />
        )}

        <Table
          columns={productColumns(false)}
          rows={table}
          rowKey={(r) => r.asin}
          loading={loading}
          loadingText="Loading…"
          emptyText="No snapshot data for this category yet."
        />
      </div>
    </div>
  );
}

function productColumns(showCategory: boolean): Column<SnapshotRow>[] {
  const cols: Column<SnapshotRow>[] = [
    { key: "rank", header: "Rank", render: (p) => `#${p.rank}`, cellClassName: "text-muted" },
    {
      key: "title",
      header: "Product",
      render: (p) => (
        <span className="max-w-sm truncate block" title={p.title ?? ""}>
          {p.title}
        </span>
      ),
    },
  ];
  if (showCategory) {
    cols.push({
      key: "category",
      header: "Category",
      render: (p) => (p as SnapshotRow & { category?: string }).category,
      cellClassName: "text-muted",
    });
  }
  cols.push(
    {
      key: "price",
      header: "Price",
      render: (p) => (p.price != null ? `₹${p.price.toLocaleString("en-IN")}` : "—"),
    },
    { key: "rating", header: "Rating", render: (p) => `${p.rating ?? "—"} ⭐` },
    {
      key: "reviews",
      header: "Reviews",
      render: (p) => p.review_count?.toLocaleString("en-IN") ?? "—",
    },
  );
  return cols;
}

const moverColumns: Column<MoverRow>[] = [
  {
    key: "title",
    header: "Product",
    render: (r) => (
      <span className="max-w-md truncate block" title={r.title}>
        {r.title}
      </span>
    ),
  },
  { key: "category", header: "Category", render: (r) => r.category, cellClassName: "text-muted" },
  { key: "first_rank", header: "First rank", render: (r) => `#${r.first_rank}` },
  { key: "latest_rank", header: "Latest rank", render: (r) => `#${r.latest_rank}` },
  {
    key: "delta",
    header: "Δ",
    render: (r) => `+${r.delta}`,
    cellClassName: "text-green font-semibold",
  },
];

const crossColumns: Column<CrossRow>[] = [
  {
    key: "title",
    header: "Product",
    render: (r) => (
      <span className="max-w-md truncate block" title={r.title}>
        {r.title}
      </span>
    ),
  },
  {
    key: "categories",
    header: "Categories",
    render: (r) => r.categories,
    cellClassName: "text-muted",
  },
  { key: "num_categories", header: "# Categories", render: (r) => r.num_categories },
  { key: "best_rank", header: "Best rank", render: (r) => `#${r.best_rank}` },
];
