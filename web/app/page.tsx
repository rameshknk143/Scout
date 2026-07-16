"use client";

import Link from "next/link";
import { useState } from "react";
import Tilt from "@/components/3d/Tilt";

/* ScoutVeda public landing page. All copy/data here is marketing-only sample
   content — it deliberately does NOT touch the real product-research logic. */

function Wordmark() {
  return (
    <Link href="/" className="sv-mark">
      <span className="sv-mark-dot" />
      Scout<b>Veda</b>
    </Link>
  );
}

const NAV = [
  { label: "Product Research", href: "#research" },
  { label: "Features", href: "#features" },
  { label: "How It Works", href: "#how" },
  { label: "Pricing", href: "#pricing" },
];

export default function Landing() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div className="sv-page">
      <div className="sv-bg" aria-hidden>
        <div className="sv-grid-perspective">
          <div className="sv-grid-plane" />
        </div>
      </div>

      <header className="sv-header">
        <div className="sv-wrap sv-header-inner">
          <Wordmark />
          <nav className="sv-nav" aria-label="Primary">
            {NAV.map((n) => (
              <a key={n.href} href={n.href}>{n.label}</a>
            ))}
          </nav>
          <div className="sv-header-cta">
            <Link href="/login" className="sv-btn sv-btn-ghost sv-hide-sm">Log in</Link>
            <Link href="/signup" className="sv-btn sv-btn-primary">Start researching</Link>
            <button
              className="sv-burger"
              aria-label="Menu"
              aria-expanded={menuOpen}
              onClick={() => setMenuOpen((v) => !v)}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                {menuOpen ? <path d="M18 6 6 18M6 6l12 12" /> : <><path d="M3 6h18" /><path d="M3 12h18" /><path d="M3 18h18" /></>}
              </svg>
            </button>
          </div>
        </div>
        {menuOpen && (
          <div className="sv-mobile-menu" style={{ display: "flex" }}>
            {NAV.map((n) => <a key={n.href} href={n.href} onClick={() => setMenuOpen(false)}>{n.label}</a>)}
            <a href="/login">Log in</a>
          </div>
        )}
      </header>

      {/* HERO */}
      <section className="sv-wrap sv-hero">
        <div className="sv-hero-grid">
          <div>
            <span className="sv-eyebrow">Amazon product research</span>
            <h1 className="sv-h1">Find products worth selling.</h1>
            <p className="sv-lede">
              ScoutVeda helps Amazon resellers research products, understand competition,
              and make sourcing decisions with confidence.
            </p>
            <div className="sv-hero-cta">
              <Link href="/signup" className="sv-btn sv-btn-primary sv-btn-lg">Start free research</Link>
              <a href="#how" className="sv-btn sv-btn-ghost sv-btn-lg">See how it works</a>
            </div>
            <div className="sv-hero-trust">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--sv-teal)" strokeWidth="2"><path d="M20 6 9 17l-5-5" /></svg>
              Independent research platform — not affiliated with Amazon
            </div>
          </div>

          {/* Dashboard preview (marketing visual only) */}
          <HeroPreview />
        </div>
      </section>

      {/* PROBLEM / VALUE */}
      <section id="research" className="sv-wrap sv-section">
        <div className="sv-section-head">
          <span className="sv-eyebrow">The problem</span>
          <h2 className="sv-h2">Product sourcing gets expensive when decisions are guesswork.</h2>
          <p className="sv-sub">Buying stock on a hunch ties up capital in products that don&apos;t sell. ScoutVeda replaces the guessing with data you can act on.</p>
        </div>
        <div className="sv-value-grid">
          {[
            { t: "Discover products faster", d: "Surface opportunities across categories instead of scrolling bestseller lists by hand.", i: "search" },
            { t: "Evaluate competition first", d: "See how entrenched the incumbents are before you commit a rupee to inventory.", i: "shield" },
            { t: "Estimate profit before sourcing", d: "Model fees, GST, and margin up front so you know the number before you buy.", i: "coin" },
            { t: "Track demand and trends", d: "Watch how a product is moving — climbing, stable, seasonal, or fading.", i: "trend" },
          ].map((v) => (
            <div key={v.t} className="sv-glass sv-value">
              <div className="ic"><Icon name={v.i} /></div>
              <div><h3>{v.t}</h3><p>{v.d}</p></div>
            </div>
          ))}
        </div>
      </section>

      {/* FEATURES */}
      <section id="features" className="sv-wrap sv-section" style={{ paddingTop: 0 }}>
        <div className="sv-section-head">
          <span className="sv-eyebrow">Features</span>
          <h2 className="sv-h2">Everything you need to vet an opportunity.</h2>
        </div>
        <div className="bento-grid">
          {/* Card 1: Opportunity Scoring (Span 4) */}
          <div className="bento-card bento-col-4 sv-glass p-6 flex flex-col justify-between h-[280px]">
            <div className="flex items-center justify-between">
              <span className="text-[9px] font-bold uppercase tracking-widest text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded font-mono">SCORING ENGINE</span>
              <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="10" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4" />
              </svg>
            </div>
            <div className="my-auto py-4 flex items-center justify-center">
              <div className="sv-score-ring" style={{ "--v": 82 } as React.CSSProperties}><span className="text-xl">82</span></div>
            </div>
            <div>
              <h3 className="text-sm font-bold text-white font-mono uppercase tracking-wider">Opportunity Scoring</h3>
              <p className="text-xs text-zinc-400 font-medium mt-1">See which products deserve a closer look, computed across demand metrics instantly.</p>
            </div>
          </div>

          {/* Card 2: Market Analysis (Span 8) */}
          <div className="bento-card bento-col-8 sv-glass p-6 flex flex-col justify-between h-[280px]">
            <div className="flex items-center justify-between">
              <span className="text-[9px] font-bold uppercase tracking-widest text-blue-400 bg-blue-500/10 border border-blue-500/20 px-2.5 py-1 rounded font-mono">COMPETITION MAP</span>
              <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 002 2h2a2 2 0 002-2z" />
              </svg>
            </div>
            <div className="my-auto py-4 flex items-end justify-center gap-3.5 h-[100px]">
              {[35, 68, 48, 92, 54, 76, 62].map((val, idx) => (
                <div key={idx} className="w-6 bg-blue-500 rounded-t-sm" style={{ height: `${val}%` }} />
              ))}
            </div>
            <div>
              <h3 className="text-sm font-bold text-white font-mono uppercase tracking-wider">Market Analysis</h3>
              <p className="text-xs text-zinc-400 font-medium mt-1">Deep-dive into competitor pricing, ratings, reviews depth, and listing entrenchment.</p>
            </div>
          </div>

          {/* Card 3: Profit Insights (Span 8) */}
          <div className="bento-card bento-col-8 sv-glass p-6 flex flex-col justify-between h-[280px]">
            <div className="flex items-center justify-between">
              <span className="text-[9px] font-bold uppercase tracking-widest text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2.5 py-1 rounded font-mono">MARGIN ESTIMATOR</span>
              <svg className="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <rect x="4" y="4" width="16" height="16" rx="2" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 9h6M9 13h6M9 17h6" />
              </svg>
            </div>
            <div className="my-auto py-4 flex flex-col justify-center space-y-3 w-full">
              <div className="flex justify-between items-center text-xs font-mono">
                <span className="text-zinc-500 font-bold uppercase">Estimated Gross Profit</span>
                <span className="text-emerald-400 font-bold">31% Margin</span>
              </div>
              <div className="w-full bg-white/[0.04] h-2.5 rounded-full overflow-hidden">
                <div className="bg-gradient-to-r from-emerald-500/70 to-emerald-400 h-full w-[31%]" />
              </div>
              <div className="flex justify-between text-[10px] text-zinc-400 font-medium">
                <span>FBA Fees: ₹184</span>
                <span>GST (18%): ₹89</span>
                <span>Closing Fee: ₹25</span>
              </div>
            </div>
            <div>
              <h3 className="text-sm font-bold text-white font-mono uppercase tracking-wider">Profit Insights</h3>
              <p className="text-xs text-zinc-400 font-medium mt-1">Model Amazon India Easy Ship / FBA referral fees and taxes before buying stock.</p>
            </div>
          </div>

          {/* Card 4: Trend Tracking (Span 4) */}
          <div className="bento-card bento-col-4 sv-glass p-6 flex flex-col justify-between h-[280px]">
            <div className="flex items-center justify-between">
              <span className="text-[9px] font-bold uppercase tracking-widest text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-2.5 py-1 rounded font-mono">TREND RADAR</span>
              <svg className="w-5 h-5 text-indigo-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <div className="my-auto py-4 flex items-center justify-center w-full">
              <svg viewBox="0 0 100 40" preserveAspectRatio="none" style={{ width: "100%", height: 52 }}>
                <defs><linearGradient id="trend-bento-grad" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="var(--sv-teal)" stopOpacity="0.4" /><stop offset="1" stopColor="var(--sv-teal)" stopOpacity="0" /></linearGradient></defs>
                <polygon points="0,40 16,36 33,39 50,22 66,28 83,12 100,5 100,40" fill="url(#trend-bento-grad)" />
                <polyline points="0,40 16,36 33,39 50,22 66,28 83,12 100,5" fill="none" stroke="var(--sv-teal)" strokeWidth="2.5" vectorEffect="non-scaling-stroke" />
              </svg>
            </div>
            <div>
              <h3 className="text-sm font-bold text-white font-mono uppercase tracking-wider">Trend Radar</h3>
              <p className="text-xs text-zinc-400 font-medium mt-1">Spot rising, stable, seasonal, or fading product niches with historical charts.</p>
            </div>
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section id="how" className="sv-wrap sv-section" style={{ paddingTop: 0 }}>
        <div className="sv-section-head">
          <span className="sv-eyebrow">How it works</span>
          <h2 className="sv-h2">Three steps from question to confident decision.</h2>
        </div>
        <div className="sv-steps">
          {[
            { n: "1", t: "Search", d: "Enter a product, keyword, or ASIN you're curious about." },
            { n: "2", t: "Review", d: "Read ScoutVeda's research — score, competition, demand, and margin." },
            { n: "3", t: "Source with confidence", d: "Commit capital knowing the numbers back the decision." },
          ].map((s) => (
            <div key={s.n} className="sv-glass sv-step">
              <div className="sv-step-n">{s.n}</div>
              <h3>{s.t}</h3>
              <p>{s.d}</p>
            </div>
          ))}
        </div>
      </section>

      {/* FINAL CTA */}
      <section id="pricing" className="sv-wrap">
        <div className="sv-glass sv-final">
          <span className="sv-eyebrow">Get started</span>
          <h2 className="sv-h2" style={{ marginTop: 14 }}>Make every sourcing decision with better data.</h2>
          <p className="sv-sub" style={{ margin: "14px auto 0", maxWidth: 520 }}>
            Create your ScoutVeda account and start researching your next opportunity.
          </p>
          <div style={{ marginTop: 26, display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap" }}>
            <Link href="/signup" className="sv-btn sv-btn-primary sv-btn-lg">Create free account</Link>
            <Link href="/login" className="sv-btn sv-btn-ghost sv-btn-lg">Log in</Link>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="sv-footer">
        <div className="sv-wrap">
          <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 24 }}>
            <Wordmark />
            <nav className="sv-footer-links" aria-label="Footer">
              <a href="#features">Product</a>
              <a href="#pricing">Pricing</a>
              <a href="mailto:ramesh@scoutveda.com">Support</a>
              <a href="#">Privacy</a>
              <a href="#">Terms</a>
              <a href="mailto:ramesh@scoutveda.com">Contact</a>
            </nav>
          </div>
          <p className="sv-footer-fine">
            ScoutVeda is an independent research platform and is not affiliated with Amazon.<br />
            © {new Date().getFullYear()} ScoutVeda. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}

