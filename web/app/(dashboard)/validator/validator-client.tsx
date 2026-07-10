"use client";

import { useState, useTransition } from "react";
import VerdictBadge from "@/components/VerdictBadge";
import CaveatBox from "@/components/CaveatBox";
import { Card, Field, MiniStat } from "@/components/ui";
import type { ScoreResult } from "@/lib/api";
import { CATEGORIES } from "@/lib/constants";
import { scoreAsin } from "@/lib/actions";

const WEIGHT_LABELS: Record<string, string> = {
  demand: "Demand",
  competition: "Competition",
  margin: "Margin",
  trend: "Trend",
  differentiation: "Differentiation",
  operational_fit: "Operational fit",
};

export default function ValidatorClient() {
  const [asin, setAsin] = useState("");
  const [buyPrice, setBuyPrice] = useState("100");
  const [weightGrams, setWeightGrams] = useState("300");
  const [fulfillment, setFulfillment] = useState("easy_ship");
  const [gst, setGst] = useState("18");
  const [category, setCategory] = useState("");
  const [differentiation, setDifferentiation] = useState(3);
  const [operationalFit, setOperationalFit] = useState(3);
  const [notes, setNotes] = useState("");

  const [result, setResult] = useState<ScoreResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    startTransition(async () => {
      try {
        const res = await scoreAsin({
          asin: asin.trim(),
          buy_price: parseFloat(buyPrice),
          category: category || undefined,
          weight_grams: parseInt(weightGrams, 10),
          fulfillment,
          gst_rate_pct: parseInt(gst, 10),
          differentiation,
          operational_fit: operationalFit,
          notes,
        });
        setResult(res);
      } catch {
        setError("Couldn't score that ASIN — check it's a valid Amazon product ID and try again.");
      }
    });
  }

  return (
    <div className="space-y-8">
      <form onSubmit={handleSubmit} className="glass-panel p-6 space-y-5">
        <div>
          <label className="block text-sm text-muted mb-1.5">Amazon ASIN</label>
          <input
            value={asin}
            onChange={(e) => setAsin(e.target.value)}
            placeholder="B0D4DZ7WL2"
            required
            className="w-full rounded-lg bg-white/5 border border-white/10 px-4 py-2.5 outline-none focus:border-amber/50 font-mono text-sm"
          />
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          <Field label="Buy / cost price (₹)">
            <input
              type="number"
              min={0}
              step="1"
              value={buyPrice}
              onChange={(e) => setBuyPrice(e.target.value)}
              className="input"
              required
            />
          </Field>
          <Field label="Weight (grams)">
            <input
              type="number"
              min={1}
              value={weightGrams}
              onChange={(e) => setWeightGrams(e.target.value)}
              className="input"
            />
          </Field>
          <Field label="GST rate">
            <select value={gst} onChange={(e) => setGst(e.target.value)} className="input">
              {[5, 12, 18, 28].map((g) => (
                <option key={g} value={g} className="bg-bg-elevated">
                  {g}%
                </option>
              ))}
            </select>
          </Field>
          <Field label="Fulfillment">
            <select
              value={fulfillment}
              onChange={(e) => setFulfillment(e.target.value)}
              className="input"
            >
              <option value="easy_ship" className="bg-bg-elevated">Easy Ship</option>
              <option value="fba" className="bg-bg-elevated">FBA</option>
              <option value="self_ship" className="bg-bg-elevated">Self Ship</option>
            </select>
          </Field>
          <Field label="Category (optional)">
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="input"
            >
              <option value="" className="bg-bg-elevated">(auto-detect)</option>
              {CATEGORIES.map((c) => (
                <option key={c} value={c} className="bg-bg-elevated">
                  {c}
                </option>
              ))}
            </select>
          </Field>
        </div>

        <Slider
          label="Private-label differentiation"
          hint="Can a new, unbranded entrant realistically compete here — or does this category need strong existing brand trust to sell?"
          value={differentiation}
          onChange={setDifferentiation}
        />
        <Slider
          label="Operational fit"
          hint="Could you realistically source, stock, and ship a version of this yourself?"
          value={operationalFit}
          onChange={setOperationalFit}
        />

        <Field label="Notes (optional)">
          <input
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="input"
          />
        </Field>

        <button
          type="submit"
          disabled={isPending}
          className="btn-primary w-auto disabled:opacity-50"
        >
          {isPending ? "Scoring…" : "Score this product"}
        </button>
      </form>

      {error && <div className="text-red text-sm">{error}</div>}

      {result && (
        <Card>
          <div className="flex items-start justify-between gap-4 mb-4">
            <div>
              <div className="text-xs text-muted mb-1">{result.asin}</div>
              <div className="font-semibold leading-snug">{result.title}</div>
              <div className="text-xs text-muted mt-1">
                {result.category ?? "unknown category"} · sell ₹
                {result.sell_price?.toLocaleString("en-IN")} · buy ₹
                {result.buy_price.toLocaleString("en-IN")} · net margin{" "}
                {result.margin_detail.net_margin_pct.toFixed(1)}%
              </div>
            </div>
            <div className="text-right shrink-0">
              <div className="text-4xl font-extrabold text-text tracking-tight">
                {result.score}
              </div>
              <div className="mt-1.5">
                <VerdictBadge verdict={result.verdict} />
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-4">
            {Object.entries(result.weights).map(([key, weight]) => (
              <MiniStat
                key={key}
                label={`${WEIGHT_LABELS[key]} · ${weight}%`}
                value={
                  <>
                    {result.components[key].toFixed(0)}
                    <span className="text-muted text-sm">/100</span>
                  </>
                }
              />
            ))}
          </div>

          {result.caveats.length > 0 && (
            <div className="space-y-2">
              {result.caveats.map((c, i) => (
                <CaveatBox key={i}>{c}</CaveatBox>
              ))}
            </div>
          )}
        </Card>
      )}
    </div>
  );
}

function Slider({
  label,
  hint,
  value,
  onChange,
}: {
  label: string;
  hint: string;
  value: number;
  onChange: (v: number) => void;
}) {
  return (
    <div>
      <div className="flex items-baseline justify-between mb-1">
        <span className="text-sm text-muted">{label}</span>
        <span className="text-amber font-semibold">{value}/5</span>
      </div>
      <input
        type="range"
        min={1}
        max={5}
        value={value}
        onChange={(e) => onChange(parseInt(e.target.value, 10))}
        className="w-full accent-text"
      />
      <p className="text-xs text-muted/80 mt-1">{hint}</p>
    </div>
  );
}
