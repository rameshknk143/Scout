"use client";

import { useMemo } from "react";
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
    { 
      key: "score", 
      header: "Score", 
      render: (v) => v.score, 
      cellClassName: "font-mono font-bold text-text" 
    },
    { 
      key: "verdict", 
      header: "Verdict", 
      render: (v) => <VerdictBadge verdict={v.verdict} /> 
    },
    {
      key: "title",
      header: "Product",
      render: (v) => (
        <span className="max-w-sm truncate block font-medium" title={v.title ?? ""}>
          {v.title ?? v.asin}
        </span>
      ),
    },
    { 
      key: "category", 
      header: "Category", 
      render: (v) => v.category ?? "—", 
      cellClassName: "text-muted font-medium" 
    },
  ];

  return (
    <div className="space-y-10">
      {/* Top Header Block */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between border-b border-white/5 pb-6">
        <div>
          <h1 className="text-3xl font-extrabold text-text tracking-tight">Analytics</h1>
          <p className="text-sm text-muted mt-1.5">Aggregate insights and historical patterns across logged validations.</p>
        </div>
      </div>

      {/* Cohesive Stat Grid (Apple-style divide list) */}
      <div className="grid grid-cols-2 md:grid-cols-4 border border-white/5 rounded-xl overflow-hidden divide-x divide-y md:divide-y-0 divide-white/5 bg-white/[0.01] shadow-sm">
        <div className="p-6">
          <p className="text-[10px] uppercase tracking-wider text-muted font-bold">Total Validations</p>
          <p className="text-3xl font-extrabold text-text mt-2.5 tracking-tight">{stats.total}</p>
        </div>
        <div className="p-6">
          <p className="text-[10px] uppercase tracking-wider text-muted font-bold">Unique Products</p>
          <p className="text-3xl font-extrabold text-text mt-2.5 tracking-tight">{stats.uniqueAsins}</p>
        </div>
        <div className="p-6">
          <p className="text-[10px] uppercase tracking-wider text-muted font-bold">Average Score</p>
          <p className="text-3xl font-extrabold text-text mt-2.5 tracking-tight">{stats.avgScore.toFixed(1)}</p>
        </div>
        <div className="p-6">
          <p className="text-[10px] uppercase tracking-wider text-muted font-bold">Pursue Candidates</p>
          <p className="text-3xl font-extrabold text-text mt-2.5 tracking-tight">
            {stats.verdictData.find((d) => d.verdict === "PURSUE")?.count ?? 0}
          </p>
        </div>
      </div>

      {/* Grid for breakdown and top-category charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
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

      {/* Top candidates list */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold tracking-tight text-text">Top-scoring candidates</h2>
        <Table columns={columns} rows={stats.topCandidates} rowKey={(v) => v.id} />
      </div>

      {/* Average score by category slider block */}
      {stats.categoryData.length > 0 && (
        <Card className="p-6">
          <h2 className="text-lg font-bold tracking-tight text-text mb-6">Average score by category</h2>
          <div className="space-y-4">
            {stats.categoryData
              .slice()
              .sort((a, b) => b.avgScore - a.avgScore)
              .map((c) => (
                <div key={c.category} className="flex items-center gap-4">
                  <span className="w-44 shrink-0 text-xs font-semibold text-muted truncate">{c.category}</span>
                  <div className="flex-1 h-1.5 rounded-full bg-white/5 overflow-hidden">
                    <div
                      className="h-full bg-text rounded-full"
                      style={{ width: `${Math.min(100, c.avgScore)}%` }}
                    />
                  </div>
                  <span className="w-12 text-right text-xs font-bold text-text font-mono">
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
