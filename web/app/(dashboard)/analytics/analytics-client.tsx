"use client";

import { useMemo } from "react";
import StatCard from "@/components/StatCard";
import { Card, ChartCard, EmptyState, Table, type Column } from "@/components/ui";
import VerdictBadge from "@/components/VerdictBadge";
import type { Validation } from "@/lib/api";

export default function AnalyticsClient({
  validations,
}: {
  validations: Validation[];
}) {
  const stats = useMemo(() => {
    const total = validations.length;
    const uniqueAsins = new Set(validations.map((v) => v.asin)).size;
    const avgScore = total
      ? validations.reduce((sum, v) => sum + v.score, 0) / total
      : 0;

    const verdictCounts: Record<string, number> = {};
    for (const v of validations) {
      verdictCounts[v.verdict] = (verdictCounts[v.verdict] ?? 0) + 1;
    }
    const verdictData = ["PURSUE", "WATCH", "SKIP"]
      .filter((v) => verdictCounts[v])
      .map((v) => ({ verdict: v, count: verdictCounts[v] }));

    const categoryAgg: Record<string, { total: number; sum: number }> = {};
    for (const v of validations) {
      const cat = v.category ?? "Unknown";
      categoryAgg[cat] ??= { total: 0, sum: 0 };
      categoryAgg[cat].total += 1;
      categoryAgg[cat].sum += v.score;
    }
    const categoryData = Object.entries(categoryAgg)
      .map(([category, { total, sum }]) => ({
        category,
        checked: total,
        avgScore: Math.round((sum / total) * 10) / 10,
      }))
      .sort((a, b) => b.checked - a.checked)
      .slice(0, 10);

    const topCandidates = [...validations]
      .sort((a, b) => b.score - a.score)
      .slice(0, 10);

    return { total, uniqueAsins, avgScore, verdictData, categoryData, topCandidates };
  }, [validations]);

  if (!validations.length) {
    return (
      <EmptyState text="No validations logged yet — run the Validator on a few ASINs first, then come back here for the patterns." />
    );
  }

  const columns: Column<Validation>[] = [
    { key: "score", header: "Score", render: (v) => v.score, cellClassName: "font-semibold text-amber" },
    { key: "verdict", header: "Verdict", render: (v) => <VerdictBadge verdict={v.verdict} /> },
    {
      key: "title",
      header: "Product",
      render: (v) => (
        <span className="max-w-sm truncate block" title={v.title ?? ""}>
          {v.title ?? v.asin}
        </span>
      ),
    },
    { key: "category", header: "Category", render: (v) => v.category ?? "—", cellClassName: "text-muted" },
  ];

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <StatCard label="Total validations" value={stats.total} delay={0} />
        <StatCard label="Unique products" value={stats.uniqueAsins} delay={0.05} />
        <StatCard label="Average score" value={stats.avgScore.toFixed(1)} delay={0.1} />
        <StatCard
          label="PURSUE candidates"
          value={stats.verdictData.find((d) => d.verdict === "PURSUE")?.count ?? 0}
          delay={0.15}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <ChartCard
          title="Verdict breakdown"
          data={stats.verdictData}
          xKey="verdict"
          dataKey="count"
        />
        <ChartCard
          title="Times checked by category (top 10)"
          data={stats.categoryData}
          xKey="category"
          dataKey="checked"
        />
      </div>

      <div>
        <h2 className="text-lg font-semibold mb-4">Top-scoring candidates</h2>
        <Table columns={columns} rows={stats.topCandidates} rowKey={(v) => v.id} />
      </div>

      {stats.categoryData.length > 0 && (
        <Card>
          <h2 className="text-lg font-semibold mb-4">Average score by category</h2>
          <div className="space-y-2">
            {stats.categoryData
              .slice()
              .sort((a, b) => b.avgScore - a.avgScore)
              .map((c) => (
                <div key={c.category} className="flex items-center gap-3">
                  <span className="w-40 shrink-0 text-sm text-muted truncate">{c.category}</span>
                  <div className="flex-1 h-2 rounded-full bg-white/5 overflow-hidden">
                    <div
                      className="h-full bg-amber rounded-full"
                      style={{ width: `${Math.min(100, c.avgScore)}%` }}
                    />
                  </div>
                  <span className="w-12 text-right text-sm font-semibold text-amber">
                    {c.avgScore}
                  </span>
                </div>
              ))}
          </div>
        </Card>
      )}
    </div>
  );
}
