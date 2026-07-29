"use client";

import Link from "next/link";
import { useState } from "react";
import Tilt from "@/components/3d/Tilt";
import BrowserShowcase from "@/components/BrowserShowcase";

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
  { label: "Security", href: "#security" },
  { label: "Pricing", href: "#pricing" },
  { label: "FAQ", href: "#faq" },
];

export default function Landing() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [annualBilling, setAnnualBilling] = useState(true);
  const [openFaq, setOpenFaq] = useState<number | null>(0);

  const faqs = [
    {
      q: "Is it safe? Do you need my Amazon password?",
      a: "ScoutVeda connects using Amazon's official Selling Partner API (SP-API) via OAuth 2.0. We never see or store your Amazon password. You approve read-only access directly on Amazon's official site.",
    },
    {
      q: "Can Amazon suspend my seller account for connecting?",
      a: "No. ScoutVeda uses standard Amazon LWA read-only scopes. We do not place automated orders or execute restricted inventory operations. Access can be revoked anytime with one click.",
    },
    {
      q: "Can I explore ScoutVeda before connecting my seller account?",
      a: "Yes! You get full access to our product database, keyword harvester, and profit calculator immediately upon sign up. Connecting your Seller Central account is an optional upgrade to unlock live storefront sales sync.",
    },
    {
      q: "What data does ScoutVeda sync from my storefront?",
      a: "We sync order metrics, sales revenue totals, units sold, and inventory health flags over a 14-day rolling period. We never share, sell, or benchmark your private storefront data with third parties.",
    },
  ];

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
            <Link href="/signup" className="sv-btn sv-btn-primary">Start free</Link>
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
            <span className="sv-eyebrow">The Operating System for Amazon Sellers</span>
            <h1 className="sv-h1">Run your Amazon business with total confidence.</h1>
            <p className="sv-lede">
              Research products, calculate real net margins, monitor keywords, and sync storefront sales in one secure workspace.
            </p>
            <div className="sv-hero-cta">
              <Link href="/signup" className="sv-btn sv-btn-primary sv-btn-lg">Start Free Research</Link>
              <a href="#how" className="sv-btn sv-btn-ghost sv-btn-lg">See How It Works</a>
            </div>
            <div className="sv-hero-trust flex items-center gap-2 text-xs text-zinc-400 mt-4">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--sv-teal)" strokeWidth="2"><path d="M20 6 9 17l-5-5" /></svg>
              Built on Amazon&apos;s Official SP-API OAuth · Read-only access · Revoke anytime
            </div>
          </div>

          <HeroPreview />
        </div>
      </section>

      {/* PROBLEM / VALUE */}
      <section id="research" className="sv-wrap sv-section">
        <div className="sv-section-head">
          <span className="sv-eyebrow">The Sourcing Challenge</span>
          <h2 className="sv-h2">Sourcing gets expensive when decisions are guesswork.</h2>
          <p className="sv-sub">Buying inventory on a hunch ties up capital in slow-moving products. ScoutVeda gives you the exact numbers before you buy.</p>
        </div>
        <div className="sv-value-grid">
          {[
            { t: "Discover High-Margin Niche Products", d: "Surface uncrowded opportunities across categories instead of scrolling bestseller lists by hand.", i: "search" },
            { t: "Evaluate Incumbent Competition", d: "See review depth, price stability, and seller entrenchment before committing a single rupee.", i: "shield" },
            { t: "Calculate Real FBA Net Profit", d: "Model Amazon Easy Ship, FBA referral fees, GST (18%), and closing fees up front.", i: "coin" },
            { t: "Track Rank & Sales Trends", d: "Watch product demand velocity — climbing, stable, seasonal, or fading.", i: "trend" },
          ].map((v) => (
            <div key={v.t} className="sv-glass sv-value">
              <div className="ic"><Icon name={v.i} /></div>
              <div><h3>{v.t}</h3><p>{v.d}</p></div>
            </div>
          ))}
        </div>
      </section>

      {/* HOW IT WORKS (3-STEP VISUAL DIAGRAM) */}
      <section id="how" className="sv-wrap sv-section" style={{ paddingTop: 0 }}>
        <div className="sv-section-head">
          <span className="sv-eyebrow">How Connection Works</span>
          <h2 className="sv-h2">Three simple steps to unlock your seller cockpit.</h2>
        </div>
        <div className="sv-steps">
          {[
            { n: "1", t: "1. Authorize on Amazon", d: "Click 'Connect' on ScoutVeda. You are redirected to Seller Central to log in and approve read-only permissions on Amazon's site." },
            { n: "2", t: "2. We Sync Read-Only Data", d: "ScoutVeda's 4-wave sync engine securely backfills order metrics, sales totals, and inventory health without touching your password." },
            { n: "3", t: "3. Actionable Insights", d: "Your personalized dashboard populates with live sales trends, stockout alerts, and AI next actions." },
          ].map((s) => (
            <div key={s.n} className="sv-glass sv-step">
              <div className="sv-step-n">{s.n}</div>
              <h3>{s.t}</h3>
              <p>{s.d}</p>
            </div>
          ))}
        </div>
      </section>

      {/* DEDICATED SECURITY BLOCK */}
      <section id="security" className="sv-wrap sv-section" style={{ paddingTop: 0 }}>
        <div className="sv-glass p-8 rounded-2xl border border-emerald-500/20 bg-emerald-500/5 backdrop-blur-md">
          <div className="max-w-2xl mb-8">
            <span className="sv-eyebrow text-emerald-400">Trust & Security</span>
            <h2 className="sv-h2 text-white mt-1">Trust is the product. Enterprise security at every layer.</h2>
            <p className="sv-sub text-zinc-400 mt-2">
              We handle your storefront tokens and financial data with the highest security standards.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[
              { title: "Fernet Token Encryption", desc: "Refresh tokens are encrypted at rest using AES-128 Fernet keys." },
              { title: "OAuth 2.0 Protocol", desc: "Your Amazon password never touches ScoutVeda servers." },
              { title: "Least-Privilege Scopes", desc: "We request only the minimum read-only permissions needed." },
              { title: "Instant Revocation", desc: "One-click disconnect deletes stored credentials immediately." },
            ].map((sec) => (
              <div key={sec.title} className="p-4 rounded-xl bg-white/[0.03] border border-white/10">
                <div className="text-xs font-bold text-emerald-400 mb-1">{sec.title}</div>
                <div className="text-[11px] text-zinc-400 leading-relaxed">{sec.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* PRICING SECTION */}
      <section id="pricing" className="sv-wrap sv-section" style={{ paddingTop: 0 }}>
        <div className="sv-section-head">
          <span className="sv-eyebrow">Transparent Pricing</span>
          <h2 className="sv-h2">Plans that scale with your Amazon business.</h2>
          <div className="flex items-center justify-center gap-3 mt-4">
            <span className={`text-xs font-semibold ${!annualBilling ? "text-white" : "text-zinc-500"}`}>Monthly</span>
            <button
              onClick={() => setAnnualBilling(!annualBilling)}
              className="relative w-12 h-6 rounded-full bg-emerald-500/20 p-1 transition-colors border border-emerald-500/40"
            >
              <div className={`w-4 h-4 rounded-full bg-emerald-400 transition-transform ${annualBilling ? "translate-x-6" : ""}`} />
            </button>
            <span className={`text-xs font-semibold ${annualBilling ? "text-emerald-400" : "text-zinc-500"}`}>
              Annual <span className="bg-emerald-500/20 text-emerald-300 text-[10px] px-2 py-0.5 rounded-full border border-emerald-500/30">Save 35%</span>
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
          {[
            {
              name: "Starter",
              price: annualBilling ? "₹1,499" : "₹2,299",
              desc: "Perfect for new resellers researching their first products.",
              features: ["1 Connected Storefront", "100 ASIN Validations/mo", "Basic Margin Calculator", "Daily Keyword Tracking"],
              cta: "Start Free Trial",
              popular: false,
            },
            {
              name: "Pro Reseller",
              price: annualBilling ? "₹2,999" : "₹4,499",
              desc: "For active Amazon sellers scaling inventory & PPC.",
              features: ["3 Connected Storefronts", "Unlimited Validations", "FBA Fee & Tax Breakdown", "Real-Time Stockout Alerts", "Competitor Review Miner"],
              cta: "Get Pro Access",
              popular: true,
            },
            {
              name: "Agency & Brand",
              price: annualBilling ? "₹6,999" : "₹9,999",
              desc: "For agencies managing multiple Amazon seller accounts.",
              features: ["10 Connected Storefronts", "Multi-Workspace Access", "Custom Export Reports", "Dedicated Account Manager", "API Data Access"],
              cta: "Contact Sales",
              popular: false,
            },
          ].map((plan) => (
            <div
              key={plan.name}
              className={`sv-glass p-6 rounded-2xl flex flex-col justify-between relative ${
                plan.popular ? "border-emerald-500/50 bg-emerald-500/[0.06] ring-1 ring-emerald-500/30" : ""
              }`}
            >
              {plan.popular && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-emerald-500 text-black text-[10px] font-bold uppercase tracking-wider px-3 py-0.5 rounded-full">
                  Most Popular
                </span>
              )}
              <div>
                <h3 className="text-base font-bold text-white">{plan.name}</h3>
                <p className="text-xs text-zinc-400 mt-1">{plan.desc}</p>
                <div className="my-5">
                  <span className="text-3xl font-extrabold text-white">{plan.price}</span>
                  <span className="text-xs text-zinc-500 font-medium"> / month</span>
                </div>
                <ul className="space-y-2 text-xs text-zinc-300">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-center gap-2">
                      <span className="text-emerald-400 font-bold">✓</span> {f}
                    </li>
                  ))}
                </ul>
              </div>
              <Link
                href="/signup"
                className={`sv-btn mt-6 w-full text-center ${plan.popular ? "sv-btn-primary" : "sv-btn-ghost"}`}
              >
                {plan.cta}
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* FAQ SECTION */}
      <section id="faq" className="sv-wrap sv-section" style={{ paddingTop: 0 }}>
        <div className="sv-section-head">
          <span className="sv-eyebrow">Frequently Asked Questions</span>
          <h2 className="sv-h2">Answers to your top questions.</h2>
        </div>
        <div className="max-w-2xl mx-auto space-y-3 mt-6">
          {faqs.map((faq, idx) => (
            <div key={idx} className="sv-glass rounded-xl overflow-hidden border border-white/10">
              <button
                onClick={() => setOpenFaq(openFaq === idx ? null : idx)}
                className="w-full p-4 text-left font-semibold text-xs text-white flex justify-between items-center"
              >
                <span>{faq.q}</span>
                <span className="text-emerald-400 font-bold">{openFaq === idx ? "−" : "+"}</span>
              </button>
              {openFaq === idx && (
                <div className="px-4 pb-4 text-xs text-zinc-400 leading-relaxed border-t border-white/5 pt-3">
                  {faq.a}
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* FEEDBACK & SUGGESTIONS */}
      <section id="feedback" className="sv-wrap sv-section" style={{ paddingTop: 0, paddingBottom: "40px" }}>
        <div className="sv-glass p-6 md:p-8 rounded-2xl flex flex-col md:flex-row items-center justify-between gap-6 border-l-4 border-l-amber-500 border-t border-r border-b border-black/5 bg-gradient-to-br from-amber-500/5 to-white/70 backdrop-blur-md shadow-sm">
          <div className="max-w-lg text-left">
            <span className="sv-eyebrow" style={{ color: "#d97706" }}>Feedback & Suggestions</span>
            <h2 className="text-lg font-bold text-zinc-900 mt-1" style={{ fontSize: "1.25rem" }}>Help us shape the future of ScoutVeda</h2>
            <p className="text-xs text-zinc-650 leading-relaxed mt-2 font-semibold">
              Have suggestions, feature requests, or encountered a bug? We iterate fast based on seller input. Reach out directly via Email or WhatsApp.
            </p>
          </div>
          <div className="flex flex-wrap gap-3 shrink-0">
            <a
              href="mailto:rameshknk143@gmail.com?subject=ScoutVeda Feedback & Suggestions"
              className="sv-btn sv-btn-ghost flex items-center gap-2 text-xs py-2.5 px-4 border border-black/10 hover:bg-zinc-50 cursor-pointer shadow-sm rounded-lg"
              style={{ padding: "10px 16px", fontSize: "11px", fontWeight: "bold" }}
            >
              ✉️ Email Suggestions
            </a>
            <a
              href="https://wa.me/919900000000?text=Hi%20Ram,%20I%20have%20some%20feedback/suggestions%20for%20ScoutVeda..."
              target="_blank"
              rel="noopener noreferrer"
              className="sv-btn sv-btn-primary flex items-center gap-2 text-xs py-2.5 px-4 bg-emerald-600 hover:bg-emerald-700 text-white cursor-pointer shadow-sm rounded-lg border border-emerald-700/10"
              style={{ padding: "10px 16px", fontSize: "11px", fontWeight: "bold", background: "#10b981" }}
            >
              💬 WhatsApp Chat
            </a>
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
              <a href="#security">Security</a>
              <a href="#faq">FAQ</a>
              <a href="#feedback">Feedback</a>
              <a href="mailto:rameshknk143@gmail.com">Support</a>
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

function HeroPreview() {
  return (
    <Tilt className="relative w-full max-w-[620px] mx-auto py-10">
      <BrowserShowcase />
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
