"use client";

import React, { useState, useEffect } from "react";

export interface SellerConfig {
  brandName: string;
  marketplace: string;
  sellerType: "private_label" | "wholesale" | "arbitrage" | "agency" | "brand_owner";
  targetMargin: number;
  completedAt?: string;
}

const DEFAULT_CONFIG: SellerConfig = {
  brandName: "My Amazon Brand",
  marketplace: "IN",
  sellerType: "private_label",
  targetMargin: 20,
};

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
    // Check if configuration already exists in localStorage
    const saved = localStorage.getItem("scoutveda_seller_config");
    if (!saved && !isOpen) {
      setVisible(true);
    } else if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setConfig(parsed);
      } catch (e) {
        // Fallback to default
      }
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

  const handleSave = () => {
    const finalConfig = { ...config, completedAt: new Date().toISOString() };
    localStorage.setItem("scoutveda_seller_config", JSON.stringify(finalConfig));
    window.dispatchEvent(new CustomEvent("scoutveda_config_updated", { detail: finalConfig }));
    if (onComplete) onComplete(finalConfig);
    setVisible(false);
    if (onClose) onClose();
  };

  const marketplaces = [
    { code: "IN", name: "Amazon India (amazon.in)", currency: "₹ INR", flag: "🇮🇳" },
    { code: "US", name: "Amazon US (amazon.com)", currency: "$ USD", flag: "🇺🇸" },
    { code: "EU", name: "Amazon Europe (amazon.de/it/es/fr)", currency: "€ EUR", flag: "🇪🇺" },
    { code: "UK", name: "Amazon UK (amazon.co.uk)", currency: "£ GBP", flag: "🇬🇧" },
  ];

  const sellerTypes = [
    { id: "private_label", label: "Private Label", desc: "Building and selling your own branded products" },
    { id: "wholesale", label: "Wholesale & Distribution", desc: "Reselling existing brand inventory at scale" },
    { id: "arbitrage", label: "Retail / Online Arbitrage", desc: "Sourcing discounted products from retail & online stores" },
    { id: "agency", label: "Agency / Multi-Brand", desc: "Managing Amazon accounts & listings for clients" },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="bg-white rounded-2xl shadow-xl border border-black/10 w-full max-w-lg overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-zinc-100 flex items-center justify-between bg-zinc-50/50">
          <div>
            <div className="text-[10px] font-bold tracking-widest text-emerald-600 uppercase">
              Phase 04 · Onboarding Setup
            </div>
            <h2 className="text-lg font-bold text-zinc-900 mt-0.5">
              Personalize Your ScoutVeda Cockpit
            </h2>
          </div>
          <button
            onClick={() => setVisible(false)}
            className="text-zinc-400 hover:text-zinc-600 p-1 rounded-lg hover:bg-zinc-100 text-sm font-semibold transition"
          >
            ✕
          </button>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-zinc-100 h-1">
          <div
            className="bg-emerald-500 h-1 transition-all duration-300 ease-out"
            style={{ width: `${(step / 3) * 100}%` }}
          />
        </div>

        {/* Body Steps */}
        <div className="p-6 space-y-6 flex-1 overflow-y-auto">
          {step === 1 && (
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-zinc-700 mb-1">
                  1. Business / Brand Name
                </label>
                <p className="text-xs text-zinc-500 mb-2">
                  What is the name of your primary Amazon storefront or brand?
                </p>
                <input
                  type="text"
                  value={config.brandName}
                  onChange={(e) => setConfig({ ...config, brandName: e.target.value })}
                  placeholder="e.g. City Knights, ScoutVeda Store"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-zinc-200 text-sm text-zinc-900 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition"
                />
              </div>

              <div className="pt-2">
                <label className="block text-xs font-semibold text-zinc-700 mb-1">
                  Primary Marketplace
                </label>
                <p className="text-xs text-zinc-500 mb-2">
                  Select your main region to set default currencies and fee calculations.
                </p>
                <div className="grid grid-cols-2 gap-2.5">
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
                  This reorders your dashboard widgets to show what matters most to your workflow.
                </p>
                <div className="space-y-2">
                  {sellerTypes.map((st) => (
                    <button
                      key={st.id}
                      type="button"
                      onClick={() => setConfig({ ...config, sellerType: st.id as any })}
                      className={`w-full p-3.5 rounded-xl text-left border transition ${
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
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-zinc-700 mb-1">
                  3. Target Minimum Net Margin (%)
                </label>
                <p className="text-xs text-zinc-500 mb-3">
                  ASINs meeting or exceeding this net margin will be automatically flagged as "PURSUE".
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
                <span className="text-base leading-none">💡</span>
                <div>
                  <div className="font-semibold text-amber-950">ScoutVeda Honest Policy</div>
                  <p className="text-[11px] text-amber-800/90 mt-0.5 leading-relaxed">
                    We never show fake, simulated, or placeholder numbers on your dashboard. Pre-connection screens will remain empty until you sync real storefront data.
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
              onClick={() => setVisible(false)}
              className="px-4 py-2 text-xs font-semibold text-zinc-400 hover:text-zinc-600 transition"
            >
              Skip setup
            </button>
          )}

          {step < 3 ? (
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
              Complete Setup & Launch 🚀
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
