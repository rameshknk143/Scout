"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";

type Slide = {
  title: string;
  subtitle: string;
  renderContent: () => React.ReactNode;
};

export default function PhoneShowcase() {
  const [current, setCurrent] = useState(0);
  const [direction, setDirection] = useState(1); // 1 = down/next, -1 = up/prev

  const slides: Slide[] = [
    {
      title: "Opportunity Finder",
      subtitle: "Evaluate items on Amazon India instantly",
      renderContent: () => (
        <div className="flex flex-col h-full justify-between p-4">
          <div className="space-y-3">
            <div className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest font-mono">
              Product Search
            </div>
            <div className="bg-white/[0.02] border border-white/10 p-2.5 rounded-lg flex items-center gap-2 text-xs text-zinc-400 font-medium font-mono">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="7" />
                <path d="m21 21-4.3-4.3" />
              </svg>
              <span>Wireless earbuds</span>
              <span className="text-[9px] font-bold text-[#f59e0b] bg-[#f59e0b]/10 border border-[#f59e0b]/20 px-2 py-0.5 rounded ml-auto">
                ACTIVE
              </span>
            </div>

            <div className="space-y-2 mt-4">
              {[
                { name: "Noise-cancel buds", score: "88", color: "text-emerald-400" },
                { name: "Sport wireless buds", score: "64", color: "text-amber-400" },
                { name: "Budget TWS clone", score: "41", color: "text-red-400" },
              ].map((item, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-2 rounded bg-white/[0.01] border border-white/5 text-xs"
                >
                  <span className="text-zinc-300 font-medium truncate max-w-[120px]">
                    {item.name}
                  </span>
                  <span className={`font-bold font-mono ${item.color}`}>{item.score}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-zinc-950/80 border border-white/5 rounded-xl p-3.5 flex flex-col items-center justify-center">
            <div className="text-[8px] font-bold text-zinc-500 uppercase tracking-widest font-mono">
              OPPORTUNITY SCORE
            </div>
            <div className="w-14 h-14 rounded-full border-4 border-emerald-500/20 border-t-emerald-400 flex items-center justify-center font-mono font-bold text-base text-white mt-2 shadow-[0_0_15px_rgba(16,185,129,0.2)]">
              82
            </div>
            <span className="text-[9px] font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded uppercase tracking-wider mt-3">
              PURSUE
            </span>
          </div>
        </div>
      ),
    },
    {
      title: "Listing Optimizer",
      subtitle: "Optimize titles and keywords with AI",
      renderContent: () => (
        <div className="flex flex-col h-full justify-between p-4">
          <div className="space-y-3">
            <div className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest font-mono">
              AI Listing Health
            </div>
            <div className="bg-[#121c18] border border-emerald-500/20 p-3 rounded-lg flex items-center justify-between">
              <span className="text-xs text-zinc-300 font-medium">Listing Score</span>
              <span className="text-sm font-bold text-emerald-400 font-mono">92 / 100</span>
            </div>
          </div>

          <div className="space-y-2.5 flex-1 mt-4">
            <div className="p-2.5 rounded bg-red-500/5 border border-red-500/15 text-[11px]">
              <div className="font-bold text-red-400 uppercase tracking-wider text-[8px] mb-1 font-mono">Original Description</div>
              <p className="text-zinc-400 leading-normal line-clamp-2">"Cheap wireless earphone for running with mic and good sound."</p>
            </div>
            <div className="p-2.5 rounded bg-emerald-500/5 border border-emerald-500/15 text-[11px]">
              <div className="font-bold text-emerald-400 uppercase tracking-wider text-[8px] mb-1 font-mono">AI Optimized (High Conversion)</div>
              <p className="text-zinc-200 leading-normal line-clamp-2">"Active Noise Cancelling Wireless Earbuds - Waterproof Sport Headphones."</p>
            </div>
          </div>

          <div className="bg-zinc-950/80 border border-white/5 rounded-xl p-3 flex items-center justify-between text-xs mt-3">
            <span className="text-zinc-400 font-medium">AI Suggestions</span>
            <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">
              +14% Traffic
            </span>
          </div>
        </div>
      ),
    },
    {
      title: "Profit & Fees Calculator",
      subtitle: "Analyze referral and FBA margins",
      renderContent: () => (
        <div className="flex flex-col h-full justify-between p-4">
          <div className="space-y-3">
            <div className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest font-mono">
              Net Profit Margin
            </div>
            <div className="bg-white/[0.02] border border-white/10 p-3 rounded-lg space-y-2 font-mono text-xs">
              <div className="flex justify-between text-zinc-400">
                <span>Selling Price</span>
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

          <div className="bg-zinc-950/80 border border-white/5 rounded-xl p-3 flex items-center justify-between mt-4">
            <div>
              <div className="text-[8px] font-bold text-zinc-500 uppercase tracking-widest font-mono">NET MARGIN</div>
              <div className="text-sm font-bold text-white font-mono mt-0.5">₹835.12</div>
            </div>
            <div className="text-xs font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded-lg">
              34% ROI
            </div>
          </div>
        </div>
      ),
    },
    {
      title: "Trend Radar",
      subtitle: "Track bestsellers rankings dynamically",
      renderContent: () => (
        <div className="flex flex-col h-full justify-between p-4">
          <div className="space-y-2">
            <div className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest font-mono">
              12-Week Demand Radar
            </div>
            <div className="h-20 w-full relative overflow-hidden mt-2 bg-white/[0.01] border border-white/5 rounded-lg p-2">
              <svg viewBox="0 0 100 40" preserveAspectRatio="none" className="w-full h-full">
                <defs>
                  <linearGradient id="blue-glow" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0" stopColor="#38bdf8" stopOpacity="0.4" />
                    <stop offset="1" stopColor="#38bdf8" stopOpacity="0" />
                  </linearGradient>
                </defs>
                <polygon points="0,40 10,32 20,38 30,22 40,28 50,14 60,18 70,8 80,12 90,4 100,2 100,40" fill="url(#blue-glow)" />
                <polyline points="0,40 10,32 20,38 30,22 40,28 50,14 60,18 70,8 80,12 90,4 100,2" fill="none" stroke="#38bdf8" strokeWidth="2" vectorEffect="non-scaling-stroke" />
              </svg>
            </div>
          </div>

          <div className="space-y-2 mt-4">
            <div className="flex items-center gap-2 p-2 rounded bg-amber-500/5 border border-amber-500/10 text-[10px]">
              <span className="text-amber-400 font-bold font-mono">⚠️ ALERT</span>
              <span className="text-zinc-300 truncate">ASIN B08XN3Z6P2 ranking rose by +14 positions</span>
            </div>
            <div className="flex items-center gap-2 p-2 rounded bg-emerald-500/5 border border-emerald-500/10 text-[10px]">
              <span className="text-emerald-400 font-bold font-mono">✅ OPPORTUNITY</span>
              <span className="text-zinc-300 truncate">Category Electronics rose 25% this week</span>
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
    }, 4500);
    return () => clearInterval(timer);
  }, [slides.length]);

  const handleNext = () => {
    setDirection(1);
    setCurrent((prev) => (prev + 1) % slides.length);
  };

  const handlePrev = () => {
    setDirection(-1);
    setCurrent((prev) => (prev - 1 + slides.length) % slides.length);
  };

  const selectPage = (idx: number) => {
    setDirection(idx > current ? 1 : -1);
    setCurrent(idx);
  };

  const slideVariants = {
    enter: (dir: number) => ({
      y: dir > 0 ? 320 : -320,
      opacity: 0,
      scale: 0.96,
    }),
    center: {
      y: 0,
      opacity: 1,
      scale: 1,
      transition: {
        y: { type: "spring" as const, stiffness: 350, damping: 28 },
        opacity: { duration: 0.25 },
        scale: { duration: 0.3 },
      },
    },
    exit: (dir: number) => ({
      y: dir > 0 ? -320 : 320,
      opacity: 0,
      scale: 0.96,
      transition: {
        y: { type: "spring" as const, stiffness: 350, damping: 28 },
        opacity: { duration: 0.25 },
        scale: { duration: 0.3 },
      },
    }),
  };

  return (
    <div className="relative flex items-center justify-center select-none gap-6">
      {/* 3D phone bezel wrapper */}
      <div className="relative w-[280px] h-[540px] rounded-[44px] p-3.5 bg-gradient-to-b from-zinc-800 to-zinc-950 shadow-[0_25px_60px_-15px_rgba(0,0,0,0.8),_0_0_0_1px_rgba(255,255,255,0.08)] border border-zinc-700/30 flex flex-col overflow-hidden">
        {/* Notch / Dynamic Island */}
        <div className="absolute top-5 left-1/2 -translate-x-1/2 w-28 h-5 rounded-full bg-black z-30 flex items-center justify-between px-2.5 border border-white/5">
          <div className="w-1.5 h-1.5 rounded-full bg-zinc-900" />
          <div className="w-3.5 h-1.5 rounded-full bg-[#38bdf8]/10 animate-pulse border border-[#38bdf8]/20" />
        </div>

        {/* Screen Frame */}
        <div className="relative flex-1 w-full rounded-[32px] bg-[#05070c] border border-black/40 overflow-hidden flex flex-col pt-7">
          <AnimatePresence initial={false} custom={direction} mode="wait">
            <motion.div
              key={current}
              custom={direction}
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              className="absolute inset-0 flex flex-col pt-7"
            >
              {/* Slide content wrapper */}
              <div className="flex-1 w-full h-full text-white">
                {slides[current].renderContent()}
              </div>
            </motion.div>
          </AnimatePresence>

          {/* Swipe indicator bar */}
          <div className="absolute bottom-2 left-1/2 -translate-x-1/2 w-24 h-1 rounded-full bg-white/20 z-20" />
        </div>
      </div>

      {/* Pagination controls on the side */}
      <div className="flex flex-col gap-3">
        {slides.map((slide, idx) => {
          const active = idx === current;
          return (
            <button
              key={idx}
              onClick={() => selectPage(idx)}
              className="group flex items-center justify-end gap-3 text-left focus:outline-none"
            >
              <div className="hidden md:block transition-all duration-300">
                <div
                  className={`text-[10px] font-bold uppercase tracking-wider transition-colors duration-300 ${
                    active ? "text-white" : "text-zinc-500 group-hover:text-zinc-400"
                  }`}
                >
                  {slide.title}
                </div>
                <div
                  className={`text-[9px] transition-colors duration-300 leading-tight ${
                    active ? "text-[#f59e0b]" : "text-zinc-600 group-hover:text-zinc-500"
                  }`}
                >
                  {slide.subtitle}
                </div>
              </div>
              <div className="relative flex items-center justify-center">
                <span
                  className={`block rounded-full transition-all duration-300 ${
                    active
                      ? "w-2.5 h-2.5 bg-[#f59e0b] shadow-[0_0_10px_rgba(245,158,11,0.5)]"
                      : "w-2 h-2 bg-zinc-700 group-hover:bg-zinc-600"
                  }`}
                />
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
