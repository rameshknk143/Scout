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
        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 h-full p-5 text-zinc-800">
          {/* Left column - search list */}
          <div className="md:col-span-7 flex flex-col justify-between space-y-3">
            <div>
              <div className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest font-mono mb-2">
                Real-time Opportunities
              </div>
              <div className="space-y-2">
                {[
                  { name: "Noise-cancel earbuds", score: "88", color: "text-emerald-600", bg: "bg-emerald-500/10" },
                  { name: "Sport wireless buds", score: "64", color: "text-amber-700", bg: "bg-amber-500/10" },
                  { name: "Budget TWS clone", score: "41", color: "text-red-600", bg: "bg-red-500/10" },
                ].map((item, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-2.5 rounded-lg bg-zinc-50 border border-zinc-100 text-xs"
                  >
                    <span className="text-zinc-700 font-medium truncate max-w-[150px]">
                      {item.name}
                    </span>
                    <span className={`font-bold font-mono px-2 py-0.5 rounded text-[11px] ${item.color} ${item.bg}`}>
                      {item.score}
                    </span>
                  </div>
                ))}
              </div>
            </div>
            <div className="text-[11px] text-zinc-400 font-mono">
              * Based on local search queries & competitor BSR indicators
            </div>
          </div>

          {/* Right column - Opportunity Score ring */}
          <div className="md:col-span-5 flex flex-col items-center justify-center bg-zinc-50 border border-zinc-100 rounded-2xl p-4">
            <div className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest font-mono">
              OPPORTUNITY SCORE
            </div>
            <div className="relative w-20 h-20 rounded-full border-[6px] border-emerald-500/10 border-t-emerald-500 flex items-center justify-center font-mono font-bold text-2xl text-zinc-800 mt-3 shadow-[0_0_15px_rgba(16,185,129,0.1)]">
              82
            </div>
            <span className="text-[9px] font-bold text-emerald-600 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-0.5 rounded-md uppercase tracking-wider mt-4">
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
        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 h-full p-5 text-zinc-800">
          {/* Left Column: Side-by-Side comparison */}
          <div className="md:col-span-8 flex flex-col gap-3 justify-center">
            <div className="p-3 rounded-xl bg-red-50/70 border border-red-200/60 text-xs">
              <div className="font-bold text-red-500 uppercase tracking-wider text-[8px] mb-1 font-mono">Original Product Title</div>
              <p className="text-zinc-600 leading-relaxed font-sans">
                "Cheap wireless earphone for running with mic and good sound."
              </p>
            </div>
            <div className="p-3 rounded-xl bg-emerald-50/70 border border-emerald-200/60 text-xs">
              <div className="font-bold text-emerald-600 uppercase tracking-wider text-[8px] mb-1 font-mono">AI-Optimized Title (High Conversion)</div>
              <p className="text-zinc-800 leading-relaxed font-sans font-medium">
                "Active Noise Cancelling Wireless Earbuds - Waterproof Sport Headphones with Mic."
              </p>
            </div>
          </div>

          {/* Right Column: AI health score */}
          <div className="md:col-span-4 flex flex-col justify-between bg-zinc-50 border border-zinc-100 rounded-2xl p-4">
            <div>
              <div className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest font-mono text-center">
                AI HEALTH INDEX
              </div>
              <div className="text-center font-mono font-bold text-2xl text-emerald-600 mt-2">
                92 <span className="text-xs text-zinc-400">/ 100</span>
              </div>
            </div>
            <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 text-[10px] py-2 px-3 rounded-lg text-center font-semibold mt-3">
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
        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 h-full p-5 text-zinc-800">
          {/* Left Column: Spreadsheet style fee */}
          <div className="md:col-span-7 flex flex-col justify-between">
            <div className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest font-mono mb-2">
              Sourcing & Fee Analysis
            </div>
            <div className="bg-zinc-50 border border-zinc-100 p-3 rounded-xl space-y-2 font-mono text-[11px] leading-relaxed">
              <div className="flex justify-between text-zinc-500">
                <span>Sale Price</span>
                <span className="text-zinc-800 font-bold">₹1,499.00</span>
              </div>
              <div className="flex justify-between text-zinc-500">
                <span>Sourcing Cost</span>
                <span className="text-zinc-800 font-bold">₹420.00</span>
              </div>
              <div className="flex justify-between text-zinc-400 border-t border-zinc-200/60 pt-2">
                <span>Referral Fee (12%)</span>
                <span>-₹179.88</span>
              </div>
              <div className="flex justify-between text-zinc-400">
                <span>FBA Pick & Pack</span>
                <span>-₹64.00</span>
              </div>
            </div>
          </div>

          {/* Right Column: Net profit */}
          <div className="md:col-span-5 flex flex-col justify-between bg-zinc-50 border border-zinc-100 rounded-2xl p-4">
            <div>
              <div className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest font-mono">
                ESTIMATED NET MARGIN
              </div>
              <div className="text-2xl font-bold font-mono text-zinc-800 mt-1.5">₹835.12</div>
            </div>
            <div className="text-xs font-bold text-center text-emerald-600 bg-emerald-500/10 border border-emerald-500/20 py-2.5 rounded-xl mt-4">
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
        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 h-full p-5 text-zinc-800">
          {/* Left Column: line graph */}
          <div className="md:col-span-7 flex flex-col justify-between">
            <div>
              <div className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest font-mono mb-2">
                12-Week BSR Demand Trend
              </div>
              <div className="h-20 w-full relative overflow-hidden bg-zinc-50 border border-zinc-100 rounded-xl p-2.5 mt-1">
                <svg viewBox="0 0 100 40" preserveAspectRatio="none" className="w-full h-full">
                  <defs>
                    <linearGradient id="glow-rad-line" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0" stopColor="#0284c7" stopOpacity="0.15" />
                      <stop offset="1" stopColor="#0284c7" stopOpacity="0" />
                    </linearGradient>
                  </defs>
                  <polygon points="0,40 12,34 24,38 36,24 48,29 60,15 72,20 84,10 96,14 100,5 100,40" fill="url(#glow-rad-line)" />
                  <polyline points="0,40 12,34 24,38 36,24 48,29 60,15 72,20 84,10 96,14 100,5" fill="none" stroke="#0284c7" strokeWidth="2.5" vectorEffect="non-scaling-stroke" />
                </svg>
              </div>
            </div>
            <div className="text-[10px] text-zinc-400 font-mono">
              ▲ Ranking improved by +42% over last 90 days
            </div>
          </div>

          {/* Right Column: notification hub */}
          <div className="md:col-span-5 flex flex-col gap-2 justify-center">
            <div className="p-2 rounded bg-amber-50/70 border border-amber-200/60 text-[10px] flex gap-2">
              <span className="text-amber-700 font-bold font-mono">ALERT</span>
              <span className="text-zinc-700 truncate">ASIN ranking up by +14 positions</span>
            </div>
            <div className="p-2 rounded bg-emerald-50/70 border border-emerald-200/60 text-[10px] flex gap-2">
              <span className="text-emerald-600 font-bold font-mono">OPPORTUNITY</span>
              <span className="text-zinc-700 truncate">Category Electronics rose 25%</span>
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
      <div className="w-full max-w-[620px] rounded-2xl border border-black/5 bg-white overflow-hidden shadow-[0_20px_50px_-10px_rgba(0,0,0,0.1),_0_1px_4px_rgba(0,0,0,0.03),_inset_0_0_0_1px_rgba(255,255,255,0.8)]">
        {/* Browser Header Bar */}
        <div className="flex items-center justify-between border-b border-black/5 bg-zinc-50 px-4 py-3 flex-wrap sm:flex-nowrap gap-2">
          {/* Red/Yellow/Green mock dots */}
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-red-500/60" />
            <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/60" />
            <div className="w-2.5 h-2.5 rounded-full bg-green-500/60" />
          </div>

          {/* Browser Address Bar URL */}
          <div className="w-full max-w-[280px] bg-black/[0.03] border border-black/5 rounded-md px-3 py-1 text-[10px] font-mono text-zinc-500 truncate text-center select-none mx-2 order-3 sm:order-none">
            scoutveda.com/dashboard/{slides[current].urlPath}
          </div>

          {/* App Title */}
          <span className="text-[8px] font-bold text-zinc-400 uppercase tracking-widest font-mono">
            SCOUTVEDA CONSOLE
          </span>
        </div>

        {/* Tab Selection Bar */}
        <div className="flex items-center border-b border-black/5 bg-zinc-50/50 px-3">
          {slides.map((slide, idx) => {
            const active = idx === current;
            return (
              <button
                key={idx}
                onClick={() => selectTab(idx)}
                className={`px-4 py-2.5 text-[10px] font-bold uppercase tracking-wider font-mono border-b-2 transition-all focus:outline-none ${
                  active
                    ? "border-[#d97706] text-[#d97706] bg-black/[0.01]"
                    : "border-transparent text-zinc-500 hover:text-zinc-700"
                }`}
              >
                {slide.tabName}
              </button>
            );
          })}
        </div>

        {/* Browser screen area with slide transition */}
        <div className="relative h-[250px] bg-white overflow-hidden flex flex-col">
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
                ? "w-6 bg-[#d97706] shadow-[0_0_8px_rgba(217,119,6,0.3)]"
                : "bg-zinc-300 hover:bg-zinc-400"
            }`}
            aria-label={`Go to slide ${idx + 1}`}
          />
        ))}
      </div>
    </div>
  );
}
