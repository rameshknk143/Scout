"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import StatCard from "@/components/StatCard";
import CaveatBox from "@/components/CaveatBox";
import type { Digest, SnapshotRow } from "@/lib/api";
import { CATEGORIES } from "@/lib/constants";
import { getCategoryTable } from "@/lib/actions";

type Tab = "entrants" | "movers" | "cross";

export default function TrendRadarClient({ digest }: { digest: Digest }) {
  const [tab, setTab] = useState<Tab>("entrants");
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

      <div>
        <div className="flex gap-1 mb-4 border-b border-white/8">
          {(
            [
              ["entrants", "New Entrants"],
              ["movers", "Top Movers"],
              ["cross", "Cross-Category"],
            ] as [Tab, string][]
          ).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`relative px-4 py-2.5 text-sm font-medium transition-colors ${
                tab === key ? "text-amber" : "text-muted hover:text-text"
              }`}
            >
              {label}
              {tab === key && (
                <motion.div
                  layoutId="tab-underline"
                  className="absolute bottom-0 left-0 right-0 h-0.5 bg-amber"
                />
              )}
            </button>
          ))}
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={tab}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.2 }}
          >
            {tab === "entrants" && <EntrantsTable rows={digest.new_entrants} />}
            {tab === "movers" && <MoversTable rows={digest.top_movers} />}
            {tab === "cross" && <CrossTable rows={digest.cross_category} />}
          </motion.div>
        </AnimatePresence>
      </div>

      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Browse by category</h2>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm outline-none focus:border-amber/50"
          >
            {CATEGORIES.map((c) => (
              <option key={c} value={c} className="bg-bg-elevated">
                {c}
              </option>
            ))}
          </select>
        </div>

        {!loading && chartData.length > 0 && (
          <div className="glass-panel p-5 mb-5 h-64">
            <div className="text-xs uppercase tracking-wide text-muted mb-3">
              Review count by rank (entrenchment — higher bars = tougher to
              unseat)
            </div>
            <ResponsiveContainer width="100%" height="85%">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="rank" stroke="#8b93a7" fontSize={11} />
                <YAxis stroke="#8b93a7" fontSize={11} />
                <Tooltip
                  contentStyle={{
                    background: "#0e1017",
                    border: "1px solid rgba(255,255,255,0.1)",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                />
                <Bar dataKey="reviews" fill="#f5a623" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        <ProductTable rows={table} loading={loading} />
      </div>
    </div>
  );
}

function EntrantsTable({ rows }: { rows: SnapshotRow[] }) {
  if (!rows.length) return <Empty text="No new entrants recorded yet." />;
  return <ProductTable rows={rows} showCategory />;
}

function MoversTable({
  rows,
}: {
  rows: Digest["top_movers"];
}) {
  if (!rows.length)
    return (
      <Empty text="No movers yet — needs 2+ collection runs per ASIN." />
    );
  return (
    <div className="glass-panel overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-muted text-xs uppercase border-b border-white/8">
            <th className="px-4 py-3">Product</th>
            <th className="px-4 py-3">Category</th>
            <th className="px-4 py-3">First rank</th>
            <th className="px-4 py-3">Latest rank</th>
            <th className="px-4 py-3">Δ</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.asin} className="border-b border-white/5 last:border-0">
              <td className="px-4 py-3 max-w-md truncate" title={r.title}>
                {r.title}
              </td>
              <td className="px-4 py-3 text-muted">{r.category}</td>
              <td className="px-4 py-3">#{r.first_rank}</td>
              <td className="px-4 py-3">#{r.latest_rank}</td>
              <td className="px-4 py-3 text-green font-semibold">
                +{r.delta}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CrossTable({ rows }: { rows: Digest["cross_category"] }) {
  if (!rows.length)
    return <Empty text="No cross-category hits found yet." />;
  return (
    <div className="glass-panel overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-muted text-xs uppercase border-b border-white/8">
            <th className="px-4 py-3">Product</th>
            <th className="px-4 py-3">Categories</th>
            <th className="px-4 py-3"># Categories</th>
            <th className="px-4 py-3">Best rank</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.asin} className="border-b border-white/5 last:border-0">
              <td className="px-4 py-3 max-w-md truncate" title={r.title}>
                {r.title}
              </td>
              <td className="px-4 py-3 text-muted">{r.categories}</td>
              <td className="px-4 py-3">{r.num_categories}</td>
              <td className="px-4 py-3">#{r.best_rank}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ProductTable({
  rows,
  loading,
  showCategory,
}: {
  rows: SnapshotRow[];
  loading?: boolean;
  showCategory?: boolean;
}) {
  if (loading) {
    return (
      <div className="glass-panel p-8 text-center text-muted text-sm">
        Loading…
      </div>
    );
  }
  if (!rows.length) return <Empty text="No snapshot data for this category yet." />;

  return (
    <div className="glass-panel overflow-hidden overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-muted text-xs uppercase border-b border-white/8">
            <th className="px-4 py-3">Rank</th>
            <th className="px-4 py-3">Product</th>
            {showCategory && <th className="px-4 py-3">Category</th>}
            <th className="px-4 py-3">Price</th>
            <th className="px-4 py-3">Rating</th>
            <th className="px-4 py-3">Reviews</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((p) => (
            <tr key={p.asin} className="border-b border-white/5 last:border-0">
              <td className="px-4 py-3 text-muted">#{p.rank}</td>
              <td className="px-4 py-3 max-w-sm truncate" title={p.title ?? ""}>
                {p.title}
              </td>
              {showCategory && (
                <td className="px-4 py-3 text-muted">
                  {(p as SnapshotRow & { category?: string }).category}
                </td>
              )}
              <td className="px-4 py-3">
                {p.price != null ? `₹${p.price.toLocaleString("en-IN")}` : "—"}
              </td>
              <td className="px-4 py-3">{p.rating ?? "—"} ⭐</td>
              <td className="px-4 py-3">
                {p.review_count?.toLocaleString("en-IN") ?? "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Empty({ text }: { text: string }) {
  return (
    <div className="glass-panel p-8 text-center text-muted text-sm">
      {text}
    </div>
  );
}
