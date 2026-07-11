"use client";

import { useState, useTransition } from "react";
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
    <div className="space-y-8">
      <form onSubmit={handleSubmit} className="glass-panel p-6 space-y-5 bg-white">
        <div>
          <label className="block text-xs font-bold text-zinc-500 uppercase tracking-wider mb-1.5">Amazon ASIN</label>
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
            <option value="">(auto-detect from Scout's own data)</option>
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
              <div className="text-xs text-muted mb-1">{result.asin}</div>
              <div className="font-semibold leading-snug">{result.title ?? "(title not found)"}</div>
              <div className="text-xs text-muted mt-1">
                {result.category ?? "unknown category"}
                {result.price != null && ` · ₹${result.price.toLocaleString("en-IN")}`}
                {result.rating != null && ` · ${result.rating} ⭐`}
                {result.review_count != null && ` · ${result.review_count.toLocaleString("en-IN")} reviews`}
              </div>
            </div>
            <div className="text-right shrink-0">
              <div className="text-4xl font-extrabold text-zinc-950 tracking-tight">{result.score}</div>
              <div className="text-xs text-zinc-400 mt-1.5">/ 100 Score</div>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3 mb-4">
            {Object.entries(result.components).map(([key, value]) => (
              <MiniStat
                key={key}
                label={COMPONENT_LABELS[key] ?? key}
                value={
                  <>
                    {value}
                    <span className="text-zinc-400 text-xs">/100</span>
                  </>
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

          <div className="pt-3 border-t border-zinc-200/80 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={handleSuggest}
              disabled={isSuggesting}
              className="text-xs font-bold text-zinc-700 bg-white border border-zinc-200 px-3 py-2 rounded-lg hover:bg-zinc-50 cursor-pointer shadow-sm transition-colors disabled:opacity-50"
            >
              {isSuggesting ? "Asking the AI…" : "✨ Suggest AI improvements"}
            </button>
            {result.reviews.length > 0 && (
              <button
                type="button"
                onClick={handleSummarizeReviews}
                disabled={isSummarizing}
                className="text-xs font-bold text-zinc-700 bg-white border border-zinc-200 px-3 py-2 rounded-lg hover:bg-zinc-50 cursor-pointer shadow-sm transition-colors disabled:opacity-50"
              >
                {isSummarizing
                  ? "Reading reviews…"
                  : `🔍 Summarize ${result.reviews.length} reviews`}
              </button>
            )}
          </div>

          <div>
            {suggestError && <div className="text-xs text-zinc-500 mt-3">{suggestError}</div>}

            {suggestion && (
              <div className="mt-4 space-y-3">
                {suggestion.title && (
                  <div>
                    <div className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-1">Suggested title</div>
                    <div className="text-xs font-medium text-zinc-900 bg-zinc-50 rounded-lg px-3 py-2 border border-zinc-200/60">
                      {suggestion.title}
                    </div>
                  </div>
                )}
                {suggestion.bullets.length > 0 && (
                  <div>
                    <div className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-1">Suggested bullets</div>
                    <ul className="space-y-1.5">
                      {suggestion.bullets.map((b, i) => (
                        <li
                          key={i}
                          className="text-xs font-medium text-zinc-900 bg-zinc-50 rounded-lg px-3 py-2 border border-zinc-200/60 leading-relaxed"
                        >
                          {b}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                <div className="text-[10px] text-zinc-400 font-semibold">
                  * AI-generated via a free model router — review before using, not auto-published.
                </div>
              </div>
            )}

            {reviewSummaryError && <div className="text-xs text-zinc-500 mt-3">{reviewSummaryError}</div>}

            {reviewSummary && (
              <div className="mt-4 space-y-3">
                {reviewSummary.pros.length > 0 && (
                  <div>
                    <div className="text-[10px] font-bold text-emerald-700 uppercase tracking-wider mb-1">Pros customers mention</div>
                    <ul className="space-y-1.5">
                      {reviewSummary.pros.map((p, i) => (
                        <li
                          key={i}
                          className="text-xs font-medium bg-emerald-50 text-emerald-900 rounded-lg px-3 py-2 border border-emerald-100"
                        >
                          {p}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {reviewSummary.cons.length > 0 && (
                  <div>
                    <div className="text-[10px] font-bold text-red-700 uppercase tracking-wider mb-1">Cons customers mention</div>
                    <ul className="space-y-1.5">
                      {reviewSummary.cons.map((c, i) => (
                        <li
                          key={i}
                          className="text-xs font-medium bg-red-50 text-red-900 rounded-lg px-3 py-2 border border-red-100"
                        >
                          {c}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                <div className="text-[10px] text-zinc-400 font-semibold">
                  * From {result.reviews.length} of Amazon&apos;s own featured reviews on this listing.
                </div>
              </div>
            )}
          </div>
        </Card>
      )}

      {result && result.peers.length > 0 && (
        <Card>
          <div className="text-sm font-semibold mb-3">
            Category peers — top {result.peers.length} in {result.category ?? "this category"}
          </div>
          <Table
            columns={peerColumns}
            rows={result.peers}
            rowKey={(p) => p.asin}
            emptyText="No peer data for this category yet."
          />
          <div className="text-xs text-muted/70 mt-3">
            From Scout&apos;s own nightly-collected snapshot data — same source as Trend Radar.
          </div>
        </Card>
      )}
    </div>
  );
}

const peerColumns: Column<ListingPeer>[] = [
  { key: "rank", header: "Rank", render: (p) => (p.rank != null ? `#${p.rank}` : "—"), cellClassName: "text-muted" },
  {
    key: "title",
    header: "Product",
    render: (p) => (
      <span className="max-w-sm truncate block" title={p.title ?? p.asin}>
        {p.title ?? p.asin}
      </span>
    ),
  },
  { key: "price", header: "Price", render: (p) => (p.price != null ? `₹${p.price.toLocaleString("en-IN")}` : "—") },
  { key: "rating", header: "Rating", render: (p) => `${p.rating ?? "—"} ⭐` },
  {
    key: "review_count",
    header: "Reviews",
    render: (p) => p.review_count?.toLocaleString("en-IN") ?? "—",
  },
];
