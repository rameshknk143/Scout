"use client";

import { useState, useTransition } from "react";
import VerdictBadge from "@/components/VerdictBadge";
import { Card, Field, MiniStat } from "@/components/ui";
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
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="glass-panel p-6 bg-[#111625] space-y-5">
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          <Field label="Sell price (₹)">
            <input
              type="number"
              min={0}
              value={sellPrice}
              onChange={(e) => setSellPrice(e.target.value)}
              className="input text-white"
              required
            />
          </Field>
          <Field label="Buy / cost price (₹)">
            <input
              type="number"
              min={0}
              value={buyPrice}
              onChange={(e) => setBuyPrice(e.target.value)}
              className="input text-white"
              required
            />
          </Field>
          <Field label="Weight (grams)">
            <input
              type="number"
              min={1}
              value={weightGrams}
              onChange={(e) => setWeightGrams(e.target.value)}
              className="input text-white"
            />
          </Field>
          <Field label="Category (fee table)">
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="input cursor-pointer"
            >
              {FEE_CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {FEE_LABELS[c]}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Fulfillment Type">
            <select
              value={fulfillment}
              onChange={(e) => setFulfillment(e.target.value)}
              className="input cursor-pointer"
            >
              <option value="easy_ship">Easy Ship</option>
              <option value="fba">FBA</option>
              <option value="self_ship">Self Ship</option>
            </select>
          </Field>
          <Field label="GST rate">
            <select value={gst} onChange={(e) => setGst(e.target.value)} className="input cursor-pointer">
              {[5, 12, 18, 28].map((g) => (
                <option key={g} value={g}>
                  {g}%
                </option>
              ))}
            </select>
          </Field>
          {fulfillment === "easy_ship" && (
            <Field label="Zone">
              <select value={zone} onChange={(e) => setZone(e.target.value)} className="input cursor-pointer">
                <option value="local">Local</option>
                <option value="regional">Regional</option>
                <option value="national">National</option>
              </select>
            </Field>
          )}
        </div>

        <button
          type="submit"
          disabled={isPending}
          className="btn-primary w-auto disabled:opacity-50"
        >
          {isPending ? "Calculating fees…" : "Calculate net margin"}
        </button>
      </form>

      {result && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mt-6 animate-in fade-in duration-200">
          {/* Margin Scorecard */}
          <div className="lg:col-span-4 bg-[#111625]/20 border border-white/5 rounded-xl p-6 flex flex-col justify-between shadow-sm">
            <div>
              <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider block mb-1">Audit Verdict</span>
              <VerdictBadge verdict={result.verdict} />
            </div>
            <div className="mt-8">
              <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider block mb-1">Net Margin %</span>
              <span className="text-4xl font-extrabold text-white tracking-tight font-mono">
                {result.net_margin_pct.toFixed(1)}%
              </span>
              <span className="text-xs font-bold text-zinc-400 block mt-1.5 font-mono">
                Profit: ₹{result.net_margin_rupees.toFixed(2)} per unit
              </span>
            </div>
            <div className="mt-8 pt-4 border-t border-white/5 space-y-2">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-zinc-400">Breakeven Price:</span>
                <span className="text-white font-mono">₹{result.breakeven_price?.toFixed(0)}</span>
              </div>
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-zinc-400">Breakeven ACoS:</span>
                <span className="text-white font-mono">{result.breakeven_acos_pct.toFixed(1)}%</span>
              </div>
            </div>
          </div>

          {/* Fee Breakdown Table */}
          <div className="lg:col-span-8 bg-[#111625]/20 border border-white/5 rounded-xl p-6 shadow-sm">
            <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider block mb-4">Estimated Amazon Fees (Excl. GST)</span>
            <div className="space-y-3.5">
              <div className="flex justify-between items-center text-xs pb-2.5 border-b border-white/5 font-semibold">
                <span className="text-zinc-400 font-medium">Referral Fee ({FEE_LABELS[category]})</span>
                <span className="text-white font-mono">₹{result.referral_fee.toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center text-xs pb-2.5 border-b border-white/5 font-semibold">
                <span className="text-zinc-400 font-medium">Closing Fee (Price bracket)</span>
                <span className="text-white font-mono">₹{result.closing_fee.toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center text-xs pb-2.5 border-b border-white/5 font-semibold">
                <span className="text-zinc-400 font-medium">Fulfillment & Weight Fee ({weightGrams}g, {fulfillment})</span>
                <span className="text-white font-mono">₹{result.weight_or_pickpack_fee.toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center text-xs pb-2.5 border-b border-white/5 font-semibold">
                <span className="text-zinc-400 font-medium">Returns Provision (Estimated risk)</span>
                <span className="text-white font-mono">₹{result.returns_provision.toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center text-xs pt-1">
                <span className="text-white font-extrabold uppercase text-[10px] tracking-wider">Total Est. Amazon Fees</span>
                <span className="text-white font-extrabold text-sm font-mono">₹{result.amazon_fees_subtotal.toFixed(2)}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
