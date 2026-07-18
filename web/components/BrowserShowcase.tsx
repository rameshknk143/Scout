"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";

type Slide = {
  tabName: string;
  urlPath: string;
  title: string;
  renderContent: () => React.ReactNode;
};

export default function BrowserShowcase() {
  const [current, setCurrent] = useState(0);
  const [direction, setDirection] = useState(1);

  const slides: Slide[] = [
    {
      tabName: "Opportunity Finder",
      urlPath: "opportunity-finder",
      title: "Product Search & Score",
      renderContent: () => (
        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 h-full p-5 text-white">
          {/* Left column - search list */}
          <div className="md:col-span-7 flex flex-col justify-between space-y-3">
            <div>
              <div className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest font-mono mb-2">
                Real-time Opportunities
              </div>
              <div className="space-y-2">
                {[
                  { name: "Noise-cancel earbuds", score: "88", color: "text-emerald-400", bg: "bg-emerald-500/10" },
                  { name: "Sport wireless buds", score: "64", color: "text-amber-400", bg: "bg-amber-500/10" },
                  { name: "Budget TWS clone", score: "41", color: "text-red-400", bg: "bg-red-500/10" },
                ].map((item, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-2.5 rounded-lg bg-white/[0.02] border border-white/5 text-xs"
                  >
                    <span className="text-zinc-300 font-medium truncate max-w-[150px]">
                      {item.name}
                    </span>
                    <span className={`font-bold font-mono px-2 py-0.5 rounded text-[11px] ${item.color} ${item.bg}`}>
                      {item.score}
                    </span>
                  </div>
                ))}
              </div>
            </div>
            <div className="text-[11px] text-zinc-500 font-mono">
              * Based on local search queries & competitor BSR indicators
            </div>
          </div>

          {/* Right column - Opportunity Score ring */}
          <div className="md:col-span-5 flex flex-col items-center justify-center bg-zinc-950/40 border border-white/5 rounded-2xl p-4">
            <div className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest font-mono">
              OPPORTUNITY SCORE
            </div>
            <div className="relative w-20 h-20 rounded-full border-[6px] border-emerald-500/20 border-t-emerald-400 flex items-center justify-center font-mono font-bold text-2xl text-white mt-3 shadow-[0_0_20px_rgba(16,185,129,0.15)]">
              82
            </div>
            <span className="text-[9px] font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-0.5 rounded-md uppercase tracking-wider mt-4">
              PURSUE Opportunity
            </span>
          </div>
        </div>
      ),
    },
    {
      tabName: "AI Optimizer",
      urlPath: "listing-optimizer",
      title: "AI Title & Keyword Health",
      renderContent: () => (
        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 h-full p-5 text-white">
          {/* Left Column: Side-by-Side comparison */}
          <div className="md:col-span-8 flex flex-col gap-3 justify-center">
            <div className="p-3 rounded-xl bg-red-500/5 border border-red-500/15 text-xs">
              <div className="font-bold text-red-400 uppercase tracking-wider text-[8px] mb-1 font-mono">Original Product Title</div>
              <p className="text-zinc-400 leading-relaxed font-sans">
                "Cheap wireless earphone for running with mic and good sound."
              </p>
            </div>
            <div className="p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/15 text-xs">
              <div className="font-bold text-emerald-400 uppercase tracking-wider text-[8px] mb-1 font-mono">AI-Optimized Title (High Conversion)</div>
              <p className="text-zinc-200 leading-relaxed font-sans font-medium">
                "Active Noise Cancelling Wireless Earbuds - Waterproof Sport Headphones with Mic."
              </p>
            </div>
          </div>

          {/* Right Column: AI health score */}
          <div className="md:col-span-4 flex flex-col justify-between bg-zinc-950/40 border border-white/5 rounded-2xl p-4">
            <div>
              <div className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest font-mono text-center">
                AI HEALTH INDEX
              </div>
              <div className="text-center font-mono font-bold text-2xl text-emerald-400 mt-2">
                92 <span className="text-xs text-zinc-500">/ 100</span>
              </div>
            </div>
            <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] py-2 px-3 rounded-lg text-center font-semibold mt-3">
              +14% Conversion boost
            </div>
          </div>
        </div>
      ),
    },
    {
      tabName: "Profit Calculator",
      urlPath: "profit-calculator",
      title: "FBA Margin Breakdown",
      renderContent: () => (
        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 h-full p-5 text-white">
          {/* Left Column: Spreadsheet style fee */}
          <div className="md:col-span-7 flex flex-col justify-between">
            <div className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest font-mono mb-2">
              Sourcing & Fee Analysis
            </div>
            <div className="bg-white/[0.01] border border-white/5 p-3 rounded-xl space-y-2 font-mono text-[11px] leading-relaxed">
              <div className="flex justify-between text-zinc-400">
                <span>Sale Price</span>
                <span className="text-white">₹1,499.00</span>
              </div>
              <div className="flex justify-between text-zinc-400">
                <span>Sourcing Cost</span>
                <span className="text-white">₹420.00</span>
              </div>
              <div className="flex justify-between text-zinc-500 border-t border-white/5 pt-2">
                <span>Referral Fee (12%)</span>
                <span>-₹179.88</span>
              </div>
              <div className="flex justify-between text-zinc-500">
                <span>FBA Pick & Pack</span>
                <span>-₹64.00</span>
              </div>
            </div>
          </div>

          {/* Right Column: Net profit */}
          <div className="md:col-span-5 flex flex-col justify-between bg-zinc-950/40 border border-white/5 rounded-2xl p-4">
            <div>
              <div className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest font-mono">
                ESTIMATED NET MARGIN
              </div>
              <div className="text-2xl font-bold font-mono text-white mt-1.5">₹835.12</div>
            </div>
            <div className="text-xs font-bold text-center text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 py-2.5 rounded-xl mt-4">
              34% Net ROI
            </div>
          </div>
        </div>
      ),
    },
    {
      tabName: "Trend Explorer",
      urlPath: "trend-explorer",
      title: "Niche BSR & Alert radar",
      renderContent: () => (
        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 h-full p-5 text-white">
          {/* Left Column: line graph */}
          <div className="md:col-span-7 flex flex-col justify-between">
            <div>
              <div className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest font-mono mb-2">
                12-Week BSR Demand Trend
              </div>
              <div className="h-20 w-full relative overflow-hidden bg-white/[0.01] border border-white/5 rounded-xl p-2.5 mt-1">
                <svg viewBox="0 0 100 40" preserveAspectRatio="none" className="w-full h-full">
                  <defs>
                    <linearGradient id="glow-rad-line" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0" stopColor="#38bdf8" stopOpacity="0.4" />
                      <stop offset="1" stopColor="#38bdf8" stopOpacity="0" />
                    </linearGradient>
                  </defs>
                  <polygon points="0,40 12,34 24,38 36,24 48,29 60,15 72,20 84,10 96,14 100,5 100,40" fill="url(#glow-rad-line)" />
                  <polyline points="0,40 12,34 24,38 36,24 48,29 60,15 72,20 84,10 96,14 100,5" fill="none" stroke="#38bdf8" strokeWidth="2.5" vectorEffect="non-scaling-stroke" />
                </svg>
              </div>
            </div>
            <div className="text-[10px] text-zinc-500 font-mono">
              ▲ Ranking improved by +42% over last 90 days
            </div>
          </div>

          {/* Right Column: notification hub */}
          <div className="md:col-span-5 flex flex-col gap-2 justify-center">
            <div className="p-2 rounded bg-amber-500/5 border border-amber-500/15 text-[10px] flex gap-2">
              <span className="text-amber-400 font-bold font-mono">ALERT</span>
              <span className="text-zinc-300 truncate">ASIN ranking up by +14 positions</span>
            </div>
            <div className="p-2 rounded bg-emerald-500/5 border border-emerald-500/15 text-[10px] flex gap-2">
              <span className="text-emerald-400 font-bold font-mono">OPPORTUNITY</span>
              <span className="text-zinc-300 truncate">Category Electronics rose 25%</span>
            </div>
          </div>
        </div>
      ),
    },
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setDirection(1);
      setCurrent((prev) => (prev + 1) % slides.length);
    }, 5000);
    return () => clearInterval(timer);
  }, [slides.length]);

  const selectTab = (idx: number) => {
    setDirection(idx > current ? 1 : -1);
    setCurrent(idx);
  };

  const slideVariants = {
    enter: (dir: number) => ({
      y: dir > 0 ? 180 : -180,
      opacity: 0,
      scale: 0.98,
    }),
    center: {
      y: 0,
      opacity: 1,
      scale: 1,
      transition: {
        y: { type: "spring" as const, stiffness: 350, damping: 28 },
        opacity: { duration: 0.2 },
        scale: { duration: 0.25 },
      },
    },
    exit: (dir: number) => ({
      y: dir > 0 ? -180 : 180,
      opacity: 0,
      scale: 0.98,
      transition: {
        y: { type: "spring" as const, stiffness: 350, damping: 28 },
        opacity: { duration: 0.2 },
        scale: { duration: 0.25 },
      },
    }),
  };

  return (
    <div className="w-full flex flex-col items-center gap-6">
      {/* 3D Browser window container */}
      <div className="w-full max-w-[620px] rounded-2xl border border-white/10 bg-[#0f1524]/90 backdrop-blur-md overflow-hidden shadow-[0_30px_60px_-15px_rgba(0,0,0,0.8),_inset_0_0_0_1px_rgba(255,255,255,0.06)]">
        {/* Browser Header Bar */}
        <div className="flex items-center justify-between border-b border-white/5 bg-zinc-950/40 px-4 py-3 flex-wrap sm:flex-nowrap gap-2">
          {/* Red/Yellow/Green mock dots */}
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-red-500/60" />
            <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/60" />
            <div className="w-2.5 h-2.5 rounded-full bg-green-500/60" />
          </div>

          {/* Browser Address Bar URL */}
          <div className="w-full max-w-[280px] bg-black/40 border border-white/5 rounded-md px-3 py-1 text-[10px] font-mono text-zinc-500 truncate text-center select-none mx-2 order-3 sm:order-none">
            scoutveda.com/dashboard/{slides[current].urlPath}
          </div>

          {/* App Title */}
          <span className="text-[8px] font-bold text-zinc-500 uppercase tracking-widest font-mono">
            SCOUTVEDA CONSOLE
          </span>
        </div>

        {/* Tab Selection Bar */}
        <div className="flex items-center border-b border-white/5 bg-zinc-950/20 px-3">
          {slides.map((slide, idx) => {
            const active = idx === current;
            return (
              <button
                key={idx}
                onClick={() => selectTab(idx)}
                className={`px-4 py-2 text-[10px] font-bold uppercase tracking-wider font-mono border-b-2 transition-all focus:outline-none ${
                  active
                    ? "border-[#f59e0b] text-[#f59e0b] bg-white/[0.02]"
                    : "border-transparent text-zinc-500 hover:text-zinc-300"
                }`}
              >
                {slide.tabName}
              </button>
            );
          })}
        </div>

        {/* Browser screen area with slide transition */}
        <div className="relative h-[250px] bg-[#05070c] overflow-hidden flex flex-col">
          <AnimatePresence initial={false} custom={direction} mode="wait">
            <motion.div
              key={current}
              custom={direction}
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              className="absolute inset-0 w-full h-full"
            >
              {slides[current].renderContent()}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>

      {/* Pagination controls under the browser */}
      <div className="flex items-center gap-2">
        {slides.map((_, idx) => (
          <button
            key={idx}
            onClick={() => selectTab(idx)}
            className={`w-2 h-2 rounded-full transition-all duration-300 ${
              idx === current
                ? "w-6 bg-[#f59e0b] shadow-[0_0_10px_rgba(245,158,11,0.4)]"
                : "bg-zinc-700 hover:bg-zinc-600"
            }`}
            aria-label={`Go to slide ${idx + 1}`}
          />
        ))}
      </div>
    </div>
  );
}
