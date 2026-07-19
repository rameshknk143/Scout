"use client";

import { useState, useTransition, useMemo } from "react";
import { Table, Select, EmptyState } from "@/components/ui";
import { gatherKeywords } from "@/lib/actions";

interface KeywordResult {
  keyword: string;
  relevancy: number;
  intent: "HIGH" | "MEDIUM" | "LOW";
  occurrences: number;
}

export default function KeywordsClient() {
  const [seed, setSeed] = useState("");
  const [results, setResults] = useState<KeywordResult[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [intentFilter, setIntentFilter] = useState("all");
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const handleHarvest = (e: React.FormEvent) => {
    e.preventDefault();
    if (!seed.trim()) return;

    startTransition(async () => {
      try {
        setError(null);
        const keywords = await gatherKeywords(seed);
        setResults(keywords);
      } catch (err: any) {
        setError(err?.message || "Failed to harvest suggestions keyword list.");
        setResults([]);
      }
    });
  };

  // Filter suggestion results
  const filteredResults = useMemo(() => {
    return results.filter((item) => {
      const matchesSearch = item.keyword.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesIntent = intentFilter === "all" || item.intent === intentFilter;
      return matchesSearch && matchesIntent;
    });
  }, [results, searchQuery, intentFilter]);

  return (
    <div className="space-y-6">
      {/* Search Harvester Card Form */}
      <form onSubmit={handleHarvest} className="glass-panel p-6 bg-white border border-black/5 space-y-4">
        <div>
          <label className="block text-xs font-bold text-zinc-400 uppercase tracking-wider mb-1.5">
            Seed Keyword
          </label>
          <div className="flex gap-3">
            <input
              type="text"
              value={seed}
              onChange={(e) => setSeed(e.target.value)}
              placeholder="e.g. phone case, organic tea, wireless charger"
              required
              className="input text-white"
            />
            <button
              type="submit"
              disabled={isPending}
              className="btn-primary w-auto whitespace-nowrap px-6 py-2 cursor-pointer disabled:opacity-50"
            >
              {isPending ? "Harvesting Suggestions..." : "🔍 Harvest Keywords"}
            </button>
          </div>
          <p className="text-[10px] text-zinc-500 font-semibold mt-2">
            * ScoutVeda runs 27 recursive queries (base query + letters a-z) in parallel to harvest deep suggestions.
          </p>
        </div>
      </form>

      {error && (
        <div className="p-4 border border-red-500/20 rounded-xl bg-red-500/10 text-red-400 text-xs font-semibold animate-in fade-in duration-200 animate-pulse">
          ⚠️ {error}
        </div>
      )}

      {results.length > 0 && (
        <div className="space-y-4 animate-in fade-in duration-200">
          {/* Results Filters & Toolbar */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 bg-[#111625] p-4 rounded-xl border border-white/5 shadow-sm">
            <div className="flex items-center gap-3 flex-1 max-w-sm">
              <input
                type="text"
                placeholder="Filter suggestions list..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="input py-1.5 text-xs text-white"
              />
            </div>

            <div className="flex flex-wrap gap-2.5">
              {/* Intent Filter */}
              <select
                value={intentFilter}
                onChange={(e) => setIntentFilter(e.target.value)}
                className="text-xs font-semibold text-zinc-300 bg-[#181d2c] border border-white/10 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-zinc-500 cursor-pointer"
              >
                <option value="all">All Intent Types</option>
                <option value="HIGH">🔥 High Intent (Long-tail)</option>
                <option value="MEDIUM">⚡ Medium Intent (Phrase)</option>
                <option value="LOW">🏷️ Low Intent (Short-tail)</option>
              </select>

              <button
                onClick={() => {
                  const csvContent = "data:text/csv;charset=utf-8," 
                    + ["Keyword,Relevancy Score,Search Intent,Hits Count"].join(",") + "\n"
                    + results.map(r => `"${r.keyword}",${r.relevancy},"${r.intent}",${r.occurrences}`).join("\n");
                  const encodedUri = encodeURI(csvContent);
                  const link = document.createElement("a");
                  link.setAttribute("href", encodedUri);
                  link.setAttribute("download", `scoutveda_keywords_${seed.trim().replace(/\s+/g, "_")}.csv`);
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

          {/* Results Suggestions Table */}
          <div className="bg-transparent overflow-hidden">
            <Table
              columns={[
                {
                  key: "rank",
                  header: "Rank",
                  cellClassName: "text-zinc-500 font-mono text-xs font-bold w-12",
                  render: (row, idx) => `#${(idx ?? 0) + 1}`,
                },
                {
                  key: "keyword",
                  header: "Keyword Suggestion",
                  cellClassName: "text-white font-bold text-xs",
                  render: (row) => row.keyword,
                },
                {
                  key: "relevancy",
                  header: "Search Relevancy",
                  render: (row) => (
                    <div className="flex items-center gap-3 w-40">
                      <div className="flex-1 h-1.5 bg-[#181d2c] rounded-full overflow-hidden border border-white/5">
                        <div
                          style={{ width: `${row.relevancy}%` }}
                          className={`h-full rounded-full ${
                            row.relevancy >= 70
                              ? "bg-emerald-500"
                              : row.relevancy >= 40
                              ? "bg-amber-500"
                              : "bg-zinc-600"
                          }`}
                        />
                      </div>
                      <span className="text-[11px] font-bold text-zinc-300 w-8 text-right font-mono">
                        {row.relevancy}%
                      </span>
                    </div>
                  ),
                },
                {
                  key: "intent",
                  header: "Search Intent",
                  render: (row) => (
                    <span className={`text-[9px] font-bold tracking-wider px-2 py-0.5 rounded border ${
                      row.intent === "HIGH"
                        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                        : row.intent === "MEDIUM"
                        ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                        : "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                    }`}>
                      {row.intent} INTENT
                    </span>
                  ),
                },
                {
                  key: "occurrences",
                  header: "Search Loop Hits",
                  cellClassName: "text-zinc-400 font-bold text-xs text-center w-24 font-mono",
                  render: (row) => `${row.occurrences} / 27`,
                },
                {
                  key: "action",
                  header: "Action",
                  render: (row) => (
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(row.keyword);
                      }}
                      className="text-[10px] font-bold text-zinc-300 bg-[#181d2c] border border-white/10 hover:bg-white/5 px-2 py-1 rounded transition-colors cursor-pointer"
                    >
                      Copy Term
                    </button>
                  ),
                },
              ]}
              rows={filteredResults}
              rowKey={(row) => row.keyword}
            />
          </div>

          <div className="text-xs font-semibold text-zinc-400 pl-1">
            {filteredResults.length} of {results.length} keyword suggestion matches shown.
          </div>
        </div>
      )}

      {results.length === 0 && !isPending && (
        <div className="bg-[#111625] p-8 rounded-xl border border-white/5 shadow-sm">
          <EmptyState text="Enter a seed keyword above to query Amazon India suggestions." />
        </div>
      )}
    </div>
  );
}