/* ---------- Hero dashboard preview (pure visual) ---------- */
function HeroPreview() {
  const spark = [38, 44, 41, 52, 49, 63, 60, 72, 78, 74, 86, 92];
  const max = Math.max(...spark);
  const pts = spark.map((v, i) => `${(i / (spark.length - 1)) * 100},${40 - (v / max) * 34}`).join(" ");

  return (
    <Tilt className="relative w-full max-w-[480px] mx-auto py-10">
      <div className="isometric-view relative w-full h-[380px] transform-style-3d select-none">
        {/* Layer 1: Base Shadow Plate */}
        <div className="absolute inset-0 bg-blue-500/5 rounded-2xl filter blur-xl layer-base" />

        {/* Layer 2: Main Console Board (Layer Base) */}
        <div className="absolute inset-0 sv-glass p-5 flex flex-col justify-between layer-base border border-white/10 bg-[#0f1524]/90 backdrop-blur-md">
          <div className="flex items-center justify-between border-b border-white/5 pb-3">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-red-500/60" />
              <div className="w-2 h-2 rounded-full bg-yellow-500/60" />
              <div className="w-2 h-2 rounded-full bg-green-500/60" />
            </div>
            <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest font-mono">SCOUTVEDA CONSOLE</span>
          </div>

          <div className="sv-preview-search bg-[#060a13] border border-white/5 p-2.5 rounded-lg flex items-center gap-2 text-xs text-zinc-400 font-medium font-mono mt-3">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="7" /><path d="m21 21-4.3-4.3" /></svg>
            <span>Wireless earbuds</span>
            <span className="text-[9px] font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded ml-auto">ACTIVE</span>
          </div>

          {/* List items representing products */}
          <div className="space-y-2 mt-4 flex-1">
            {[
              { n: "Noise-cancel earbuds", c: "Low", t: "g", s: "88" },
              { n: "Sport wireless buds", c: "Medium", t: "a", s: "64" },
              { n: "Budget TWS clone", c: "High", t: "r", s: "41" },
            ].map((r, idx) => (
              <div key={idx} className="flex items-center justify-between p-2 rounded bg-white/[0.01] border border-white/5 text-xs">
                <span className="text-zinc-300 font-medium font-sans truncate max-w-[150px]">{r.n}</span>
                <div className="flex items-center gap-3">
                  <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wider ${r.t === "g" ? "text-emerald-400 bg-emerald-500/10" : (r.t === "a" ? "text-amber-400 bg-amber-500/10" : "text-red-400 bg-red-500/10")}`}>{r.c}</span>
                  <span className="font-bold text-white font-mono">{r.s}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Layer 3: Floating Opportunity Score (Layer Middle) */}
        <div className="absolute top-4 right-[-20px] w-[145px] bg-[#141b2c] border border-white/10 rounded-xl p-4 shadow-2xl layer-middle flex flex-col items-center justify-center">
          <div className="text-[8px] font-bold text-zinc-500 uppercase tracking-widest font-mono">OPPORTUNITY SCORE</div>
          <div className="sv-score-ring mt-2.5" style={{ "--v": 82 } as React.CSSProperties}><span>82</span></div>
          <span className="text-[9px] font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded uppercase tracking-wider mt-3">PURSUE</span>
        </div>

        {/* Layer 4: Floating Stats Widget (Layer High) */}
        <div className="absolute bottom-[40px] left-[-30px] w-[165px] bg-[#141b2c] border border-white/10 rounded-xl p-3.5 shadow-2xl layer-high space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[8px] font-bold text-zinc-500 uppercase tracking-widest font-mono">EST. MONTHLY SALES</span>
            <span className="text-emerald-400 text-[10px] font-bold">▲ 24%</span>
          </div>
          <div className="text-lg font-bold text-white font-mono">2,140 <span className="text-[10px] text-zinc-400 font-sans font-medium">units</span></div>
          <div className="w-full bg-white/[0.04] h-1.5 rounded-full overflow-hidden">
            <div className="bg-emerald-500 h-full w-[72%]" />
          </div>
        </div>

        {/* Layer 5: Floating Trend Sparkline (Layer Top) */}
        <div className="absolute bottom-[20px] right-[-10px] w-[190px] bg-[#141b2c] border border-white/10 rounded-xl p-3.5 shadow-2xl layer-top">
          <div className="text-[8px] font-bold text-zinc-500 uppercase tracking-widest font-mono mb-2">12-WEEK DEMAND RADAR</div>
          <svg viewBox="0 0 100 40" preserveAspectRatio="none" style={{ width: "100%", height: 36 }}>
            <defs><linearGradient id="glow-grad" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="var(--sv-teal)" stopOpacity="0.4" /><stop offset="1" stopColor="var(--sv-teal)" stopOpacity="0" /></linearGradient></defs>
            <polygon points={`0,40 ${pts} 100,40`} fill="url(#glow-grad)" />
            <polyline points={pts} fill="none" stroke="var(--sv-teal)" strokeWidth="2" vectorEffect="non-scaling-stroke" />
          </svg>
        </div>
      </div>
    </Tilt>
  );
}

function Icon({ name }: { name: string }) {
  const common = { width: 18, height: 18, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 2, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  if (name === "search") return <svg {...common}><circle cx="11" cy="11" r="7" /><path d="m21 21-4.3-4.3" /></svg>;
  if (name === "shield") return <svg {...common}><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z" /></svg>;
  if (name === "coin") return <svg {...common}><circle cx="12" cy="12" r="9" /><path d="M12 7v10M9.5 9.5h4a1.5 1.5 0 0 1 0 3h-3a1.5 1.5 0 0 0 0 3h4" /></svg>;
  return <svg {...common}><path d="M3 17l6-6 4 4 8-8" /><path d="M17 7h4v4" /></svg>;
}
