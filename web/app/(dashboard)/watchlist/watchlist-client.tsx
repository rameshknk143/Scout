"use client";

import { useMemo, useState } from "react";
import VerdictBadge from "@/components/VerdictBadge";
import { Table, Select, EmptyState, type Column } from "@/components/ui";
import type { Validation } from "@/lib/api";

export default function WatchlistClient({
  validations,
}: {
  validations: Validation[];
}) {
  const [verdictFilter, setVerdictFilter] = useState<string>("");
  const [categoryFilter, setCategoryFilter] = useState<string>("");

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

  const filtered = validations.filter(
    (v) =>
      (!verdictFilter || v.verdict === verdictFilter) &&
      (!categoryFilter || v.category === categoryFilter)
  );

  if (!validations.length) {
    return <EmptyState text="No validations logged yet — run the Validator first." />;
  }

  const columns: Column<Validation>[] = [
    {
      key: "score",
      header: "Score",
      render: (v) => v.score,
      cellClassName: "font-semibold text-amber",
    },
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
    { key: "buy_price", header: "Buy price", render: (v) => `₹${v.buy_price.toLocaleString("en-IN")}` },
    {
      key: "validated_at",
      header: "Validated",
      render: (v) =>
        new Date(v.validated_at).toLocaleString("en-IN", {
          dateStyle: "medium",
          timeStyle: "short",
        }),
      cellClassName: "text-muted text-xs",
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3">
        <Select
          value={verdictFilter}
          onChange={setVerdictFilter}
          placeholder="All verdicts"
          options={verdicts.map((v) => ({ value: v, label: v }))}
        />
        <Select
          value={categoryFilter}
          onChange={setCategoryFilter}
          placeholder="All categories"
          options={categories.map((c) => ({ value: c, label: c }))}
        />
      </div>

      <Table columns={columns} rows={filtered} rowKey={(v) => v.id} />

      <div className="text-xs text-muted">
        {filtered.length} of {validations.length} validations shown.
      </div>
    </div>
  );
}
