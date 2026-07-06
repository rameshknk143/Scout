"use client";

import { useMemo, useState } from "react";
import VerdictBadge from "@/components/VerdictBadge";
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
    return (
      <div className="glass-panel p-8 text-center text-muted text-sm">
        No validations logged yet — run the Validator first.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3">
        <select
          value={verdictFilter}
          onChange={(e) => setVerdictFilter(e.target.value)}
          className="input w-auto"
        >
          <option value="" className="bg-bg-elevated">All verdicts</option>
          {verdicts.map((v) => (
            <option key={v} value={v} className="bg-bg-elevated">
              {v}
            </option>
          ))}
        </select>
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="input w-auto"
        >
          <option value="" className="bg-bg-elevated">All categories</option>
          {categories.map((c) => (
            <option key={c} value={c} className="bg-bg-elevated">
              {c}
            </option>
          ))}
        </select>
      </div>

      <div className="glass-panel overflow-hidden overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-muted text-xs uppercase border-b border-white/8">
              <th className="px-4 py-3">Score</th>
              <th className="px-4 py-3">Verdict</th>
              <th className="px-4 py-3">Product</th>
              <th className="px-4 py-3">Category</th>
              <th className="px-4 py-3">Buy price</th>
              <th className="px-4 py-3">Validated</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((v) => (
              <tr key={v.id} className="border-b border-white/5 last:border-0">
                <td className="px-4 py-3 font-semibold text-amber">{v.score}</td>
                <td className="px-4 py-3">
                  <VerdictBadge verdict={v.verdict} />
                </td>
                <td className="px-4 py-3 max-w-sm truncate" title={v.title ?? ""}>
                  {v.title ?? v.asin}
                </td>
                <td className="px-4 py-3 text-muted">{v.category ?? "—"}</td>
                <td className="px-4 py-3">₹{v.buy_price.toLocaleString("en-IN")}</td>
                <td className="px-4 py-3 text-muted text-xs">
                  {new Date(v.validated_at).toLocaleString("en-IN", {
                    dateStyle: "medium",
                    timeStyle: "short",
                  })}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="text-xs text-muted">
        {filtered.length} of {validations.length} validations shown.
      </div>
    </div>
  );
}
