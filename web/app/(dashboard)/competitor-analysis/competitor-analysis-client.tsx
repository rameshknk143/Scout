"use client";

import { useState, useTransition } from "react";
import Link from "next/link";
import VerdictBadge from "@/components/VerdictBadge";
import { compareCompetitors } from "@/lib/actions";

type ComparisonItem = {
  asin: string;
  title: string | null;
  price: number | null;
  rank: number | null;
  rating: number | null;
  review_count: number | null;
  score: number;
  verdict: "PURSUE" | "WATCH" | "SKIP";
  found: boolean;
};

export default function CompetitorAnalysisClient() {
  const [asinInputs, setAsinInputs] = useState<string[]>(["", "", ""]);
  const [results, setResults] = useState<ComparisonItem[]>([]);
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  const handleInputChange = (idx: number, val: string) => {
    const updated = [...asinInputs];
    updated[idx] = val;
    setAsinInputs(updated);
  };

  const handleAddInput = () => {
    if (asinInputs.length < 5) {
      setAsinInputs([...asinInputs, ""]);
    }
  };

  const handleRemoveInput = (idx: number) => {
    if (asinInputs.length > 2) {
      const updated = asinInputs.filter((_, i) => i !== idx);
      setAsinInputs(updated);
    }
  };

  const handleCompare = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const activeAsins = asinInputs.map((a) => a.trim()).filter((a) => a.length > 0);
    if (activeAsins.length === 0) {
      setError("Please input at least one ASIN to compare.");
      return;
    }

    startTransition(async () => {
      try {
        const res = await compareCompetitors(activeAsins);
        setResults(res.comparisons);
      } catch (err) {
        setError("Failed to fetch competitor comparisons. Verify your database connection.");
      }
    });
  };

  const hasResults = results.length > 0;

  return (
    <div className="space-y-6">
      {/* Input panel */}
      <form onSubmit={handleCompare} className="glass-panel p-5 bg-white space-y-4">
        <div className="text-sm font-semibold text-zinc-950 mb-1">Enter Competitor ASINs</div>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          {asinInputs.map((input, idx) => (
            <div key={idx} className="relative space-y-1">
              <div className="flex items-center justify-between">
                <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider">
                  ASIN {idx + 1}
                </label>
                {asinInputs.length > 2 && (
                  <button
                    type="button"
                    onClick={() => handleRemoveInput(idx)}
                    className="text-[9px] font-bold text-zinc-400 hover:text-red-700 transition-colors"
                  >
                    Remove
                  </button>
                )}
              </div>
              <input
                type="text"
                value={input}
                onChange={(e) => handleInputChange(idx, e.target.value)}
                placeholder="e.g. B0D4DZ7WL2"
                className="input font-mono text-xs uppercase"
              />
            </div>
          ))}
        </div>

        <div className="flex items-center justify-between pt-2">
          {asinInputs.length < 5 ? (
            <button
              type="button"
              onClick={handleAddInput}
              className="text-xs font-bold text-zinc-700 bg-white border border-zinc-200 px-3 py-2 rounded-lg hover:bg-zinc-50 cursor-pointer shadow-sm transition-colors"
            >
              + Add ASIN Slot ({5 - asinInputs.length} remaining)
            </button>
          ) : (
            <div />
          )}

          <button
            type="submit"
            disabled={isPending}
            className="btn-primary w-auto text-xs py-2 disabled:opacity-50"
          >
            {isPending ? "Comparing ASINs..." : "Compare side-by-side"}
          </button>
        </div>

        {error && <div className="text-xs text-red-700 font-semibold">{error}</div>}
      </form>

      {/* Comparison Grid Matrix */}
      {hasResults && (
        <div className="bg-white border border-zinc-200/80 rounded-xl shadow-sm overflow-x-auto">
          {isPending ? (
            <div className="flex flex-col items-center justify-center py-24 space-y-3">
              <div className="w-6 h-6 border-2 border-zinc-950 border-t-transparent rounded-full animate-spin"></div>
              <div className="text-xs text-zinc-400 font-semibold">Updating comparison matrix...</div>
            </div>
          ) : (
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-zinc-50/70 border-b border-zinc-200/80">
                  <th className="p-4 font-bold text-zinc-500 uppercase tracking-wider w-1/5">Niche Metric</th>
                  {results.map((r, i) => (
                    <th key={i} className="p-4 font-bold text-zinc-900 border-l border-zinc-200/60 w-1/5">
                      <span className="font-mono text-xs text-zinc-900 bg-zinc-100/70 px-1.5 py-0.5 rounded border border-zinc-200/50">
                        {r.asin}
                      </span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-200/60 font-semibold text-zinc-800">
                {/* Title */}
                <tr>
                  <td className="p-4 text-[10px] text-zinc-400 font-bold uppercase tracking-wider bg-zinc-50/20">Title</td>
                  {results.map((r, i) => (
                    <td key={i} className="p-4 border-l border-zinc-200/60 align-top text-zinc-900 text-xs leading-normal">
                      {r.found ? (
                        <span className="line-clamp-3" title={r.title || ""}>
                          {r.title || "(no title found)"}
                        </span>
                      ) : (
                        <span className="text-zinc-400 font-medium">ASIN not in database</span>
                      )}
                    </td>
                  ))}
                </tr>

                {/* Price */}
                <tr>
                  <td className="p-4 text-[10px] text-zinc-400 font-bold uppercase tracking-wider bg-zinc-50/20">Buy Box Price</td>
                  {results.map((r, i) => (
                    <td key={i} className="p-4 border-l border-zinc-200/60 text-zinc-950 font-bold text-sm">
                      {r.found && r.price != null ? `₹${r.price.toLocaleString("en-IN")}` : "—"}
                    </td>
                  ))}
                </tr>

                {/* BSR */}
                <tr>
                  <td className="p-4 text-[10px] text-zinc-400 font-bold uppercase tracking-wider bg-zinc-50/20">BSR Rank</td>
                  {results.map((r, i) => (
                    <td key={i} className="p-4 border-l border-zinc-200/60 font-bold">
                      {r.found && r.rank != null ? `#${r.rank.toLocaleString("en-IN")}` : "—"}
                    </td>
                  ))}
                </tr>

                {/* Reviews */}
                <tr>
                  <td className="p-4 text-[10px] text-zinc-400 font-bold uppercase tracking-wider bg-zinc-50/20">Reviews</td>
                  {results.map((r, i) => (
                    <td key={i} className="p-4 border-l border-zinc-200/60">
                      {r.found && r.review_count != null ? (
                        <div className="flex items-center gap-1.5">
                          <span>{r.review_count.toLocaleString("en-IN")}</span>
                          {r.rating != null && (
                            <span className="text-[10px] bg-amber-50 text-amber-800 border border-amber-100 rounded px-1.5 py-0.5">
                              {r.rating} ⭐
                            </span>
                          )}
                        </div>
                      ) : (
                        "—"
                      )}
                    </td>
                  ))}
                </tr>

                {/* Opportunity Score */}
                <tr>
                  <td className="p-4 text-[10px] text-zinc-400 font-bold uppercase tracking-wider bg-zinc-50/20">Opportunity Score</td>
                  {results.map((r, i) => (
                    <td key={i} className="p-4 border-l border-zinc-200/60 font-black text-lg text-zinc-950">
                      {r.found ? `${r.score} / 100` : "—"}
                    </td>
                  ))}
                </tr>

                {/* Verdict */}
                <tr>
                  <td className="p-4 text-[10px] text-zinc-400 font-bold uppercase tracking-wider bg-zinc-50/20">Verdict</td>
                  {results.map((r, i) => (
                    <td key={i} className="p-4 border-l border-zinc-200/60">
                      {r.found ? <VerdictBadge verdict={r.verdict} /> : "—"}
                    </td>
                  ))}
                </tr>

                {/* Actions */}
                <tr>
                  <td className="p-4 text-[10px] text-zinc-400 font-bold uppercase tracking-wider bg-zinc-50/20">Quick Actions</td>
                  {results.map((r, i) => (
                    <td key={i} className="p-4 border-l border-zinc-200/60">
                      {r.found ? (
                        <div className="flex flex-col gap-1.5">
                          <Link
                            href={`/validator?asin=${r.asin}`}
                            className="text-[10px] font-bold text-center text-zinc-950 bg-zinc-100 hover:bg-zinc-200 px-2 py-1 rounded transition-colors border border-zinc-200/40"
                          >
                            Re-Validate Cost
                          </Link>
                          <Link
                            href={`/listing?asin=${r.asin}`}
                            className="text-[10px] font-bold text-center text-zinc-700 bg-white hover:bg-zinc-50 px-2 py-1 rounded transition-colors border border-zinc-200"
                          >
                            Analyze Copy
                          </Link>
                        </div>
                      ) : (
                        <Link
                          href={`/validator?asin=${r.asin}`}
                          className="text-[10px] font-bold text-center text-white bg-zinc-900 hover:bg-zinc-950 px-2.5 py-1 rounded transition-colors shadow-sm block"
                        >
                          Scout ASIN
                        </Link>
                      )}
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
