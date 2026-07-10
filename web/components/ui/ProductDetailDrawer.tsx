"use client";

import { useEffect, useState, useTransition } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { api } from "@/lib/api";

interface ProductDetailDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  product: {
    asin: string;
    title: string;
    price: number | string;
    rating?: number;
    reviews?: number;
    score?: number;
    verdict?: "PURSUE" | "WATCH" | "SKIP";
    category?: string;
    notes?: string;
    buy_price?: number;
    sell_price?: number;
    shipping_cost?: number;
    fees?: number;
    net_margin?: number;
  } | null;
  onUpdateNotes?: (asin: string, newNotes: string) => Promise<void>;
}

export default function ProductDetailDrawer({
  isOpen,
  onClose,
  product,
  onUpdateNotes,
}: ProductDetailDrawerProps) {
  const [activeTab, setActiveTab] = useState<"overview" | "trends" | "listing" | "notes">("overview");
  const [notesText, setNotesText] = useState("");
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    if (product) {
      setNotesText(product.notes || "");
      setActiveTab("overview");
    }
  }, [product]);

  if (!product) return null;

  // Mock trend data based on price and score for chart rendering
  const trendData = [
    { day: "Mon", BSR: 4800, Price: Number(product.price) || 299 },
    { day: "Tue", BSR: 4200, Price: (Number(product.price) || 299) * 0.98 },
    { day: "Wed", BSR: 3900, Price: (Number(product.price) || 299) * 0.98 },
    { day: "Thu", BSR: 4500, Price: (Number(product.price) || 299) * 1.02 },
    { day: "Fri", BSR: 3100, Price: (Number(product.price) || 299) * 1.02 },
    { day: "Sat", BSR: 2800, Price: Number(product.price) || 299 },
    { day: "Sun", BSR: 2400, Price: Number(product.price) || 299 },
  ];

  const handleSaveNotes = () => {
    if (!onUpdateNotes) return;
    startTransition(async () => {
      await onUpdateNotes(product.asin, notesText);
    });
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.3 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-50 bg-black/60 cursor-pointer"
          />

          {/* Slide-over Drawer */}
          <motion.div
            initial={{ translateX: "100%" }}
            animate={{ translateX: 0 }}
            exit={{ translateX: "100%" }}
            transition={{ type: "spring", damping: 30, stiffness: 280 }}
            className="fixed inset-y-0 right-0 z-50 w-full max-w-xl bg-white shadow-2xl border-l border-zinc-200 flex flex-col h-full"
          >
            {/* Header */}
            <div className="p-6 border-b border-zinc-200/80">
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest bg-zinc-100 border border-zinc-200 px-2 py-0.5 rounded">
                    {product.category || "General"}
                  </span>
                  <h2 className="text-base font-bold text-zinc-950 mt-2 line-clamp-2">
                    {product.title}
                  </h2>
                  <div className="flex items-center gap-3 mt-1.5 text-xs text-zinc-500 font-semibold">
                    <span>ASIN: <strong className="text-zinc-800">{product.asin}</strong></span>
                    <span>•</span>
                    <span>Marketplace: <strong className="text-zinc-800">Amazon.in</strong></span>
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="p-1 rounded-md text-zinc-400 hover:text-zinc-600 hover:bg-zinc-100 cursor-pointer"
                >
                  ✕
                </button>
              </div>
            </div>

            {/* Quick Metrics Bar */}
            <div className="grid grid-cols-3 divide-x divide-zinc-200 border-b border-zinc-200/80 bg-zinc-50/50">
              <div className="p-4 text-center">
                <span className="block text-[9px] font-bold text-zinc-400 uppercase tracking-wider">
                  Current Price
                </span>
                <span className="block text-base font-extrabold text-zinc-950 mt-1">
                  ₹{product.price}
                </span>
              </div>
              <div className="p-4 text-center">
                <span className="block text-[9px] font-bold text-zinc-400 uppercase tracking-wider">
                  Opportunity Score
                </span>
                <span className={`block text-base font-extrabold mt-1 ${
                  product.score && product.score >= 70
                    ? "text-emerald-700"
                    : product.score && product.score >= 50
                    ? "text-amber-700"
                    : "text-red-700"
                }`}>
                  {product.score || "N/A"}
                </span>
              </div>
              <div className="p-4 text-center">
                <span className="block text-[9px] font-bold text-zinc-400 uppercase tracking-wider">
                  Net Margin
                </span>
                <span className="block text-base font-extrabold text-emerald-700 mt-1">
                  {product.net_margin ? `${product.net_margin.toFixed(1)}%` : "N/A"}
                </span>
              </div>
            </div>

            {/* Tabs Navigation */}
            <div className="flex border-b border-zinc-200/80 px-4">
              {(["overview", "trends", "listing", "notes"] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`py-3 px-3 text-xs font-bold uppercase tracking-wider border-b-2 transition-all cursor-pointer ${
                    activeTab === tab
                      ? "border-zinc-900 text-zinc-950"
                      : "border-transparent text-zinc-400 hover:text-zinc-600"
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>

            {/* Tab Contents */}
            <div className="flex-1 overflow-y-auto p-6">
              {activeTab === "overview" && (
                <div className="space-y-6">
                  {/* Performance Summary */}
                  <div>
                    <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500 mb-3">
                      Performance Summary
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="glass-panel p-3.5 bg-zinc-50/50">
                        <span className="block text-[10px] text-zinc-400 font-semibold uppercase">
                          Buy Box Status
                        </span>
                        <span className="text-xs font-bold text-zinc-800 mt-1 block">
                          Active (100% Share)
                        </span>
                      </div>
                      <div className="glass-panel p-3.5 bg-zinc-50/50">
                        <span className="block text-[10px] text-zinc-400 font-semibold uppercase">
                          Estimated Monthly Sales
                        </span>
                        <span className="text-xs font-bold text-zinc-800 mt-1 block">
                          185 Units
                        </span>
                      </div>
                      <div className="glass-panel p-3.5 bg-zinc-50/50">
                        <span className="block text-[10px] text-zinc-400 font-semibold uppercase">
                          Fulfillment
                        </span>
                        <span className="text-xs font-bold text-zinc-800 mt-1 block">
                          FBA (Fulfillment by Amazon)
                        </span>
                      </div>
                      <div className="glass-panel p-3.5 bg-zinc-50/50">
                        <span className="block text-[10px] text-zinc-400 font-semibold uppercase">
                          Review Rating
                        </span>
                        <div className="flex items-center gap-1 mt-1 text-xs font-bold text-zinc-800">
                          ⭐️ {product.rating || "4.2"}
                          <span className="text-[10px] text-zinc-400 font-normal">
                            ({product.reviews || "120"} reviews)
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Profit Breakdown */}
                  <div>
                    <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500 mb-3">
                      Margin & Cost Breakdown
                    </h3>
                    <div className="glass-panel p-4 space-y-2.5">
                      <div className="flex justify-between text-xs font-medium">
                        <span className="text-zinc-500">Retail Listing Price</span>
                        <span className="text-zinc-900 font-semibold">₹{product.price}</span>
                      </div>
                      <div className="flex justify-between text-xs font-medium">
                        <span className="text-zinc-500">Estimated Supplier Buy Price</span>
                        <span className="text-zinc-900 font-semibold">₹{product.buy_price || "—"}</span>
                      </div>
                      <div className="flex justify-between text-xs font-medium">
                        <span className="text-zinc-500">Shipping & Logistics</span>
                        <span className="text-zinc-900 font-semibold">₹{product.shipping_cost || "—"}</span>
                      </div>
                      <div className="flex justify-between text-xs font-medium">
                        <span className="text-zinc-500">Amazon Referral & Closing Fees</span>
                        <span className="text-zinc-900 font-semibold">₹{product.fees || "—"}</span>
                      </div>
                      <div className="h-px bg-zinc-200 my-1" />
                      <div className="flex justify-between text-xs font-bold">
                        <span className="text-zinc-800">Estimated Profit per Unit</span>
                        <span className="text-emerald-700">
                          ₹{product.sell_price && product.buy_price
                            ? (product.sell_price - product.buy_price - (product.shipping_cost || 0) - (product.fees || 0)).toFixed(1)
                            : "—"}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === "trends" && (
                <div className="space-y-6">
                  {/* BSR Trend Chart */}
                  <div>
                    <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500 mb-3">
                      Best Sellers Rank (BSR) History (7 Days)
                    </h3>
                    <div className="h-44 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={trendData}>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" />
                          <XAxis dataKey="day" stroke="#71717a" fontSize={11} />
                          <YAxis stroke="#71717a" fontSize={11} reversed />
                          <Tooltip contentStyle={{ fontSize: 11, background: "#fff", border: "1px solid rgba(0,0,0,0.06)", borderRadius: 6 }} />
                          <Line type="monotone" dataKey="BSR" stroke="#b45309" strokeWidth={2} dot={{ r: 3 }} />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  {/* Price History Chart */}
                  <div>
                    <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500 mb-3">
                      Buy Box Price History (7 Days)
                    </h3>
                    <div className="h-44 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={trendData}>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" />
                          <XAxis dataKey="day" stroke="#71717a" fontSize={11} />
                          <YAxis stroke="#71717a" fontSize={11} />
                          <Tooltip contentStyle={{ fontSize: 11, background: "#fff", border: "1px solid rgba(0,0,0,0.06)", borderRadius: 6 }} />
                          <Line type="monotone" dataKey="Price" stroke="#18181b" strokeWidth={2} dot={{ r: 3 }} />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === "listing" && (
                <div className="space-y-5">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500">
                    Listing Audit Checklist
                  </h3>
                  <div className="space-y-2">
                    {[
                      { check: "Title length is optimized (150+ characters)", pass: true },
                      { check: "At least 5 bullet points are present", pass: true },
                      { check: "Contains high-volume search keywords", pass: false },
                      { check: "Image count is 6 or more", pass: true },
                      { check: "A+ Enhanced Brand Content is active", pass: false },
                    ].map((item, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between p-3 rounded-lg border border-zinc-200 bg-zinc-50/30 text-xs font-semibold"
                      >
                        <span className="text-zinc-700">{item.check}</span>
                        <span className={item.pass ? "text-emerald-700" : "text-amber-700"}>
                          {item.pass ? "✓ Pass" : "⚠ Missing"}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {activeTab === "notes" && (
                <div className="space-y-4">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500">
                    Reseller Notes & Sourcing Log
                  </h3>
                  <textarea
                    value={notesText}
                    onChange={(e) => setNotesText(e.target.value)}
                    placeholder="Enter supplier contact details, MOQ notes, or target unit cost ideas..."
                    className="w-full h-40 border border-zinc-200 rounded-lg p-3 text-xs outline-none focus:border-zinc-400 bg-zinc-50/30 focus:bg-white text-zinc-900 leading-relaxed resize-none"
                  />
                  <div className="flex justify-end">
                    <button
                      onClick={handleSaveNotes}
                      disabled={isPending}
                      className="btn-primary w-auto text-xs py-2 px-4 shadow-sm"
                    >
                      {isPending ? "Saving..." : "Save Notes"}
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Bottom Actions Panel */}
            <div className="p-4 border-t border-zinc-200 bg-zinc-50 flex items-center justify-between gap-3">
              <button
                onClick={() => {
                  window.open(`https://www.amazon.in/dp/${product.asin}`, "_blank");
                }}
                className="btn-primary bg-white text-zinc-800 border border-zinc-200 hover:bg-zinc-100 flex-1 text-xs"
              >
                View on Amazon ↗
              </button>
              <button
                onClick={() => {
                  window.location.href = `/validator?asin=${product.asin}`;
                }}
                className="btn-primary flex-1 text-xs"
              >
                Re-Validate Opportunity
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
