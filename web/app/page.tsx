"use client";

import Link from "next/link";
import { useState } from "react";

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
      <div className="sv-bg" aria-hidden />

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
        <div className="sv-feature-grid">
          {[
            { t: "Opportunity scoring", d: "See which products deserve a closer look.", viz: "score" },
            { t: "Market analysis", d: "Understand prices, demand, ratings, and competition.", viz: "bars" },
            { t: "Profit insights", d: "Estimate potential margins before committing capital.", viz: "margin" },
            { t: "Trend tracking", d: "Spot growing, stable, seasonal, and declining products.", viz: "line" },
          ].map((f) => (
            <div key={f.t} className="sv-glass sv-feature">
              <FeatureViz kind={f.viz} />
              <h3>{f.t}</h3>
              <p>{f.d}</p>
            </div>
          ))}
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
    <div className="sv-glass sv-preview" role="img" aria-label="ScoutVeda research preview">
      <div className="sv-preview-search">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="7" /><path d="m21 21-4.3-4.3" /></svg>
        Wireless earbuds
        <span className="sv-tag g" style={{ marginLeft: "auto" }}>ANALYZED</span>
      </div>

      <div className="sv-preview-top">
        <div className="sv-soft" style={{ padding: 14, textAlign: "center" }}>
          <div style={{ fontSize: "0.66rem", textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--muted)" }}>Opportunity score</div>
          <div className="sv-score-ring"><span>82</span></div>
          <div className="sv-tag g" style={{ marginTop: 10, display: "inline-block" }}>PURSUE</div>
        </div>
        <div className="sv-stat-grid">
          <div className="sv-soft sv-stat"><div className="k">Est. sales / mo</div><div className="v">2,140</div></div>
          <div className="sv-soft sv-stat"><div className="k">Est. revenue</div><div className="v">₹18.2L</div></div>
          <div className="sv-soft sv-stat"><div className="k">Price range</div><div className="v">₹699–1,299</div></div>
          <div className="sv-soft sv-stat"><div className="k">Net margin</div><div className="v" style={{ color: "var(--green)" }}>31%</div></div>
        </div>
      </div>

      <div className="sv-soft sv-spark">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
          <span style={{ fontSize: "0.66rem", textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--muted)" }}>Demand trend · 12 wk</span>
          <span className="sv-tag g">▲ 24%</span>
        </div>
        <svg viewBox="0 0 100 40" preserveAspectRatio="none" style={{ width: "100%", height: 44 }}>
          <defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="var(--sv-teal)" stopOpacity="0.35" /><stop offset="1" stopColor="var(--sv-teal)" stopOpacity="0" /></linearGradient></defs>
          <polygon points={`0,40 ${pts} 100,40`} fill="url(#g)" />
          <polyline points={pts} fill="none" stroke="var(--sv-teal)" strokeWidth="1.6" vectorEffect="non-scaling-stroke" />
        </svg>
      </div>

      <div className="sv-rows">
        {[
          { n: "Noise-cancel earbuds", c: "Low", t: "g", s: "88" },
          { n: "Sport wireless buds", c: "Medium", t: "a", s: "64" },
          { n: "Budget TWS clone", c: "High", t: "r", s: "41" },
        ].map((r) => (
          <div key={r.n} className="sv-row">
            <span className="nm">{r.n}</span>
            <span className={`sv-tag ${r.t}`}>{r.c} comp</span>
            <span style={{ fontFamily: "var(--font-mono)", fontWeight: 700, color: "var(--sv-teal)" }}>{r.s}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ---------- small inline visuals ---------- */
function FeatureViz({ kind }: { kind: string }) {
  if (kind === "bars") {
    const h = [40, 62, 48, 80, 55, 72];
    return <div className="sv-feature-viz">{h.map((v, i) => <div key={i} className="sv-bar" style={{ height: `${v}%` }} />)}</div>;
  }
  if (kind === "score") {
    return <div className="sv-feature-viz" style={{ alignItems: "center", justifyContent: "center" }}>
      <div className="sv-score-ring" style={{ width: 52, height: 52 }}><span style={{ fontSize: "0.85rem" }}>82</span></div>
    </div>;
  }
  if (kind === "margin") {
    return <div className="sv-feature-viz" style={{ alignItems: "center", padding: 12 }}>
      <div style={{ width: "100%", height: 8, borderRadius: 4, background: "rgba(255,255,255,0.06)", overflow: "hidden" }}>
        <div style={{ width: "31%", height: "100%", background: "var(--green)" }} />
      </div>
      <span style={{ marginLeft: 10, fontFamily: "var(--font-mono)", fontWeight: 700, color: "var(--green)", fontSize: "0.85rem" }}>31%</span>
    </div>;
  }
  const pts = [30, 34, 28, 42, 38, 52, 60].map((v, i) => `${(i / 6) * 100},${40 - (v / 60) * 30}`).join(" ");
  return <div className="sv-feature-viz" style={{ padding: 8 }}>
    <svg viewBox="0 0 100 40" preserveAspectRatio="none" style={{ width: "100%", height: "100%" }}>
      <polyline points={pts} fill="none" stroke="var(--sv-teal)" strokeWidth="2" vectorEffect="non-scaling-stroke" />
    </svg>
  </div>;
}

function Icon({ name }: { name: string }) {
  const common = { width: 18, height: 18, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 2, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  if (name === "search") return <svg {...common}><circle cx="11" cy="11" r="7" /><path d="m21 21-4.3-4.3" /></svg>;
  if (name === "shield") return <svg {...common}><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z" /></svg>;
  if (name === "coin") return <svg {...common}><circle cx="12" cy="12" r="9" /><path d="M12 7v10M9.5 9.5h4a1.5 1.5 0 0 1 0 3h-3a1.5 1.5 0 0 0 0 3h4" /></svg>;
  return <svg {...common}><path d="M3 17l6-6 4 4 8-8" /><path d="M17 7h4v4" /></svg>;
}
