"use client";

import { useState, useTransition, useMemo } from "react";
import CaveatBox from "@/components/CaveatBox";
import { Card, Field, MiniStat, Table, type Column } from "@/components/ui";
import type { ListingAnalysis, ListingPeer, ListingSuggestion, ReviewSummary } from "@/lib/api";
import { CATEGORIES } from "@/lib/constants";
import { analyzeListing, suggestListingImprovements, summarizeReviews } from "@/lib/actions";

function extractDetail(err: unknown, fallback: string): string {
  const raw = err instanceof Error ? err.message : "";
  const match = raw.match(/"detail":"(.*?)"(?:,|\})/);
  return match ? match[1] : fallback;
}

const COMPONENT_LABELS: Record<string, string> = {
  title: "Title",
  bullets: "Bullets",
  images: "Images",
};

export default function ListingClient() {
  const [activeMode, setActiveMode] = useState<"analyze" | "scribbles">("analyze");

  // Scribbles states
  const [keywordInput, setKeywordInput] = useState("phone case\nback cover\npremium\nslim cover\nprotective case");
  const [titleDraft, setTitleDraft] = useState("");
  const [bullet1, setBullet1] = useState("");
  const [bullet2, setBullet2] = useState("");
  const [bullet3, setBullet3] = useState("");
  const [bullet4, setBullet4] = useState("");
  const [bullet5, setBullet5] = useState("");
  const [descriptionDraft, setDescriptionDraft] = useState("");

  const targetKeywords = useMemo(() => {
    return keywordInput
      .split(/[\n,]/)
      .map((k) => k.trim())
      .filter((k) => k.length > 0);
  }, [keywordInput]);

  const usedKeywords = useMemo(() => {
    const used = new Set<string>();
    const combinedText = `${titleDraft} ${bullet1} ${bullet2} ${bullet3} ${bullet4} ${bullet5} ${descriptionDraft}`.toLowerCase();
    targetKeywords.forEach((kw) => {
      if (combinedText.includes(kw.toLowerCase())) {
        used.add(kw.toLowerCase());
      }
    });
    return used;
  }, [targetKeywords, titleDraft, bullet1, bullet2, bullet3, bullet4, bullet5, descriptionDraft]);

  const [asin, setAsin] = useState("");
  const [category, setCategory] = useState("");

  const [result, setResult] = useState<ListingAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const [suggestion, setSuggestion] = useState<ListingSuggestion | null>(null);
  const [suggestError, setSuggestError] = useState<string | null>(null);
  const [isSuggesting, startSuggestTransition] = useTransition();

  const [reviewSummary, setReviewSummary] = useState<ReviewSummary | null>(null);
  const [reviewSummaryError, setReviewSummaryError] = useState<string | null>(null);
  const [isSummarizing, startSummarizeTransition] = useTransition();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSuggestion(null);
    setSuggestError(null);
    setReviewSummary(null);
    setReviewSummaryError(null);
    startTransition(async () => {
      try {
        const res = await analyzeListing({ asin: asin.trim(), category: category || undefined });
        setResult(res);
      } catch (err) {
        setError(
          extractDetail(
            err,
            "Couldn't load that listing — check it's a valid ASIN and try again."
          )
        );
      }
    });
  }

  function handleSuggest() {
    if (!result) return;
    setSuggestError(null);
    startSuggestTransition(async () => {
      try {
        const res = await suggestListingImprovements({
          title: result.title,
          bullets: result.bullets,
          category: result.category,
          gaps: result.gaps,
        });
        setSuggestion(res);
      } catch (err) {
        setSuggestError(
          extractDetail(err, "AI suggestions aren't available right now — try again in a moment.")
        );
      }
    });
  }

  function handleSummarizeReviews() {
    if (!result) return;
    setReviewSummaryError(null);
    startSummarizeTransition(async () => {
      try {
        const res = await summarizeReviews(result.reviews);
        setReviewSummary(res);
      } catch (err) {
        setReviewSummaryError(
          extractDetail(err, "Couldn't summarize reviews right now — try again in a moment.")
        );
      }
    });
  }

  return (
    <div className="space-y-6">
      {/* Tabs Switcher */}
      <div className="flex border-b border-white/5">
        <button
          onClick={() => setActiveMode("analyze")}
          className={`px-4 py-2.5 text-xs font-bold uppercase tracking-wider border-b-2 transition-all cursor-pointer ${
            activeMode === "analyze"
              ? "border-white text-white font-extrabold"
              : "border-transparent text-zinc-500 hover:text-zinc-300"
          }`}
        >
          🔍 Live Listing Analyzer
        </button>
        <button
          onClick={() => setActiveMode("scribbles")}
          className={`px-4 py-2.5 text-xs font-bold uppercase tracking-wider border-b-2 transition-all cursor-pointer ${
            activeMode === "scribbles"
              ? "border-white text-white font-extrabold"
              : "border-transparent text-zinc-500 hover:text-zinc-300"
          }`}
        >
          ✨ Scribbles Keyword Sandbox
        </button>
      </div>

      {activeMode === "analyze" && (
        <div className="space-y-6 animate-in fade-in duration-200">
          <form onSubmit={handleSubmit} className="glass-panel p-6 space-y-5 bg-white border border-black/5">
            <div>
              <label className="block text-xs font-bold text-zinc-400 uppercase tracking-wider mb-1.5">Amazon ASIN</label>
              <input
                value={asin}
                onChange={(e) => setAsin(e.target.value)}
                placeholder="B0D4DZ7WL2"
                required
                className="input font-mono text-sm"
              />
            </div>
            <Field label="Category (optional — helps benchmark against peers)">
              <select value={category} onChange={(e) => setCategory(e.target.value)} className="input cursor-pointer">
                <option value="">(auto-detect from ScoutVeda's own data)</option>
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </Field>
            <button
              type="submit"
              disabled={isPending}
              className="btn-primary w-auto disabled:opacity-50"
            >
              {isPending ? "Loading live page…" : "Analyze listing"}
            </button>
          </form>

          {error && (
            <CaveatBox>
              {error}
            </CaveatBox>
          )}

          {result && (
            <Card>
              <div className="flex items-start justify-between gap-4 mb-4">
                <div>
                  <div className="text-xs text-muted mb-1 font-mono">{result.asin}</div>
                  <div className="font-semibold leading-snug text-white">{result.title ?? "(title not found)"}</div>
                  <div className="text-xs text-muted mt-1 font-mono">
                    {result.category ?? "unknown category"}
                    {result.price != null && ` · ₹${result.price.toLocaleString("en-IN")}`}
                    {result.rating != null && ` · ${result.rating} ⭐`}
                    {result.review_count != null && ` · ${result.review_count.toLocaleString("en-IN")} reviews`}
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <div className="text-4xl font-extrabold text-white tracking-tight font-mono">{result.score}</div>
                  <div className="text-xs text-zinc-500 mt-1.5 font-mono">/ 100 Score</div>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3 mb-4">
                {Object.entries(result.components).map(([key, value]) => (
                  <MiniStat
                    key={key}
                    label={COMPONENT_LABELS[key] ?? key}
                    value={
                      <span className="font-mono">
                        {value}
                        <span className="text-zinc-500 text-xs">/100</span>
                      </span>
                    }
                  />
                ))}
              </div>

              {result.gaps.length > 0 && (
                <div className="space-y-2 mb-4">
                  {result.gaps.map((g, i) => (
                    <CaveatBox key={i}>{g}</CaveatBox>
                  ))}
                </div>
              )}

              <div className="pt-3 border-t border-white/5 flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={handleSuggest}
                  disabled={isSuggesting}
                  className="text-xs font-bold text-zinc-300 bg-[#181d2c] border border-white/10 px-3 py-2 rounded-lg hover:bg-white/5 cursor-pointer shadow-sm transition-colors disabled:opacity-50"
                >
                  {isSuggesting ? "Asking the AI…" : "✨ Suggest AI improvements"}
                </button>
                {result.reviews.length > 0 && (
                  <button
                    type="button"
                    onClick={handleSummarizeReviews}
                    disabled={isSummarizing}
                    className="text-xs font-bold text-zinc-300 bg-[#181d2c] border border-white/10 px-3 py-2 rounded-lg hover:bg-white/5 cursor-pointer shadow-sm transition-colors disabled:opacity-50"
                  >
                    {isSummarizing
                      ? "Reading reviews…"
                      : `🔍 Summarize ${result.reviews.length} reviews`}
                  </button>
                )}
              </div>

              <div>
                {suggestError && <div className="text-xs text-red-400 mt-3 font-semibold">{suggestError}</div>}

                {suggestion && (
                  <div className="mt-4 space-y-3">
                    {suggestion.title && (
                      <div>
                        <div className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1">Suggested title</div>
                        <div className="text-xs font-medium text-white bg-[#181d2c] rounded-lg px-3 py-2 border border-white/5">
                          {suggestion.title}
                        </div>
                      </div>
                    )}
                    {suggestion.bullets.length > 0 && (
                      <div>
                        <div className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1">Suggested bullets</div>
                        <ul className="space-y-1.5">
                          {suggestion.bullets.map((b, i) => (
                            <li
                              key={i}
                              className="text-xs font-medium text-white bg-[#181d2c] rounded-lg px-3 py-2 border border-white/5 leading-relaxed"
                            >
                              {b}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    <div className="text-[10px] text-zinc-500 font-semibold font-mono">
                      * AI-generated via a free model router — review before using, not auto-published.
                    </div>
                  </div>
                )}

                {reviewSummaryError && <div className="text-xs text-red-400 mt-3 font-semibold">{reviewSummaryError}</div>}

                {reviewSummary && (
                  <div className="mt-4 space-y-3">
                    {reviewSummary.pros.length > 0 && (
                      <div>
                        <div className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider mb-1">Pros customers mention</div>
                        <ul className="space-y-1.5">
                          {reviewSummary.pros.map((p, i) => (
                            <li
                              key={i}
                              className="text-xs font-medium bg-emerald-500/10 text-emerald-400 rounded-lg px-3 py-2 border border-emerald-500/20"
                            >
                              {p}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {reviewSummary.cons.length > 0 && (
                      <div>
                        <div className="text-[10px] font-bold text-red-400 uppercase tracking-wider mb-1">Cons customers mention</div>
                        <ul className="space-y-1.5">
                          {reviewSummary.cons.map((c, i) => (
                            <li
                              key={i}
                              className="text-xs font-medium bg-red-500/10 text-red-400 rounded-lg px-3 py-2 border border-red-500/20"
                            >
                              {c}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    <div className="text-[10px] text-zinc-500 font-semibold font-mono">
                      * From {result.reviews.length} of Amazon&apos;s own featured reviews on this listing.
                    </div>
                  </div>
                )}
              </div>
            </Card>
          )}

          {result && result.peers.length > 0 && (
            <Card>
              <div className="text-sm font-semibold mb-3 text-white">
                Category peers — top {result.peers.length} in {result.category ?? "this category"}
              </div>
              <Table
                columns={peerColumns}
                rows={result.peers}
                rowKey={(p) => p.asin}
                emptyText="No peer data for this category yet."
              />
              <div className="text-xs text-zinc-500 mt-3 font-semibold font-mono">
                * From ScoutVeda&apos;s own nightly-collected snapshot data — same source as Trend Radar.
              </div>
            </Card>
          )}
        </div>
      )}

      {activeMode === "scribbles" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mt-6 animate-in fade-in duration-200">
          {/* Keyword Bank Panel */}
          <div className="lg:col-span-4 bg-[#111625] border border-white/5 rounded-xl p-5 shadow-sm space-y-5 flex flex-col">
            <div>
              <span className="text-[10px] font-extrabold text-zinc-500 uppercase tracking-wider block mb-1.5">
                Keyword Bank (Enter newlines or commas)
              </span>
              <textarea
                value={keywordInput}
                onChange={(e) => setKeywordInput(e.target.value)}
                placeholder="Paste keywords list..."
                className="w-full h-36 border border-white/10 rounded-lg p-3 text-xs outline-none focus:border-zinc-500 text-white bg-[#181d2c] leading-relaxed font-mono resize-none shadow-inner"
              />
            </div>

            <div className="flex-1 space-y-2.5">
              <span className="text-[10px] font-extrabold text-zinc-500 uppercase tracking-wider block">
                SEO Indexation Checks ({usedKeywords.size} / {targetKeywords.length} Used)
              </span>
              <div className="space-y-1.5 overflow-y-auto max-h-[360px] pr-1">
                {targetKeywords.map((kw, i) => {
                  const isUsed = usedKeywords.has(kw.toLowerCase());
                  return (
                    <div
                      key={i}
                      className={`flex items-center justify-between p-2 rounded border text-xs font-semibold transition-all ${
                        isUsed
                          ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400 line-through decoration-emerald-500/40"
                          : "bg-[#181d2c]/50 border-white/5 text-zinc-400"
                      }`}
                    >
                      <span className="truncate pr-2">{kw}</span>
                      <span className={`text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded ${
                        isUsed ? "bg-emerald-500/20 text-emerald-400" : "bg-[#181d2c] text-zinc-500 border border-white/5"
                      }`}>
                        {isUsed ? "✓ Used" : "Unused"}
                      </span>
                    </div>
                  );
                })}
                {targetKeywords.length === 0 && (
                  <div className="text-xs text-zinc-500 font-semibold py-4 text-center">
                    No keywords entered yet.
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Listing Draft Optimizer Editor */}
          <div className="lg:col-span-8 bg-[#111625]/20 border border-white/5 rounded-xl p-6 shadow-sm space-y-5">
            {/* Title Section */}
            <div>
              <div className="flex items-baseline justify-between mb-1.5">
                <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Draft Product Title</span>
                <span className={`text-[10px] font-mono font-bold ${titleDraft.length > 200 ? "text-amber-400 font-extrabold" : "text-zinc-500"}`}>
                  {titleDraft.length} / 200 characters
                </span>
              </div>
               <input
                type="text"
                value={titleDraft}
                onChange={(e) => setTitleDraft(e.target.value)}
                placeholder="Draft your optimized product title..."
                className="input font-medium"
              />
            </div>

            {/* Bullets Section */}
            <div className="space-y-4">
              <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider block">
                Features & Bullet Points (Drafting Checklist)
              </span>
              {[
                { val: bullet1, set: setBullet1, label: "Bullet Point 1" },
                { val: bullet2, set: setBullet2, label: "Bullet Point 2" },
                { val: bullet3, set: setBullet3, label: "Bullet Point 3" },
                { val: bullet4, set: setBullet4, label: "Bullet Point 4" },
                { val: bullet5, set: setBullet5, label: "Bullet Point 5" },
              ].map((b, idx) => (
                <div key={idx} className="space-y-1">
                  <div className="flex items-baseline justify-between">
                    <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">{b.label}</span>
                    <span className={`text-[9px] font-mono font-bold ${b.val.length > 500 ? "text-amber-400 font-extrabold" : "text-zinc-500"}`}>
                      {b.val.length} / 500 characters
                    </span>
                  </div>
                   <input
                    type="text"
                    value={b.val}
                    onChange={(e) => b.set(e.target.value)}
                    placeholder={`Key feature copy block ${idx + 1}...`}
                    className="input py-2 text-xs"
                  />
                </div>
              ))}
            </div>

            {/* Description Section */}
            <div>
              <div className="flex items-baseline justify-between mb-1.5">
                <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Product Detailed Description</span>
                <span className={`text-[10px] font-mono font-bold ${descriptionDraft.length > 2000 ? "text-amber-400 font-extrabold" : "text-zinc-500"}`}>
                  {descriptionDraft.length} / 2000 characters
                </span>
              </div>
               <textarea
                value={descriptionDraft}
                onChange={(e) => setDescriptionDraft(e.target.value)}
                placeholder="Draft product specifications description copy..."
                className="w-full h-36 border border-black/15 rounded-lg p-3 text-xs outline-none focus:border-zinc-400 text-zinc-800 bg-white leading-relaxed resize-none shadow-sm"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const peerColumns: Column<ListingPeer>[] = [
  { key: "rank", header: "Rank", render: (p) => (p.rank != null ? `#${p.rank}` : "—"), cellClassName: "text-zinc-500 font-mono text-xs" },
  {
    key: "title",
    header: "Product",
    cellClassName: "text-white font-semibold",
    render: (p) => (
      <span className="max-w-sm truncate block" title={p.title ?? p.asin}>
        {p.title ?? p.asin}
      </span>
    ),
  },
  { key: "price", header: "Price", render: (p) => (p.price != null ? `₹${p.price.toLocaleString("en-IN")}` : "—"), cellClassName: "font-mono text-white" },
  { key: "rating", header: "Rating", render: (p) => `${p.rating ?? "—"} ⭐`, cellClassName: "font-mono text-white" },
  {
    key: "review_count",
    header: "Reviews",
    cellClassName: "font-mono text-white",
    render: (p) => p.review_count?.toLocaleString("en-IN") ?? "—",
  },
];
