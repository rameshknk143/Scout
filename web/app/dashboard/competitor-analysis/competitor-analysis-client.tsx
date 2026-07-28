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
      <form onSubmit={handleCompare} className="glass-panel p-5 bg-white border border-black/5 space-y-4">
        <div className="text-sm font-semibold text-zinc-900 mb-1">Enter Competitor ASINs</div>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          {asinInputs.map((input, idx) => (
            <div key={idx} className="relative space-y-1">
              <div className="flex items-center justify-between">
                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">
                  ASIN {idx + 1}
                </label>
                {asinInputs.length > 2 && (
                  <button
                    type="button"
                    onClick={() => handleRemoveInput(idx)}
                    className="text-[9px] font-bold text-zinc-500 hover:text-red-400 transition-colors"
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
              className="text-xs font-bold text-zinc-300 bg-[#181d2c] border border-white/10 px-3 py-2 rounded-lg hover:bg-white/5 cursor-pointer shadow-sm transition-colors"
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

        {error && <div className="text-xs text-red-400 font-semibold">{error}</div>}
      </form>

      {/* Comparison Grid Matrix */}
      {hasResults && (
        <div className="bg-[#111625]/20 border border-white/5 rounded-xl shadow-sm overflow-x-auto">
          {isPending ? (
            <div className="flex flex-col items-center justify-center py-24 space-y-3">
              <div className="w-6 h-6 border-2 border-zinc-900 border-t-transparent rounded-full animate-spin"></div>
              <div className="text-xs text-zinc-500 font-semibold">Updating comparison matrix...</div>
            </div>
          ) : (
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-[#181d2c]/50 border-b border-white/5">
                  <th className="p-4 font-bold text-zinc-400 uppercase tracking-wider w-1/5">Niche Metric</th>
                  {results.map((r, i) => (
                    <th key={i} className="p-4 font-bold text-zinc-900 border-l border-black/5 w-1/5">
                      <span className="font-mono text-xs text-zinc-300 bg-[#181d2c] px-1.5 py-0.5 rounded border border-white/5">
                        {r.asin}
                      </span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 font-semibold text-zinc-300">
                {/* Title */}
                <tr>
                  <td className="p-4 text-[10px] text-zinc-500 font-bold uppercase tracking-wider bg-transparent">Title</td>
                  {results.map((r, i) => (
                    <td key={i} className="p-4 border-l border-black/5 align-top text-zinc-900 text-xs leading-normal font-sans">
                      {r.found ? (
                        <span className="line-clamp-3" title={r.title || ""}>
                          {r.title || "(no title found)"}
                        </span>
                      ) : (
                        <span className="text-zinc-500 font-medium">ASIN not in database</span>
                      )}
                    </td>
                  ))}
                </tr>

                {/* Price */}
                <tr>
                  <td className="p-4 text-[10px] text-zinc-500 font-bold uppercase tracking-wider bg-transparent">Buy Box Price</td>
                  {results.map((r, i) => (
                    <td key={i} className="p-4 border-l border-black/5 text-zinc-900 font-bold text-sm font-mono">
                      {r.found && r.price != null ? `₹${r.price.toLocaleString("en-IN")}` : "—"}
                    </td>
                  ))}
                </tr>

                {/* BSR */}
                <tr>
                  <td className="p-4 text-[10px] text-zinc-500 font-bold uppercase tracking-wider bg-transparent">BSR Rank</td>
                  {results.map((r, i) => (
                    <td key={i} className="p-4 border-l border-black/5 font-bold font-mono text-zinc-900">
                      {r.found && r.rank != null ? `#${r.rank.toLocaleString("en-IN")}` : "—"}
                    </td>
                  ))}
                </tr>

                {/* Reviews */}
                <tr>
                  <td className="p-4 text-[10px] text-zinc-500 font-bold uppercase tracking-wider bg-transparent">Reviews</td>
                  {results.map((r, i) => (
                    <td key={i} className="p-4 border-l border-black/5 font-mono text-zinc-900">
                      {r.found && r.review_count != null ? (
                        <div className="flex items-center gap-1.5">
                          <span>{r.review_count.toLocaleString("en-IN")}</span>
                          {r.rating != null && (
                            <span className="text-[10px] bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded px-1.5 py-0.5 font-bold">
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
                  <td className="p-4 text-[10px] text-zinc-500 font-bold uppercase tracking-wider bg-transparent">Opportunity Score</td>
                  {results.map((r, i) => (
                    <td key={i} className="p-4 border-l border-black/5 font-black text-lg text-zinc-900 font-mono">
                      {r.found ? `${r.score} / 100` : "—"}
                    </td>
                  ))}
                </tr>

                {/* Verdict */}
                <tr>
                  <td className="p-4 text-[10px] text-zinc-500 font-bold uppercase tracking-wider bg-transparent">Verdict</td>
                  {results.map((r, i) => (
                    <td key={i} className="p-4 border-l border-black/5">
                      {r.found ? <VerdictBadge verdict={r.verdict} /> : "—"}
                    </td>
                  ))}
                </tr>

                {/* Actions */}
                <tr>
                  <td className="p-4 text-[10px] text-zinc-500 font-bold uppercase tracking-wider bg-transparent">Quick Actions</td>
                  {results.map((r, i) => (
                    <td key={i} className="p-4 border-l border-black/5">
                      {r.found ? (
                        <div className="flex flex-col gap-1.5">
                          <Link
                             href={`/dashboard/validator?asin=${r.asin}`}
                             className="text-[10px] font-bold text-center text-zinc-300 bg-[#181d2c] border border-white/10 hover:bg-white/5 px-2 py-1 rounded transition-colors"
                          >
                            Re-Validate Cost
                          </Link>
                          <Link
                            href={`/dashboard/listing?asin=${r.asin}`}
                            className="text-[10px] font-bold text-center text-zinc-400 bg-transparent hover:text-zinc-900 px-2 py-1 rounded transition-colors border border-black/10"
                          >
                            Analyze Copy
                          </Link>
                        </div>
                      ) : (
                        <Link
                          href={`/dashboard/validator?asin=${r.asin}`}
                          className="btn-primary text-center block text-[10px] py-1"
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
