"use client";

import { useState, useTransition } from "react";
import { motion, AnimatePresence } from "framer-motion";
import VerdictBadge from "@/components/VerdictBadge";
import type { ProfitResult } from "@/lib/api";
import { FEE_CATEGORIES } from "@/lib/constants";
import { calcProfit } from "@/lib/actions";

const FEE_LABELS: Record<string, string> = {
  electronics_accessories: "Electronics Accessories",
  fashion_apparel: "Fashion & Apparel",
  home_kitchen: "Home & Kitchen",
  beauty_personal_care: "Beauty & Personal Care",
  grocery: "Grocery",
  books: "Books",
  sports_fitness: "Sports & Fitness",
  toys: "Toys",
  automotive_parts: "Automotive Parts",
  other_default: "Other / Default",
};

export default function ProfitCalculatorClient() {
  const [sellPrice, setSellPrice] = useState("499");
  const [buyPrice, setBuyPrice] = useState("150");
  const [category, setCategory] = useState<string>(FEE_CATEGORIES[0]);
  const [weightGrams, setWeightGrams] = useState("300");
  const [fulfillment, setFulfillment] = useState("easy_ship");
  const [gst, setGst] = useState("18");
  const [zone, setZone] = useState("national");

  const [result, setResult] = useState<ProfitResult | null>(null);
  const [isPending, startTransition] = useTransition();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    startTransition(async () => {
      const res = await calcProfit({
        sell_price: parseFloat(sellPrice),
        buy_price: parseFloat(buyPrice),
        category,
        weight_grams: parseInt(weightGrams, 10),
        fulfillment,
        gst_rate_pct: parseInt(gst, 10),
        zone,
      });
      setResult(res);
    });
  }

  return (
    <div className="space-y-8">
      <form onSubmit={handleSubmit} className="glass-panel p-6 space-y-5">
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          <Field label="Sell price (₹)">
            <input
              type="number"
              min={0}
              value={sellPrice}
              onChange={(e) => setSellPrice(e.target.value)}
              className="input"
              required
            />
          </Field>
          <Field label="Buy / cost price (₹)">
            <input
              type="number"
              min={0}
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
          <Field label="Category (fee table)">
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="input"
            >
              {FEE_CATEGORIES.map((c) => (
                <option key={c} value={c} className="bg-bg-elevated">
                  {FEE_LABELS[c]}
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
          <Field label="GST rate">
            <select value={gst} onChange={(e) => setGst(e.target.value)} className="input">
              {[5, 12, 18, 28].map((g) => (
                <option key={g} value={g} className="bg-bg-elevated">
                  {g}%
                </option>
              ))}
            </select>
          </Field>
          {fulfillment === "easy_ship" && (
            <Field label="Zone">
              <select value={zone} onChange={(e) => setZone(e.target.value)} className="input">
                <option value="local" className="bg-bg-elevated">Local</option>
                <option value="regional" className="bg-bg-elevated">Regional</option>
                <option value="national" className="bg-bg-elevated">National</option>
              </select>
            </Field>
          )}
        </div>

        <button
          type="submit"
          disabled={isPending}
          className="rounded-lg bg-amber text-black font-semibold px-6 py-2.5 hover:opacity-90 disabled:opacity-50 transition-opacity"
        >
          {isPending ? "Calculating…" : "Calculate"}
        </button>
      </form>

      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35 }}
            className="glass-panel p-6"
          >
            <div className="flex items-center justify-between mb-5">
              <div className="text-sm text-muted">Net margin</div>
              <VerdictBadge verdict={result.verdict} />
            </div>
            <div className="text-4xl font-bold text-amber amber-glow-text mb-6">
              {result.net_margin_pct.toFixed(1)}%
              <span className="text-lg text-muted font-normal ml-2">
                (₹{result.net_margin_rupees.toFixed(0)}/unit)
              </span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              <Stat label="Referral fee" value={`₹${result.referral_fee}`} />
              <Stat label="Closing fee" value={`₹${result.closing_fee}`} />
              <Stat
                label="Weight / pick-pack fee"
                value={`₹${result.weight_or_pickpack_fee}`}
              />
              <Stat
                label="Amazon fees (total)"
                value={`₹${result.amazon_fees_subtotal}`}
              />
              <Stat
                label="Returns provision"
                value={`₹${result.returns_provision}`}
              />
              <Stat
                label="Breakeven price"
                value={
                  result.breakeven_price != null
                    ? `₹${result.breakeven_price.toFixed(0)}`
                    : "—"
                }
              />
              <Stat
                label="Breakeven ACoS"
                value={`${result.breakeven_acos_pct.toFixed(1)}%`}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="block text-sm text-muted mb-1.5">{label}</span>
      {children}
    </label>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-white/5 px-3 py-2.5">
      <div className="text-xs text-muted">{label}</div>
      <div className="text-lg font-semibold">{value}</div>
    </div>
  );
}
