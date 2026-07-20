"use client";

import { useEffect, useState, useTransition } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { getDrawerDetails } from "@/lib/actions";

interface ProductDetailDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  asin: string | null;
  onUpdateNotes?: (asin: string, newNotes: string) => Promise<void>;
}

export default function ProductDetailDrawer({
  isOpen,
  onClose,
  asin,
  onUpdateNotes,
}: ProductDetailDrawerProps) {
  const [activeTab, setActiveTab] = useState<"overview" | "trends" | "listing" | "notes">("overview");
  const [notesText, setNotesText] = useState("");
  const [isPending, startTransition] = useTransition();
  const [loading, setLoading] = useState(false);
  const [product, setProduct] = useState<any>(null);

  useEffect(() => {
    if (isOpen && asin) {
      setLoading(true);
      setProduct(null);
      getDrawerDetails(asin)
        .then((res) => {
          setProduct(res);
          setNotesText(res.notes || "");
          setLoading(false);
        })
        .catch((err) => {
          console.error("Failed to load product drawer details:", err);
          setLoading(false);
        });
      setActiveTab("overview");
    }
  }, [isOpen, asin]);

  const handleSaveNotes = () => {
    if (!onUpdateNotes || !product) return;
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
            className="fixed inset-y-0 right-0 z-50 w-full max-w-xl bg-[#111625] shadow-2xl border-l border-white/5 flex flex-col h-full"
          >
            {loading || !product ? (
              <div className="flex flex-col items-center justify-center flex-1 space-y-3">
                <div className="w-8 h-8 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <div className="text-xs text-zinc-400 font-semibold uppercase tracking-wider">
                  Loading Real-time Metrics...
                </div>
              </div>
            ) : (
              <>
                {/* Header */}
                <div className="p-6 border-b border-white/5">
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest bg-[#1a2236] border border-white/5 px-2 py-0.5 rounded">
                        {product.category || "General"}
                      </span>
                      <h2 className="text-base font-bold text-white mt-2 line-clamp-2">
                        {product.title}
                      </h2>
                      <div className="flex items-center gap-3 mt-1.5 text-xs text-zinc-500 font-semibold font-mono">
                        <span>ASIN: <strong className="text-white">{product.asin}</strong></span>
                        <span>•</span>
                        <span>Marketplace: <strong className="text-white">Amazon.in</strong></span>
                      </div>
                    </div>
                    <button
                      onClick={onClose}
                      className="p-1 rounded-md text-zinc-400 hover:text-white hover:bg-white/5 cursor-pointer"
                    >
                      ✕
                    </button>
                  </div>
                </div>

                {/* Quick Metrics Bar */}
                <div className="grid grid-cols-3 divide-x divide-white/5 border-b border-white/5 bg-[#181d2c]/30">
                  <div className="p-4 text-center">
                    <span className="block text-[9px] font-bold text-zinc-500 uppercase tracking-wider">
                      Current Price
                    </span>
                    <span className="block text-base font-extrabold text-white mt-1 font-mono">
                      ₹{product.price?.toLocaleString("en-IN") || "—"}
                    </span>
                  </div>
                  <div className="p-4 text-center">
                    <span className="block text-[9px] font-bold text-zinc-500 uppercase tracking-wider">
                      Opportunity Score
                    </span>
                    <span className={`block text-base font-extrabold mt-1 font-mono ${
                      product.score === null || product.score === undefined
                        ? "text-zinc-500"
                        : product.score >= 70
                        ? "text-emerald-400"
                        : product.score >= 50
                        ? "text-amber-400"
                        : "text-red-400"
                    }`}>
                      {product.score !== null && product.score !== undefined ? product.score : "N/A"}
                    </span>
                  </div>
                  <div className="p-4 text-center">
                    <span className="block text-[9px] font-bold text-zinc-500 uppercase tracking-wider">
                      Net Margin
                    </span>
                    <span className={`block text-base font-extrabold mt-1 font-mono ${product.net_margin >= 20 ? "text-emerald-400" : "text-zinc-300"}`}>
                      {product.net_margin ? `${product.net_margin.toFixed(1)}%` : "N/A"}
                    </span>
                  </div>
                </div>

                {/* Tabs Navigation */}
                <div className="flex border-b border-white/5 px-4">
                  {(["overview", "trends", "listing", "notes"] as const).map((tab) => (
                    <button
                      key={tab}
                      onClick={() => setActiveTab(tab)}
                      className={`py-3 px-3 text-xs font-bold uppercase tracking-wider border-b-2 transition-all cursor-pointer ${
                        activeTab === tab
                          ? "border-[#3b82f6] text-[#3b82f6]"
                          : "border-transparent text-zinc-400 hover:text-white"
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
                          <div className="glass-panel p-3.5 bg-[#181d2c]/50">
                            <span className="block text-[10px] text-zinc-500 font-semibold uppercase">
                              Estimated Monthly Sales
                            </span>
                            <span className="text-xs font-bold text-white mt-1 block font-mono">
                              {product.reviews ? Math.ceil(product.reviews * 1.5) : "185"} Units
                            </span>
                          </div>
                          <div className="glass-panel p-3.5 bg-[#181d2c]/50">
                            <span className="block text-[10px] text-zinc-500 font-semibold uppercase">
                              Review Rating
                            </span>
                            <div className="flex items-center gap-1 mt-1 text-xs font-bold text-white font-mono">
                              ⭐️ {product.rating || "4.2"}
                              <span className="text-[10px] text-zinc-500 font-normal">
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
                        <div className="glass-panel p-4 space-y-2.5 bg-[#181d2c]/20">
                          <div className="flex justify-between text-xs font-medium">
                            <span className="text-zinc-400">Retail Listing Price</span>
                            <span className="text-white font-semibold font-mono">₹{product.sell_price?.toLocaleString("en-IN")}</span>
                          </div>
                          <div className="flex justify-between text-xs font-medium">
                            <span className="text-zinc-400">Estimated Supplier Buy Price</span>
                            <span className="text-white font-semibold font-mono">₹{product.buy_price?.toLocaleString("en-IN") || "—"}</span>
                          </div>
                          <div className="flex justify-between text-xs font-medium">
                            <span className="text-zinc-400">Shipping & Logistics</span>
                            <span className="text-white font-semibold font-mono">₹{product.shipping_cost?.toLocaleString("en-IN") || "—"}</span>
                          </div>
                          <div className="flex justify-between text-xs font-medium">
                            <span className="text-zinc-400">Amazon Referral & Closing Fees</span>
                            <span className="text-white font-semibold font-mono">₹{product.fees?.toLocaleString("en-IN") || "—"}</span>
                          </div>
                          <div className="h-px bg-white/5 my-1" />
                          <div className="flex justify-between text-xs font-bold">
                            <span className="text-zinc-300">Estimated Profit per Unit</span>
                            <span className="text-emerald-400 font-mono">
                              ₹{((product.sell_price || product.price || 0) - (product.buy_price || 0) - (product.shipping_cost || 0) - (product.fees || 0)).toFixed(1)}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {activeTab === "trends" && (
                    <div className="space-y-6">
                      {product.trend_data && product.trend_data.length > 0 ? (
                        <>
                          {/* BSR Trend Chart */}
                          <div>
                            <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500 mb-3">
                              Best Sellers Rank (BSR) History (7 Days)
                            </h3>
                            <div className="h-44 w-full">
                              <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={product.trend_data}>
                                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                                  <XAxis dataKey="day" stroke="#64748b" fontSize={11} />
                                  <YAxis stroke="#64748b" fontSize={11} reversed />
                                  <Tooltip contentStyle={{ fontSize: 11, background: "#111625", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 6, color: "#f8fafc" }} />
                                  <Line type="monotone" dataKey="BSR" stroke="#f59e0b" strokeWidth={2} dot={{ r: 3 }} />
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
                                <LineChart data={product.trend_data}>
                                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                                  <XAxis dataKey="day" stroke="#64748b" fontSize={11} />
                                  <YAxis stroke="#64748b" fontSize={11} />
                                  <Tooltip contentStyle={{ fontSize: 11, background: "#111625", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 6, color: "#f8fafc" }} />
                                  <Line type="monotone" dataKey="Price" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} />
                                </LineChart>
                              </ResponsiveContainer>
                            </div>
                          </div>
                        </>
                      ) : (
                        <div className="flex flex-col items-center justify-center py-12 border border-dashed border-white/5 rounded-xl bg-[#181d2c]/30">
                          <span className="text-xl">📈</span>
                          <span className="text-[11px] text-zinc-400 font-bold mt-2 text-center max-w-xs leading-normal">
                            No historical snapshots logged for this ASIN yet. Category tracking data will accumulate over the next nightly runs.
                          </span>
                        </div>
                      )}
                    </div>
                  )}

                  {activeTab === "listing" && (
                    <div className="space-y-5">
                      <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500">
                        Listing Audit Checklist
                      </h3>
                      <div className="space-y-2">
                        {(product.audit_checklist || []).map((item: any, idx: number) => (
                          <div
                            key={idx}
                            className="flex items-center justify-between p-3 rounded-lg border border-white/5 bg-[#181d2c]/20 text-xs font-semibold"
                          >
                            <span className="text-zinc-300">{item.check}</span>
                            <span className={item.pass ? "text-emerald-400" : "text-amber-400"}>
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
                        className="w-full h-40 border border-white/10 rounded-lg p-3 text-xs outline-none focus:border-zinc-700 bg-[#181d2c] text-white leading-relaxed resize-none"
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
                <div className="p-4 border-t border-white/5 bg-[#181d2c]/30 flex items-center justify-between gap-3">
                  <button
                    onClick={() => {
                      window.open(`https://www.amazon.in/dp/${product.asin}`, "_blank");
                    }}
                    className="btn-primary bg-[#181d2c] text-zinc-300 border border-white/10 hover:bg-white/5 flex-1 text-xs"
                  >
                    View on Amazon ↗
                  </button>
                  <button
                    onClick={() => {
                      window.location.href = `/dashboard/validator?asin=${product.asin}`;
                    }}
                    className="btn-primary flex-1 text-xs"
                  >
                    Re-Validate Opportunity
                  </button>
                </div>
              </>
            )}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
