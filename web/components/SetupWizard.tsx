"use client";

import React, { useState, useEffect } from "react";

export interface SellerConfig {
  brandName: string;
  marketplace: string;
  sellerType: "private_label" | "wholesale" | "arbitrage" | "agency" | "brand_owner";
  experienceLevel: "beginner" | "intermediate" | "advanced";
  revenueBand: "< ₹1L" | "₹1L - ₹5L" | "₹5L - ₹25L" | "₹25L+";
  categories: string[];
  currentTools: string[];
  goals: string[];
  teamSize: string;
  targetMargin: number;
  completedAt?: string;
}

const DEFAULT_CONFIG: SellerConfig = {
  brandName: "My Storefront",
  marketplace: "IN",
  sellerType: "private_label",
  experienceLevel: "intermediate",
  revenueBand: "₹1L - ₹5L",
  categories: ["Electronics", "Home & Kitchen"],
  currentTools: ["Helium 10"],
  goals: ["Find Sourcing Margin", "Rank Keywords"],
  teamSize: "1",
  targetMargin: 20,
};

const DISMISSED_KEY = "scoutveda_setup_dismissed";

interface SetupWizardProps {
  onComplete?: (config: SellerConfig) => void;
  onClose?: () => void;
  isOpen?: boolean;
}

