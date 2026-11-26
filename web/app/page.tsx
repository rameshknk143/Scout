"use client";

import Link from "next/link";
import { useState, useEffect, useRef } from "react";
import HeroCockpit from "@/components/HeroCockpit";
import { ThemeToggle } from "@/components/ThemeToggle";

/**
 * ScoutVeda landing page — ported exactly from the homepage prototype
 * (artifact scoutveda-homepage, latest version, 26 Nov 2026), the version
 * Boss saw and asked to "upload this on the main site.. without flickering
 * any kind of colouring different and ui difference".
 *
 * What this port is, and is not:
 * - Hero copy, cockpit, fee waterfall, features, explorer, calculator,
 *   how-it-works, security, pricing, compare, FAQ, final CTA and footer
 *   all follow the artifact's copy, order, colours and layout.
 * - No fake elements: no standalone "82" OpportunityDial ring, no
 *   BrowserShowcase carousel (deleted), no weird 3D phone (removed from
 *   the artifact after Boss called it weird — it is not here either).
 * - Demo data is labelled demo; sales figures are labelled estimates.
 * - Functional links stay live: Log in -> /login, Start free trial ->
 *   /signup. Pricing trial buttons are mailto: as in the artifact —
 *   trial access is arranged by mail while the Amazon public app is
 *   pending. No billing, no WhatsApp, no invented testimonials.
 * - Margin fix: the phone-case demo record used to say 38.2% (PR #4).
 *   ₹207 / ₹499 = 41.5%, which is what the calculator shows. Fixed here.
 *
 * No-flicker notes:
 * - Theme is set before paint by ThemeBootstrapScript in layout.tsx;
 *   the glass colours below are keyed to [data-theme], the same system
 *   the live site already uses — not prefers-color-scheme on its own.
 * - Scroll reveals only hide elements AFTER JS mounts
 *   (html.sv-reveal-ready). Before that, and with JS off, everything
 *   is visible — the page can never load blank.
 * - Smooth scrolling is pure CSS (scroll-behavior: smooth in
 *   globals.css); anchor links are plain <a href="#…"> so the browser
 *   handles the glide, with no JS scroll hijack.
 */

function Wordmark() {
  return (
    <Link href="/" className="sv-mark" aria-label="ScoutVeda Home">
      <span className="sv-mark-dot" aria-hidden="true" />
      Scout<b>Veda</b>
    </Link>
  );
}

// Artifact nav order.
const NAV = [
  { label: "Features", href: "#features" },
  { label: "Product Research", href: "#research" },
  { label: "Profit Calculator", href: "#calculator" },
  { label: "How It Works", href: "#how" },
  { label: "Security", href: "#security" },
  { label: "Pricing", href: "#pricing" },
  { label: "FAQ", href: "#faq" },
];

