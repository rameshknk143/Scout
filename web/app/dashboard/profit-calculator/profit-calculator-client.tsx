"use client";

import { useState, useTransition } from "react";
import VerdictBadge from "@/components/VerdictBadge";
import { Field, MiniStat } from "@/components/ui";
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
  const [batchVolume, setBatchVolume] = useState("500");
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

  const exportFinancialStatementCSV = () => {
    if (!result) return;
    const vol = parseInt(batchVolume, 10) || 1;
    const csvRows = [
      ["ScoutVeda Storefront Financial P&L Model Statement"],
      ["Generated Date", new Date().toISOString().slice(0, 10)],
      ["Target Batch Unit Volume", vol],
      ["Sell Price (Per Unit)", `INR ${sellPrice}`],
      ["Sourcing Cost (Per Unit)", `INR ${buyPrice}`],
      ["Referral Fee (Amazon)", `INR ${result.referral_fee}`],
      ["Closing Fee (Amazon)", `INR ${result.closing_fee}`],
      ["Fulfillment Fee (Shipping)", `INR ${result.weight_or_pickpack_fee}`],
      ["Total Amazon Fees Subtotal", `INR ${result.amazon_fees_subtotal}`],
      ["Net Margin (Per Unit)", `INR ${result.net_margin_rupees}`],
      ["Net Margin %", `${result.net_margin_pct}%`],
      ["Total Batch Revenue", `INR ${(parseFloat(sellPrice) * vol).toFixed(2)}`],
      ["Total Sourcing Cost", `INR ${(parseFloat(buyPrice) * vol).toFixed(2)}`],
      ["Total Net Profit (Batch)", `INR ${(result.net_margin_rupees * vol).toFixed(2)}`],
    ];

    const csvContent = "data:text/csv;charset=utf-8," + csvRows.map((e) => e.join(",")).join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `ScoutVeda_PL_Statement_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const volumeUnits = parseInt(batchVolume, 10) || 1;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-black/5 pb-3">
        <div>
          <div className="text-[10px] font-bold tracking-widest text-emerald-600 uppercase">
            Stage 06 · Storefront P&L Modeling
          </div>
          <h2 className="text-xl font-bold text-zinc-900">Unit Economics & Batch Financial P&L Statement</h2>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="glass-panel p-6 bg-white border border-black/5 space-y-5 rounded-2xl shadow-sm">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
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
          <Field label="Target Batch Volume (Units)">
            <input
              type="number"
              min={1}
              value={batchVolume}
              onChange={(e) => setBatchVolume(e.target.value)}
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
              <option value="easy_ship">Easy Ship (Amazon delivers)</option>
              <option value="fba">FBA (Amazon stores & delivers)</option>
              <option value="self_ship">Self Ship (Merchant handles logistics)</option>
            </select>
          </Field>
          <Field label="GST Rate">
            <select value={gst} onChange={(e) => setGst(e.target.value)} className="input cursor-pointer">
              <option value="18">18% (Standard apparel/electronics)</option>
              <option value="12">12%</option>
              <option value="5">5%</option>
              <option value="0">0%</option>
            </select>
          </Field>
          <Field label="Shipping Zone">
            <select value={zone} onChange={(e) => setZone(e.target.value)} className="input cursor-pointer">
              <option value="national">National</option>
              <option value="regional">Regional</option>
              <option value="local">Local</option>
            </select>
          </Field>
        </div>

        <div className="pt-2">
          <button type="submit" disabled={isPending} className="btn-primary w-full py-2.5 text-xs uppercase font-bold tracking-wider">
            {isPending ? "Calculating P&L Statement…" : "Calculate Unit Economics & Batch P&L 📊"}
          </button>
        </div>
      </form>

      {result && (
        <div className="space-y-6">
          {/* Action Header */}
          <div className="flex items-center justify-between bg-zinc-900 text-white p-4 rounded-2xl shadow-sm">
            <div>
              <span className="text-[10px] font-mono uppercase text-emerald-400 font-bold">P&L Financial Verdict</span>
              <div className="flex items-center gap-3 mt-1">
                <VerdictBadge verdict={result.verdict} />
                <span className="text-sm font-bold">
                  {result.verdict === "PURSUE" ? "High Profitability Candidate" : result.verdict === "WATCH" ? "Moderate Margins — Monitor Fees" : "Low Margin — Risk of Loss"}
                </span>
              </div>
            </div>
            <button
              onClick={exportFinancialStatementCSV}
              className="px-4 py-2 bg-emerald-600 text-white rounded-xl text-xs font-bold hover:bg-emerald-700 transition shadow-sm"
            >
              📥 Export Financial Statement (CSV)
            </button>
          </div>

          {/* Unit KPI Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MiniStat label="Net Profit / Unit" value={`₹${result.net_margin_rupees}`} />
            <MiniStat label="Net Profit Margin %" value={`${result.net_margin_pct}%`} />
            <MiniStat
              label="Breakeven Price"
              value={result.breakeven_price !== null ? `₹${result.breakeven_price}` : "—"}
            />
            <MiniStat label="Breakeven ACoS" value={`${result.breakeven_acos_pct}%`} />
          </div>

          {/* Batch Projection Card */}
          <div className="bg-white p-6 rounded-2xl border border-black/5 shadow-sm space-y-4">
            <h3 className="text-sm font-bold text-zinc-900">
              Batch Volume Financial Projection ({volumeUnits.toLocaleString("en-IN")} Units)
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl bg-zinc-50 border border-zinc-200">
                <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">Total Projected Revenue</span>
                <div className="text-xl font-extrabold text-zinc-900 mt-1 font-mono">
                  ₹{(parseFloat(sellPrice) * volumeUnits).toLocaleString("en-IN")}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-zinc-50 border border-zinc-200">
                <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">Total Sourcing Inventory Cost</span>
                <div className="text-xl font-extrabold text-zinc-900 mt-1 font-mono">
                  ₹{(parseFloat(buyPrice) * volumeUnits).toLocaleString("en-IN")}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200">
                <span className="text-[10px] font-bold text-emerald-800 uppercase tracking-wider">Total Net Profit (Batch)</span>
                <div className="text-xl font-extrabold text-emerald-900 mt-1 font-mono">
                  ₹{(result.net_margin_rupees * volumeUnits).toLocaleString("en-IN")}
                </div>
              </div>
            </div>
          </div>

          {/* Fee Waterfall */}
          <div className="bg-white p-6 rounded-2xl border border-black/5 shadow-sm space-y-3">
            <h3 className="text-sm font-bold text-zinc-900">Fee Breakdown (Per Unit)</h3>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between py-1.5 border-b border-zinc-100">
                <span className="text-zinc-600 font-medium">Selling price</span>
                <span className="font-mono font-bold text-zinc-900">₹{sellPrice}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-zinc-100 text-red-600">
                <span>− Buy / sourcing cost</span>
                <span className="font-mono font-bold">₹{buyPrice}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-zinc-100 text-red-600">
                <span>− Amazon referral fee ({category.replace("_", " ")})</span>
                <span className="font-mono font-bold">₹{result.referral_fee}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-zinc-100 text-red-600">
                <span>− Amazon closing fee</span>
                <span className="font-mono font-bold">₹{result.closing_fee}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-zinc-100 text-red-600">
                <span>− Weight / fulfillment fee ({fulfillment.replace("_", " ")})</span>
                <span className="font-mono font-bold">₹{result.weight_or_pickpack_fee}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-zinc-100 text-amber-700">
                <span>− Returns provision (~5%)</span>
                <span className="font-mono font-bold">₹{result.returns_provision}</span>
              </div>
              <div className="flex justify-between py-2 font-bold text-sm text-emerald-700 pt-2">
                <span>= Net margin</span>
                <span className="font-mono">₹{result.net_margin_rupees} ({result.net_margin_pct}%)</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