export function SetupWizard({ onComplete, onClose, isOpen = false }: SetupWizardProps) {
  const [step, setStep] = useState(1);
  const [visible, setVisible] = useState(isOpen);
  const [config, setConfig] = useState<SellerConfig>(DEFAULT_CONFIG);

  useEffect(() => {
    const saved = localStorage.getItem("scoutveda_seller_config");
    // Only `handleSave` used to write anything, so dismissing with ✕ or
    // "Skip setup" left no trace and the wizard reopened on every single
    // page load. Dismissing is now remembered separately from completing,
    // so skipping stays skipped without faking a completed config.
    const dismissed = localStorage.getItem(DISMISSED_KEY);
    if (!saved && !dismissed && !isOpen) {
      setVisible(true);
    } else if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setConfig((prev) => ({ ...prev, ...parsed }));
      } catch (e) {}
    }

    const handleTrigger = () => {
      setStep(1);
      setVisible(true);
    };

    window.addEventListener("scoutveda_trigger_setup", handleTrigger);
    return () => {
      window.removeEventListener("scoutveda_trigger_setup", handleTrigger);
    };
  }, [isOpen]);

  if (!visible) return null;

  const handleDismiss = () => {
    localStorage.setItem(DISMISSED_KEY, new Date().toISOString());
    setVisible(false);
    if (onClose) onClose();
  };

  const handleSave = () => {
    const finalConfig = { ...config, completedAt: new Date().toISOString() };
    localStorage.setItem("scoutveda_seller_config", JSON.stringify(finalConfig));
    if (onComplete) onComplete(finalConfig);
    setVisible(false);
    if (onClose) onClose();
  };

  const toggleCategory = (cat: string) => {
    const current = config.categories || [];
    if (current.includes(cat)) {
      setConfig({ ...config, categories: current.filter((c) => c !== cat) });
    } else {
      setConfig({ ...config, categories: [...current, cat] });
    }
  };

  const toggleGoal = (goal: string) => {
    const current = config.goals || [];
    if (current.includes(goal)) {
      setConfig({ ...config, goals: current.filter((g) => g !== goal) });
    } else {
      setConfig({ ...config, goals: [...current, goal] });
    }
  };

  const marketplaces = [
    { code: "IN", name: "Amazon India (amazon.in)", currency: "₹ INR", flag: "🇮🇳" },
    { code: "US", name: "Amazon US (amazon.com)", currency: "$ USD", flag: "🇺🇸" },
    { code: "UK", name: "Amazon UK (amazon.co.uk)", currency: "£ GBP", flag: "🇬🇧" },
    { code: "DE", name: "Amazon Germany (amazon.de)", currency: "€ EUR", flag: "🇩🇪" },
    { code: "FR", name: "Amazon France (amazon.fr)", currency: "€ EUR", flag: "🇫🇷" },
    { code: "IT", name: "Amazon Italy (amazon.it)", currency: "€ EUR", flag: "🇮🇹" },
    { code: "ES", name: "Amazon Spain (amazon.es)", currency: "€ EUR", flag: "🇪🇸" },
    { code: "CA", name: "Amazon Canada (amazon.ca)", currency: "$ CAD", flag: "🇨🇦" },
    { code: "AU", name: "Amazon Australia (amazon.com.au)", currency: "$ AUD", flag: "🇦🇺" },
    { code: "JP", name: "Amazon Japan (amazon.co.jp)", currency: "¥ JPY", flag: "🇯🇵" },
    { code: "MX", name: "Amazon Mexico (amazon.com.mx)", currency: "$ MXN", flag: "🇲🇽" },
    { code: "AE", name: "Amazon UAE (amazon.ae)", currency: "AED", flag: "🇦🇪" },
  ];

  const sellerTypes = [
    { id: "private_label", label: "Private Label", desc: "Building your own brand; focus on launches & keyword ranking" },
    { id: "wholesale", label: "Wholesale & Distribution", desc: "Reselling existing brands; focus on sourcing margins & buy-box" },
    { id: "arbitrage", label: "Retail / Online Arbitrage", desc: "Sourcing discounted store stock; focus on rapid flip ROI" },
    { id: "agency", label: "Agency / Multi-Brand", desc: "Managing client accounts & multi-workspace analytics" },
  ];

  const categoryOptions = [
    "Electronics & Mobile Accessories",
    "Home & Kitchen",
    "Clothing & Apparel",
    "Beauty & Personal Care",
    "Sports & Fitness",
    "Toys & Games",
    "Health & Grocery",
  ];

  const goalOptions = [
    "Maximize Sourcing Margin",
    "Track Keyword Ranks",
    "Prevent Stockouts & Suppression",
    "Automate Storefront Sales Sync",
    "Monitor Competitor Moves",
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="bg-white rounded-2xl shadow-xl border border-black/10 w-full max-w-xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-5 border-b border-zinc-100 flex items-center justify-between bg-zinc-50/50">
          <div>
            <div className="text-[10px] font-bold tracking-widest text-emerald-600 uppercase">
              Phase 04 · Blueprint Setup Wizard
            </div>
            <h2 className="text-base font-bold text-zinc-900 mt-0.5">
              Personalize Your ScoutVeda Operating Cockpit
            </h2>
          </div>
          <button
            onClick={handleDismiss}
            aria-label="Close setup wizard"
            className="text-zinc-400 hover:text-zinc-600 p-1 rounded-lg hover:bg-zinc-100 text-sm font-semibold transition"
          >
            ✕
          </button>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-zinc-100 h-1">
          <div
            className="bg-emerald-500 h-1 transition-all duration-300 ease-out"
            style={{ width: `${(step / 4) * 100}%` }}
          />
        </div>

        {/* Body Steps */}
        <div className="p-6 space-y-5 flex-1 overflow-y-auto">
          {step === 1 && (
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-zinc-700 mb-1">
                  1. Business / Storefront Name
                </label>
                <input
                  type="text"
                  value={config.brandName}
                  onChange={(e) => setConfig({ ...config, brandName: e.target.value })}
                  placeholder="e.g. City Knights, ScoutVeda Retail"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-zinc-200 text-sm text-zinc-900 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-700 mb-1">
                  Primary Marketplace & Currency
                </label>
                <div className="grid grid-cols-2 gap-2.5 mt-2">
                  {marketplaces.map((mp) => (
                    <button
                      key={mp.code}
                      type="button"
                      onClick={() => setConfig({ ...config, marketplace: mp.code })}
                      className={`p-3 rounded-xl text-left border transition flex flex-col ${
                        config.marketplace === mp.code
                          ? "border-emerald-500 bg-emerald-50/50 ring-1 ring-emerald-500"
                          : "border-zinc-200 hover:border-zinc-300 bg-white"
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-base">{mp.flag}</span>
                        <span className="text-xs font-bold text-zinc-900">{mp.code}</span>
                      </div>
                      <span className="text-[11px] text-zinc-500 mt-1 font-medium">{mp.currency}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-zinc-700 mb-1">
                  2. Select Your Seller Model
                </label>
                <p className="text-xs text-zinc-500 mb-3">
                  This reorders your dashboard widgets (Pulse, Attention, Momentum, Guidance) to match your workflow.
                </p>
                <div className="space-y-2">
                  {sellerTypes.map((st) => (
                    <button
                      key={st.id}
                      type="button"
                      onClick={() => setConfig({ ...config, sellerType: st.id as any })}
                      className={`w-full p-3 rounded-xl text-left border transition ${
                        config.sellerType === st.id
                          ? "border-emerald-500 bg-emerald-50/50 ring-1 ring-emerald-500"
                          : "border-zinc-200 hover:border-zinc-300 bg-white"
                      }`}
                    >
                      <div className="text-xs font-bold text-zinc-900">{st.label}</div>
                      <div className="text-[11px] text-zinc-500 mt-0.5">{st.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-700 mb-1">
                  Monthly Revenue Band
                </label>
                <div className="grid grid-cols-4 gap-2">
                  {(["< ₹1L", "₹1L - ₹5L", "₹5L - ₹25L", "₹25L+"] as const).map((band) => (
                    <button
                      key={band}
                      type="button"
                      onClick={() => setConfig({ ...config, revenueBand: band })}
                      className={`py-2 px-1 text-center rounded-lg border text-xs font-semibold transition ${
                        config.revenueBand === band
                          ? "border-emerald-500 bg-emerald-50 text-emerald-900"
                          : "border-zinc-200 text-zinc-600 hover:border-zinc-300"
                      }`}
                    >
                      {band}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-zinc-700 mb-1">
                  3. Categories You Sell In
                </label>
                <p className="text-xs text-zinc-500 mb-2">
                  Pre-filters your competitor intelligence and trend radar feeds.
                </p>
                <div className="flex flex-wrap gap-2">
                  {categoryOptions.map((cat) => {
                    const selected = (config.categories || []).includes(cat);
                    return (
                      <button
                        key={cat}
                        type="button"
                        onClick={() => toggleCategory(cat)}
                        className={`px-3 py-1.5 rounded-full text-xs font-medium border transition ${
                          selected
                            ? "border-emerald-500 bg-emerald-50 text-emerald-900 font-semibold"
                            : "border-zinc-200 text-zinc-600 hover:border-zinc-300"
                        }`}
                      >
                        {selected ? "✓ " : "+ "}
                        {cat}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-700 mb-1">
                  Primary Business Goals
                </label>
                <div className="space-y-1.5">
                  {goalOptions.map((goal) => {
                    const selected = (config.goals || []).includes(goal);
                    return (
                      <button
                        key={goal}
                        type="button"
                        onClick={() => toggleGoal(goal)}
                        className={`w-full text-left px-3 py-2 rounded-xl text-xs border transition flex items-center justify-between ${
                          selected
                            ? "border-emerald-500 bg-emerald-50/50 text-emerald-950 font-semibold"
                            : "border-zinc-200 text-zinc-600 hover:border-zinc-300"
                        }`}
                      >
                        <span>{goal}</span>
                        <span className="text-emerald-600 font-bold">{selected ? "✓" : "+"}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {step === 4 && (
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-zinc-700 mb-1">
                  4. Target Minimum Net Margin (%)
                </label>
                <p className="text-xs text-zinc-500 mb-3">
                  Products with net profit margins meeting or exceeding this % will be marked "PURSUE".
                </p>
                <div className="flex items-center gap-4 bg-zinc-50 p-4 rounded-xl border border-zinc-200">
                  <input
                    type="range"
                    min={10}
                    max={50}
                    step={1}
                    value={config.targetMargin}
                    onChange={(e) => setConfig({ ...config, targetMargin: Number(e.target.value) })}
                    className="w-full accent-emerald-600 cursor-pointer"
                  />
                  <span className="text-lg font-bold text-emerald-700 min-w-[50px] text-right">
                    {config.targetMargin}%
                  </span>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200/80 text-amber-900 text-xs flex items-start gap-2.5">
                <span className="text-base leading-none">🛡️</span>
                <div>
                  <div className="font-semibold text-amber-950">ScoutVeda Trust Guarantee</div>
                  <p className="text-[11px] text-amber-800/90 mt-0.5 leading-relaxed">
                    We never show fake or simulated numbers. Pre-connection screens will show real research numbers or honest "connect to unlock" cards.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-zinc-100 bg-zinc-50/50 flex items-center justify-between">
          {step > 1 ? (
            <button
              type="button"
              onClick={() => setStep(step - 1)}
              className="px-4 py-2 rounded-xl border border-zinc-200 text-xs font-semibold text-zinc-700 hover:bg-zinc-100 transition"
            >
              Back
            </button>
          ) : (
            <button
              type="button"
              onClick={handleDismiss}
              className="px-4 py-2 text-xs font-semibold text-zinc-400 hover:text-zinc-600 transition"
            >
              Skip setup
            </button>
          )}

          {step < 4 ? (
            <button
              type="button"
              onClick={() => setStep(step + 1)}
              className="px-5 py-2 rounded-xl bg-zinc-900 text-white text-xs font-semibold hover:bg-zinc-800 transition shadow-sm"
            >
              Next Step →
            </button>
          ) : (
            <button
              type="button"
              onClick={handleSave}
              className="px-5 py-2 rounded-xl bg-emerald-600 text-white text-xs font-semibold hover:bg-emerald-700 transition shadow-sm"
            >
              Complete Setup & Launch Cockpit 🚀
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