export default function Landing() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [annualBilling, setAnnualBilling] = useState(true);
  const [explorerIdx, setExplorerIdx] = useState(0);
  const [calcPrice, setCalcPrice] = useState(499);
  const [calcCost, setCalcCost] = useState(200);
  const [scrolled, setScrolled] = useState(false);
  const revealRef = useRef<HTMLDivElement>(null);

  // Apple-style scroll reveals + smooth-scroll safety net.
  // Runs once on mount: marks the page reveal-ready (only then do
  // .sv-reveal elements start hidden), then an IntersectionObserver
  // adds .in as each element scrolls into view. Reduced-motion or no
  // IntersectionObserver -> everything is shown immediately.
  useEffect(() => {
    const root = document.documentElement;
    root.classList.add("sv-reveal-ready");
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const scope = revealRef.current;
    if (!scope) return;
    // Stagger children of reveal groups, as in the artifact.
    scope.querySelectorAll(".sv-reveal-group").forEach((g) => {
      Array.from(g.children).forEach((c, i) => {
        (c as HTMLElement).classList.add("sv-rv-item");
        (c as HTMLElement).style.setProperty("--d", String(Math.min(i, 6)));
      });
    });
    const targets = Array.from(scope.querySelectorAll(".sv-reveal, .sv-rv-item"));
    if (reduced || !("IntersectionObserver" in window)) {
      targets.forEach((el) => el.classList.add("in"));
      return;
    }
    const ob = new IntersectionObserver(
      (entries) => {
        entries.forEach((en) => {
          if (en.isIntersecting) {
            en.target.classList.add("in");
            ob.unobserve(en.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -6% 0px" }
    );
    targets.forEach((el) => ob.observe(el));
    return () => ob.disconnect();
  }, []);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const faqs = [
    {
      q: "How does the 30-day free trial work?",
      a: "The launch offer is a 30-day free trial, no card needed. Trial access is arranged by mail at support@scoutveda.com while the Amazon public app is pending — write to us and we will confirm the start. If you continue, pick Starter, Pro Reseller or Agency — monthly or annual.",
    },
    {
      q: "Is my seller account safe?",
      a: "ScoutVeda is designed to connect read-only via Amazon SP-API OAuth, so it cannot change listings, prices or orders. That public connection is not available yet — the current app is private/draft and pending a new public app.",
    },
    {
      q: "Are sales numbers exact?",
      a: "No — and we will never claim they are. Monthly sales are labelled estimates, based on BSR and category signals. Fees and margins use the published Amazon.in fee tables.",
    },
    {
      q: "Does it work for Flipkart?",
      a: "Not yet. ScoutVeda is India-first, with Amazon.in as the core today. There is no Flipkart API app yet — Flipkart support is on the roadmap, not live.",
    },
    {
      q: "How do I get help?",
      a: "By mail only — write to support@scoutveda.com and we will reply there. There is no WhatsApp support.",
    },
  ];

  const plans = [
    {
      name: "Starter",
      desc: "For new & individual sellers",
      annual: "₹1,499",
      monthly: "₹2,299",
      features: [
        "Product research & Opportunity Score",
        "Profit calculator with India fees",
        "Track up to 50 ASINs — roadmap",
        "Mail support",
      ],
      cta: "Start 30-day trial",
      popular: false,
      mail: "ScoutVeda%20Starter%20trial",
    },
    {
      name: "Pro Reseller",
      desc: "For growing resellers & SMBs",
      annual: "₹2,999",
      monthly: "₹4,499",
      features: [
        "Everything in Starter",
        "Track up to 500 ASINs — roadmap",
        "Competitor & price-drop alerts — roadmap",
        "Flipkart research — on the roadmap",
        "Priority mail support",
      ],
      cta: "Start 30-day trial",
      popular: true,
      mail: "ScoutVeda%20Pro%20trial",
    },
    {
      name: "Agency",
      desc: "For agencies & multi-store teams",
      annual: "₹6,499",
      monthly: "₹9,999",
      features: [
        "Everything in Pro",
        "Multi-store tracking — roadmap",
        "Team seats & bulk research",
        "Priority mail support",
      ],
      cta: "Start 30-day trial",
      popular: false,
      mail: "ScoutVeda%20Agency%20trial",
    },
  ];

  // Demo explorer products — exactly as in the artifact Boss approved.
  // All three are labelled demo data on the page; the phone case is the
  // verified record (₹499, BSR #1,240, 4.3★, 7 sellers). The bottle and
  // lamp are demo illustrations in the artifact, not verified records —
  // do not present them as verified, and do not add products back
  // without verified price / BSR / rating / fee figures.
  const demoProducts = [
    { name: "Phone Case — iPhone 17, Grey", cat: "Cases, Covers & Skins", price: 499, bsr: 1240, rating: "4.3 ★ (2,184)", sellers: 7, est: "1,240 / mo*", score: 86, margin: "41.5%", verdict: "Strong demand, referral 0% at this price, healthy margin after Easy Ship fees. The same product shown in the hero above." },
    { name: "Stainless Steel Bottle — 1 Litre", cat: "Kitchen & Dining", price: 699, bsr: 3810, rating: "4.4 ★ (5,902)", sellers: 14, est: "860 / mo*", score: 74, margin: "29.6%", verdict: "Steady category, more competition. Win on bundle or colour variants." },
    { name: "LED Study Lamp — Rechargeable", cat: "Home & Kitchen", price: 899, bsr: 6920, rating: "4.1 ★ (1,340)", sellers: 22, est: "410 / mo*", score: 58, margin: "21.4%", verdict: "Crowded and price-sensitive. Only enter with a clear feature edge." },
  ];
  const demo = demoProducts[explorerIdx];

  // Verified Amazon.in Easy Ship calculator (artifact logic): referral 0%
  // ≤ ₹1,000 (25% above) for Cases/Covers-type categories, closing by
  // price band, ₹55 shipping, 18% GST on fees.
  const calcReferral = calcPrice <= 1000 ? 0 : calcPrice * 0.25;
  const calcClosing = calcPrice <= 300 ? 2 : calcPrice <= 500 ? 23 : calcPrice <= 1000 ? 48 : 79;
  const calcShipping = 55;
  const calcGst = (calcReferral + calcClosing + calcShipping) * 0.18;
  const calcFees = calcReferral + calcClosing + calcShipping + calcGst;
  const calcPayout = calcPrice - calcFees;
  const calcProfit = calcPayout - calcCost;
  const calcMargin = calcPrice ? (calcProfit / calcPrice) * 100 : 0;
  const inr = (n: number) => "₹" + Math.round(n).toLocaleString("en-IN");

  return (
    <div className="sv-page" ref={revealRef}>
      {/* Animated background grid */}
      <div className="sv-bg" aria-hidden="true">
        <div className="sv-grid-perspective">
          <div className="sv-grid-plane" />
        </div>
      </div>

      {/* Header — floating pill nav, as in the artifact */}
      <header className={`sv-header ${scrolled ? "sv-header--scrolled" : ""}`}>
        <div className="sv-wrap sv-header-inner">
          <Wordmark />
          <nav className="sv-nav" aria-label="Primary">
            {NAV.map((n) => (
              <a key={n.href} href={n.href}>{n.label}</a>
            ))}
          </nav>
          <div className="sv-header-cta">
            <ThemeToggle />
            <Link href="/login" className="sv-btn sv-btn-ghost sv-hide-sm">Log in</Link>
            <Link href="/signup" className="sv-btn sv-btn-primary">Start free trial</Link>
            <button
              className="sv-burger"
              aria-label="Menu"
              aria-expanded={menuOpen}
              onClick={() => setMenuOpen((v) => !v)}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                {menuOpen ? (<><path d="M18 6 6 18" /><path d="M6 6l12 12" /></>) : (<><path d="M3 6h18" /><path d="M3 12h18" /><path d="M3 18h18" /></>)}
              </svg>
            </button>
          </div>
        </div>
        {menuOpen && (
          <div className="sv-mobile-menu" style={{ display: "flex" }}>
            {NAV.map((n) => (
              <a key={n.href} href={n.href} onClick={() => setMenuOpen(false)}>{n.label}</a>
            ))}
            <a href="/login">Log in</a>
          </div>
        )}
      </header>

      <main id="top">
        {/* HERO — artifact copy, centred, clean cockpit below */}
        <section className="sv-wrap sv-hero">
          <div className="sv-hero-grid">
            <div className="sv-reveal">
              <span className="sv-art-pill">New&nbsp;<b>30-day free trial — no card needed</b></span>
              <h1 className="sv-h1">
                Find winning products<br />on Amazon.in — before<br />you spend a rupee.
              </h1>
              <p className="sv-lede">
                ScoutVeda turns any ASIN into one complete record — price, BSR, demand, competition, true Amazon.in fees and your real margin — so the decision takes seconds, not spreadsheets. Demo data below.
              </p>
              <div className="sv-hero-cta">
                <Link href="/signup" className="sv-btn sv-btn-primary sv-btn-lg">Start your 30-day free trial</Link>
                <Link href="/login" className="sv-btn sv-btn-ghost sv-btn-lg">Log in</Link>
                <a href="#research" className="sv-btn sv-btn-ghost sv-btn-lg">See it in action ›</a>
              </div>
              <p className="sv-hero-note">
                For beginners, resellers, SMBs and agencies in India · Amazon.in first, Flipkart on the roadmap · Designed for a read-only, secure connection
              </p>
              <div className="sv-art-jump" aria-label="Jump to a section">
                <a href="#features">Features</a><a href="#research">Product Research</a><a href="#calculator">Profit Calculator</a><a href="#how">How It Works</a><a href="#security">Security</a><a href="#pricing">Pricing</a>
              </div>
            </div>
            <HeroCockpit />
          </div>
        </section>

        {/* STRIP */}
        <div className="sv-wrap sv-reveal" style={{ marginTop: 8 }}>
          <div className="sv-ios-strip">
            <span><b>₹1,499/mo</b> on annual — vs ~₹9,000+ for international tools</span>
            <span><b>India-first</b> fees &amp; pricing</span>
            <span><b>Designed for read-only</b> SP-API access</span>
            <span><b>Mail support</b> support@scoutveda.com</span>
          </div>
        </div>

        {/* FEATURES — artifact */}
        <section id="features" className="sv-wrap sv-section">
          <div className="sv-section-head sv-ios-center">
            <span className="sv-eyebrow sv-reveal">Why ScoutVeda</span>
            <h2 className="sv-h2 sv-reveal">Everything you need.<br />Nothing you overpay for.</h2>
            <p className="sv-sub sv-reveal">Helium 10 power, without the dollar pricing. Built for how Indian sellers actually sell — Easy Ship, FBA, and real Amazon.in fees.</p>
          </div>

          <div className="sv-art-grid sv-reveal-group">
            <article className="sv-art-card">
              <h3>One ASIN. One complete record.</h3>
              <p>No scattered tabs. Everything ScoutVeda knows about a product sits in one record — and the Opportunity Score is simply the last line of it, not a mystery number floating on its own.</p>
              <div className="sv-art-record" aria-label="Complete demo product record">
                <div><span>Price</span><b>₹499</b></div>
                <div><span>BSR · Cases &amp; Covers</span><b>#1,240</b></div>
                <div><span>Rating / reviews</span><b>4.3 ★ · 2,184</b></div>
                <div><span>Sellers</span><b>7</b></div>
                <div><span>Est. monthly sales*</span><b>1,240 units</b></div>
                <div><span>Net margin (after all fees)</span><b>41.5%</b></div>
                <div className="sv-art-score-row"><span>Opportunity Score</span><b>86 / 100 — Strong</b></div>
              </div>
            </article>
            <article className="sv-art-card sv-art-bluebg">
              <h3>True profit.<br />Down to the rupee.</h3>
              <p>Referral, closing, shipping and GST on fees — calculated with the current Amazon.in schedule. No more 18% referral surprises on cases under ₹1,000, where referral is now 0%.</p>
              <ul className="sv-art-mini-list">
                <li>0% referral up to ₹1,000 on eligible categories</li>
                <li>Easy Ship &amp; FBA fee tables built in</li>
                <li>Try it yourself in the calculator below</li>
              </ul>
            </article>
          </div>

          <div className="sv-art-grid2 sv-reveal-group">
            <article className="sv-art-card">
              <h3>How the score is earned.</h3>
              <p>The 86 above is a weighted blend of three things you can check yourself — never a black box.</p>
              <div className="sv-art-score-parts">
                <div><label>Demand <span>BSR #1,240 and rising</span></label><div className="sv-art-progress g"><i style={{ width: "88%" }} /></div></div>
                <div><label>Low competition <span>Only 7 sellers</span></label><div className="sv-art-progress"><i style={{ width: "79%" }} /></div></div>
                <div><label>Margin health <span>41.5% after fees</span></label><div className="sv-art-progress a"><i style={{ width: "83%" }} /></div></div>
              </div>
            </article>
            <article className="sv-art-card sv-art-darkbg">
              <h3>Simple by design.</h3>
              <p>No 40-tool maze. One place for research, profit and tracking — made to be understood on day one, in minutes. Accuracy, reliability and usability over complexity, every time.</p>
              <p className="sv-art-bigline">Research → Calculate → Launch → Track</p>
              <p className="sv-art-small">Competitor tracking and alerts are on the roadmap — planned, not live yet.</p>
            </article>
          </div>
        </section>

        {/* RESEARCH EXPLORER — artifact */}
        <section id="research" className="sv-wrap sv-section" style={{ paddingTop: 20 }}>
          <div className="sv-section-head sv-ios-center">
            <span className="sv-eyebrow sv-reveal">Product Research</span>
            <h2 className="sv-h2 sv-reveal">Tap a product.<br />See the whole picture.</h2>
            <p className="sv-sub sv-reveal">Three demo products, three very different answers. Demo data only — live seller connection for other sellers is pending Amazon public-app approval, so you cannot connect an account yet.</p>
          </div>
          <div className="sv-ios-explorer sv-reveal">
            <div className="sv-ios-asin-list">
              {demoProducts.map((p, i) => (
                <button key={p.name} type="button" onClick={() => setExplorerIdx(i)}
                  className={`sv-ios-asin-btn${i === explorerIdx ? " active" : ""}`}>
                  <span><strong>{p.name}</strong><span className="sv-ios-asin-sub">{p.cat} · ₹{p.price} · BSR #{p.bsr.toLocaleString("en-IN")}</span></span>
                  <span className="sv-ios-score">{p.score}</span>
                </button>
              ))}
            </div>
            <div className="sv-ios-detail">
              <span className="sv-ios-detail-eyebrow">OPPORTUNITY SCORE {demo.score} / 100</span>
              <h3>{demo.name}</h3>
              <p className="sv-ios-detail-verdict">{demo.verdict}</p>
              <div className="sv-ios-detail-grid">
                <div><span>Price</span><strong>₹{demo.price}</strong></div>
                <div><span>BSR</span><strong>#{demo.bsr.toLocaleString("en-IN")}</strong></div>
                <div><span>Rating / Reviews</span><strong>{demo.rating}</strong></div>
                <div><span>Sellers</span><strong>{demo.sellers}</strong></div>
                <div><span>Est. monthly sales*</span><strong>{demo.est}</strong></div>
                <div><span>Net margin</span><strong style={{ color: "#30d158" }}>{demo.margin}</strong></div>
              </div>
              <p className="sv-ios-note">*Estimate only. Category: {demo.cat}</p>
            </div>
          </div>
        </section>

        {/* PROFIT CALCULATOR — artifact */}
        <section id="calculator" className="sv-wrap sv-section" style={{ paddingTop: 20 }}>
          <div className="sv-section-head sv-ios-center">
            <span className="sv-eyebrow sv-reveal">Profit Calculator</span>
            <h2 className="sv-h2 sv-reveal">Know your margin<br />before you buy stock.</h2>
            <p className="sv-sub sv-reveal">Move the sliders. This working demo uses Amazon.in Easy Ship logic — referral, closing fee, shipping and GST on fees.</p>
          </div>
          <div className="sv-ios-calc sv-reveal">
            <div>
              <label className="sv-ios-label">Selling price <span className="sv-ios-val">{inr(calcPrice)}</span>
                <input type="range" min={199} max={1999} step={10} value={calcPrice} onChange={(e) => setCalcPrice(Number(e.target.value))} aria-label="Selling price" />
              </label>
              <label className="sv-ios-label">Your buying cost <span className="sv-ios-val">{inr(calcCost)}</span>
                <input type="range" min={50} max={1200} step={10} value={calcCost} onChange={(e) => setCalcCost(Number(e.target.value))} aria-label="Your buying cost" />
              </label>
              <p className="sv-ios-note"><b>Fee basis:</b> Referral 0% up to ₹1,000 (25% above) for Cases/Covers-type categories, closing fee by price band, Easy Ship ₹55 for first 500g, plus 18% GST on Amazon fees. Verified against Amazon.in fee schedule, Nov 2025. Other categories vary — ScoutVeda applies the right category table live.</p>
            </div>
            <div className="sv-ios-result">
              <div className="sv-ios-row"><span>Selling price</span><b>{inr(calcPrice)}</b></div>
              <div className="sv-ios-row"><span>Referral fee</span><span>{calcReferral === 0 ? "₹0 (0% up to ₹1,000)" : inr(calcReferral)}</span></div>
              <div className="sv-ios-row"><span>Closing fee (Easy Ship)</span><span>{inr(calcClosing)}</span></div>
              <div className="sv-ios-row"><span>Shipping — first 500g</span><span>{inr(calcShipping)}</span></div>
              <div className="sv-ios-row"><span>GST 18% on Amazon fees</span><span>{inr(calcGst)}</span></div>
              <div className="sv-ios-row"><span>Your buying cost</span><span>{inr(calcCost)}</span></div>
              <div className="sv-ios-row total"><span>Net profit</span><span style={{ color: calcProfit >= 0 ? "#1a7f37" : "#d70015" }}>{inr(calcProfit)}</span></div>
              <p className="sv-ios-note">Margin: <b>{calcMargin.toFixed(1)}%</b> · Estimated payout from Amazon: <b>{inr(calcPayout)}</b> before your cost. TCS 0.5% &amp; TDS 0.1% are withheld from payout but are not a lost cost.</p>
            </div>
          </div>
        </section>

        {/* HOW IT WORKS — artifact */}
        <section id="how" className="sv-wrap sv-section" style={{ paddingTop: 20 }}>
          <div className="sv-section-head sv-ios-center">
            <span className="sv-eyebrow sv-reveal">How It Works</span>
            <h2 className="sv-h2 sv-reveal">From ASIN to decision<br />in three steps.</h2>
          </div>
          <div className="sv-art-steps sv-reveal-group">
            <div className="sv-art-step"><div className="sv-art-step-num">1</div><h3>Paste an ASIN</h3><p>ScoutVeda builds the complete record — price, BSR, rating, sellers, fees and estimated sales*.</p></div>
            <div className="sv-art-step"><div className="sv-art-step-num">2</div><h3>Check true profit</h3><p>Add your buying cost and see net profit after real Amazon.in fees — before you order stock.</p></div>
            <div className="sv-art-step"><div className="sv-art-step-num">3</div><h3>Decide &amp; track</h3><p>Shortlist winners by Opportunity Score. Roadmap: price, BSR and restock alerts once tracking goes live.</p></div>
          </div>
          <p className="sv-sub sv-reveal" style={{ fontSize: 14, marginTop: 22 }}>Account connection comes when the Amazon public app is approved — designed read-only via SP-API OAuth, so ScoutVeda can never change your listings, prices or orders.</p>
        </section>

        {/* SECURITY — artifact */}
        <section id="security" className="sv-wrap sv-section" style={{ paddingTop: 20 }}>
          <div className="sv-section-head sv-ios-center">
            <span className="sv-eyebrow sv-reveal">Security</span>
            <h2 className="sv-h2 sv-reveal">Your seller account<br />stays yours.</h2>
            <p className="sv-sub sv-reveal">ScoutVeda is built to look, not to touch. Here is exactly what that means — including what is not live yet.</p>
          </div>
          <div className="sv-art-steps sv-reveal-group">
            <div className="sv-art-step"><h3>Read-only by design</h3><p>The connection is designed around Amazon SP-API OAuth with read-only access — ScoutVeda cannot change your listings, prices, orders or payouts.</p></div>
            <div className="sv-art-step"><h3>No password, ever</h3><p>You would sign in on Amazon&apos;s own page and grant access there. ScoutVeda never sees or stores your Amazon password.</p></div>
            <div className="sv-art-step"><h3>Honest about status</h3><p>That public connection is not live yet — the current app is private/draft, pending a new public app. Until then, everything on this page is clearly labelled demo data, and sales figures are always labelled estimates.</p></div>
          </div>
          <p className="sv-sub sv-reveal" style={{ fontSize: 14, marginTop: 22 }}>Questions about security? Mail us at <a href="mailto:support@scoutveda.com">support@scoutveda.com</a> — support is by mail only.</p>
        </section>

        {/* PRICING — artifact */}
        <section id="pricing" className="sv-wrap sv-section" style={{ paddingTop: 20 }}>
          <div className="sv-section-head sv-ios-center">
            <span className="sv-eyebrow sv-reveal">Pricing</span>
            <h2 className="sv-h2 sv-reveal">India pricing.<br />Honest and simple.</h2>
            <p className="sv-sub sv-reveal">Launch pricing: start with a 30-day free trial, no card needed, arranged by mail while the public app is pending. Annual billing saves you up to 35%.</p>
            <div className="sv-art-toggle-wrap">
              <div className="sv-art-toggle" role="group" aria-label="Billing period">
                <button type="button" className={annualBilling ? "active" : ""} onClick={() => setAnnualBilling(true)}>Annual — save up to 35%</button>
                <button type="button" className={!annualBilling ? "active" : ""} onClick={() => setAnnualBilling(false)}>Monthly</button>
              </div>
            </div>
            <p className="sv-art-save">{annualBilling ? "Annual prices shown, billed yearly." : "Monthly prices shown, billed monthly."}</p>
          </div>
          <div className="sv-art-prices sv-reveal-group">
            {plans.map((plan) => (
              <article key={plan.name} className={`sv-art-price-card${plan.popular ? " featured" : ""}`}>
                {plan.popular && <span className="sv-art-badge">MOST POPULAR</span>}
                <h3>{plan.name}</h3>
                <p>{plan.desc}</p>
                <div className="sv-art-price"><span>{annualBilling ? plan.annual : plan.monthly}</span><small>/month</small></div>
                <ul>
                  {plan.features.map((f) => (
                    <li key={f}>✓ {f}</li>
                  ))}
                </ul>
                <a className={`sv-btn ${plan.popular ? "sv-btn-primary" : "sv-btn-ghost"} sv-btn-sm`} href={`mailto:support@scoutveda.com?subject=${plan.mail}`} style={{ width: "100%" }}>{plan.cta}</a>
              </article>
            ))}
          </div>

          <div className="sv-ios-compare sv-reveal">
            <div className="sv-ios-compare-row head"><span>Compare</span><span>ScoutVeda</span><span>Helium 10 Platinum</span></div>
            <div className="sv-ios-compare-row"><span>Starting price</span><b>₹1,499 / mo*</b><span>$99–$129 / mo</span></div>
            <div className="sv-ios-compare-row"><span>Built for</span><span>Amazon.in sellers</span><span>US / global first</span></div>
            <div className="sv-ios-compare-row"><span>India fee accuracy</span><span>✓ Built-in</span><span>Manual check needed</span></div>
            <div className="sv-ios-compare-row"><span>Free trial</span><span>30 days, no card</span><span>Varies</span></div>
          </div>
          <p className="sv-ios-note" style={{ textAlign: "center" }}>*Annual billing. Helium 10 pricing verified Nov 2025: Platinum $129/mo monthly, $99/mo yearly.</p>
        </section>

        {/* FAQ — artifact */}
        <section id="faq" className="sv-wrap sv-section" style={{ paddingTop: 20 }}>
          <div className="sv-section-head sv-ios-center">
            <h2 className="sv-h2 sv-reveal">Questions, answered.</h2>
          </div>
          <div className="sv-art-faq sv-reveal">
            {faqs.map((faq, idx) => (
              <details key={faq.q} open={idx === 0}>
                <summary>{faq.q}</summary>
                <p>{faq.a}</p>
              </details>
            ))}
          </div>
        </section>

        {/* FINAL CTA — artifact */}
        <section className="sv-art-final">
          <div className="sv-wrap">
            <div className="sv-art-final-panel sv-reveal">
              <h2>Your next winning product<br />is already out there.</h2>
              <p className="sv-sub">Find it, price it right, and track it — with ScoutVeda.</p>
              <div style={{ marginTop: 28, display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap" }}>
                <Link href="/signup" className="sv-btn sv-btn-primary">Start your 30-day free trial</Link>
                <Link href="/login" className="sv-btn sv-btn-ghost">Log in</Link>
              </div>
              <p className="sv-art-final-note">No card needed · Cancel anytime · Support: support@scoutveda.com</p>
            </div>
          </div>
        </section>
      </main>

      {/* FOOTER — artifact, plus the live not-affiliated line */}
      <footer className="sv-art-footer">
        <div className="sv-wrap">
          <span>© 2026 ScoutVeda · Made for Indian sellers</span>
          <span><a href="mailto:support@scoutveda.com">support@scoutveda.com</a> &nbsp;·&nbsp; <a href="/login">Log in</a> &nbsp;·&nbsp; <a href="#features">Features</a> &nbsp;·&nbsp; <a href="#pricing">Pricing</a></span>
          <span>Sales figures are estimates. Fees per Amazon.in schedule.</span>
        </div>
        <div className="sv-wrap">
          <p className="sv-footer-fine">ScoutVeda is an independent research platform and is not affiliated with Amazon.</p>
        </div>
      </footer>
    </div>
  );
}
