"use client";

import Link from "next/link";
import { useState, useEffect, useRef } from "react";
import Tilt from "@/components/3d/Tilt";
import BrowserShowcase from "@/components/BrowserShowcase";
import { ThemeToggle } from "@/components/ThemeToggle";
import { OpportunityDial } from "@/components/3d/OpportunityDial";
import PerspectiveGrid from "@/components/3d/PerspectiveGrid";
import { GlassCard } from "@/components/3d/GlassCard";
import { FeatureCard3D } from "@/components/3d/FeatureCard3D";
import { TrustBadge } from "@/components/3d/TrustBadge";

function Wordmark() {
  return (
    <Link href="/" className="sv-mark" aria-label="ScoutVeda Home">
      <span className="sv-mark-dot" aria-hidden="true" />
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
];

interface StaggerItem {
  delay: number;
  visible: boolean;
}

export default function Landing() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [annualBilling, setAnnualBilling] = useState(true);
  const [openFaq, setOpenFaq] = useState<number | null>(null);
  const [scrolled, setScrolled] = useState(false);
  const [mounted, setMounted] = useState(false);

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

  // Staggered entrance animation
  const [staggerItems, setStaggerItems] = useState<StaggerItem[]>([
    { delay: 0, visible: false },
    { delay: 100, visible: false },
    { delay: 200, visible: false },
    { delay: 300, visible: false },
    { delay: 400, visible: false },
    { delay: 500, visible: false },
  ]);

  useEffect(() => {
    setMounted(true);
    // Trigger staggered entrance
    staggerItems.forEach((item, i) => {
      setTimeout(() => {
        setStaggerItems((prev) =>
          prev.map((p, idx) => (idx === i ? { ...p, visible: true } : p))
        );
      }, item.delay);
    });

    // Scroll handler for header
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const features = [
    {
      title: "Discover High-Margin Niche Products",
      desc: "Surface uncrowded opportunities across categories instead of scrolling bestseller lists by hand.",
      icon: "search",
    },
    {
      title: "Evaluate Incumbent Competition",
      desc: "See review depth, price stability, and seller entrenchment before committing a single rupee.",
      icon: "shield",
    },
    {
      title: "Calculate Real FBA Net Profit",
      desc: "Model Amazon Easy Ship, FBA referral fees, GST (18%), and closing fees up front.",
      icon: "coin",
    },
    {
      title: "Track Rank & Sales Trends",
      desc: "Watch product demand velocity — climbing, stable, seasonal, or fading.",
      icon: "trend",
    },
  ];

  const howSteps = [
    {
      n: "1",
      title: "Authorize on Amazon",
      desc: "Click 'Connect' on ScoutVeda. You are redirected to Seller Central to log in and approve read-only permissions on Amazon's site.",
    },
    {
      n: "2",
      title: "We Sync Read-Only Data",
      desc: "ScoutVeda's 4-wave sync engine securely backfills order metrics, sales totals, and inventory health without touching your password.",
    },
    {
      n: "3",
      title: "Actionable Insights",
      desc: "Your personalized dashboard populates with live sales trends, stockout alerts, and AI next actions.",
    },
  ];

  const securityItems = [
    {
      title: "Fernet Token Encryption",
      desc: "Refresh tokens are encrypted at rest using AES-128 Fernet keys.",
    },
    {
      title: "OAuth 2.0 Protocol",
      desc: "Your Amazon password never touches ScoutVeda servers.",
    },
    {
      title: "Least-Privilege Scopes",
      desc: "We request only the minimum read-only permissions needed.",
    },
    {
      title: "Instant Revocation",
      desc: "One-click disconnect deletes stored credentials immediately.",
    },
  ];

  const plans = [
    {
      name: "Starter",
      price: annualBilling ? "₹1,499" : "₹2,299",
      desc: "Perfect for new resellers researching their first products.",
      features: [
        "1 Connected Storefront",
        "100 ASIN Validations/mo",
        "Basic Margin Calculator",
        "Daily Keyword Tracking",
      ],
      cta: "Start Free Trial",
      popular: false,
    },
    {
      name: "Pro Reseller",
      price: annualBilling ? "₹2,999" : "₹4,499",
      desc: "For active Amazon sellers scaling inventory & PPC.",
      features: [
        "3 Connected Storefronts",
        "Unlimited Validations",
        "FBA Fee & Tax Breakdown",
        "Real-Time Stockout Alerts",
        "Competitor Review Miner",
      ],
      cta: "Get Pro Access",
      popular: true,
    },
    {
      name: "Agency & Brand",
      price: annualBilling ? "₹6,999" : "₹9,999",
      desc: "For agencies managing multiple Amazon seller accounts.",
      features: [
        "10 Connected Storefronts",
        "Multi-Workspace Access",
        "Custom Export Reports",
        "Dedicated Account Manager",
        "API Data Access",
      ],
      cta: "Contact Sales",
      popular: false,
    },
  ];

  return (
    <div className="sv-page">
      {/* Animated background grid */}
      <div className="sv-bg" aria-hidden="true">
        <PerspectiveGrid />
        <div className="sv-grid-perspective">
          <div className="sv-grid-plane" />
        </div>
      </div>

      {/* Header with theme toggle */}
      <header
        className={`sv-header ${scrolled ? "sv-header--scrolled" : ""}`}
        style={{
          transform: scrolled
            ? "translateY(0)"
            : "translateY(0)",
          transition: "background-color var(--dur-base) var(--ease-out), box-shadow var(--dur-base) var(--ease-out)",
        }}
      >
        <div className="sv-wrap sv-header-inner">
          <Wordmark />
          <nav className="sv-nav" aria-label="Primary">
            {NAV.map((n, i) => (
              <a
                key={n.href}
                href={n.href}
                style={{
                  opacity: staggerItems[i]?.visible ? 1 : 0,
                  transform: staggerItems[i]?.visible
                    ? "translateY(0)"
                    : "translateY(-10px)",
                  transition: `opacity var(--dur-base) var(--ease-out) ${staggerItems[i]?.delay ?? 0}ms, transform var(--dur-base) var(--ease-out) ${staggerItems[i]?.delay ?? 0}ms`,
                }}
              >
                {n.label}
              </a>
            ))}
          </nav>
          <div className="sv-header-cta">
            <ThemeToggle />
            <Link
              href="/login"
              className="sv-btn sv-btn-ghost sv-hide-sm"
              style={{
                opacity: staggerItems[5]?.visible ? 1 : 0,
                transform: staggerItems[5]?.visible
                  ? "translateY(0)"
                  : "translateY(-10px)",
                transition: `opacity var(--dur-base) var(--ease-out) ${staggerItems[5].delay}ms, transform var(--dur-base) var(--ease-out) ${staggerItems[5].delay}ms`,
              }}
            >
              Log in
            </Link>
            <Link
              href="/signup"
              className="sv-btn sv-btn-primary"
              style={{
                opacity: staggerItems[5]?.visible ? 1 : 0,
                transform: staggerItems[5]?.visible
                  ? "translateY(0)"
                  : "translateY(-10px)",
                transition: `opacity var(--dur-base) var(--ease-out) ${staggerItems[5].delay}ms, transform var(--dur-base) var(--ease-out) ${staggerItems[5].delay}ms`,
              }}
            >
              Start free
            </Link>
            <button
              className="sv-burger"
              aria-label="Menu"
              aria-expanded={menuOpen}
              onClick={() => setMenuOpen((v) => !v)}
            >
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                {menuOpen ? (
                  <>
                    <path d="M18 6 6 18" />
                    <path d="M6 6l12 12" />
                  </>
                ) : (
                  <>
                    <path d="M3 6h18" />
                    <path d="M3 12h18" />
                    <path d="M3 18h18" />
                  </>
                )}
              </svg>
            </button>
          </div>
        </div>
        {menuOpen && (
          <div
            className="sv-mobile-menu"
            style={{
              display: "flex",
              animation: "slideDown var(--dur-base) var(--ease-out)",
            }}
          >
            {NAV.map((n) => (
              <a
                key={n.href}
                href={n.href}
                onClick={() => setMenuOpen(false)}
              >
                {n.label}
              </a>
            ))}
            <a href="/login">Log in</a>
          </div>
        )}
      </header>

      {/* HERO - Premium 3D */}
      <section className="sv-wrap sv-hero">
        <div className="sv-hero-grid">
          <div
            style={{
              opacity: staggerItems[0]?.visible ? 1 : 0,
              transform: staggerItems[0]?.visible
                ? "translateY(0)"
                : "translateY(20px)",
              transition: `opacity var(--dur-slow) var(--ease-out) ${
                staggerItems[0].delay
              }ms, transform var(--dur-slow) var(--ease-out) ${
                staggerItems[0].delay
              }ms`,
            }}
          >
            <span className="sv-eyebrow">The Operating System for Amazon Sellers</span>
            <h1 className="sv-h1">
              Run your Amazon business with <span className="text-accent">total confidence</span>.
            </h1>
            <p className="sv-lede">
              Research products, calculate real net margins, monitor keywords, and sync storefront sales in one secure workspace.
            </p>
            <div className="sv-hero-cta">
              <Link
                href="/signup"
                className="sv-btn sv-btn-primary sv-btn-lg"
                style={{
                  opacity: staggerItems[1]?.visible ? 1 : 0,
                  transform: staggerItems[1]?.visible
                    ? "translateY(0)"
                    : "translateY(20px)",
                  transition: `opacity var(--dur-slow) var(--ease-out) ${
                    staggerItems[1].delay
                  }ms, transform var(--dur-slow) var(--ease-out) ${
                    staggerItems[1].delay
                  }ms`,
                }}
              >
                Start Free Research
              </Link>
              <a
                href="#how"
                className="sv-btn sv-btn-ghost sv-btn-lg"
                style={{
                  opacity: staggerItems[2]?.visible ? 1 : 0,
                  transform: staggerItems[2]?.visible
                    ? "translateY(0)"
                    : "translateY(20px)",
                  transition: `opacity var(--dur-slow) var(--ease-out) ${
                    staggerItems[2].delay
                  }ms, transform var(--dur-slow) var(--ease-out) ${
                    staggerItems[2].delay
                  }ms`,
                }}
              >
                See How It Works
              </a>
            </div>
            <div className="sv-hero-trust">
              <svg
                width="15"
                height="15"
                viewBox="0 0 24 24"
                fill="none"
                stroke="var(--accent)"
                strokeWidth="2"
              >
                <path d="M20 6 9 17l-5-5" />
              </svg>
              <span>Built on Amazon&apos;s Official SP-API OAuth</span>
              <span className="divider" aria-hidden="true">·</span>
              <span>Read-only access</span>
              <span className="divider" aria-hidden="true">·</span>
              <span>Revoke anytime</span>
            </div>
          </div>

          {/* 3D Hero Preview - Opportunity Dial + Browser Showcase */}
          <div
            style={{
              opacity: staggerItems[3]?.visible ? 1 : 0,
              transform: staggerItems[3]?.visible
                ? "translateY(0) scale(1)"
                : "translateY(30px) scale(0.95)",
              transition: `opacity var(--dur-slow) var(--ease-out) ${
                staggerItems[3].delay
              }ms, transform var(--dur-slow) var(--ease-out) ${
                staggerItems[3].delay
              }ms`,
            }}
          >
            <HeroPreview3D />
          </div>
        </div>
      </section>

      {/* PROBLEM / VALUE - 3D Feature Cards */}
      <section
        id="research"
        className="sv-wrap sv-section"
        aria-labelledby="research-heading"
      >
        <div className="sv-section-head">
          <span className="sv-eyebrow">The Sourcing Challenge</span>
          <h2 id="research-heading" className="sv-h2">
            Sourcing gets expensive when decisions are guesswork.
          </h2>
          <p className="sv-sub">
            Buying inventory on a hunch ties up capital in slow-moving products. ScoutVeda gives you the exact numbers before you buy.
          </p>
        </div>
        <div className="sv-feature-grid">
          {features.map((f, i) => (
            <FeatureCard3D
              key={f.title}
              title={f.title}
              desc={f.desc}
              icon={f.icon}
              delay={i * 100}
            />
          ))}
        </div>
      </section>

      {/* HOW IT WORKS - 3-Step with 3D Depth */}
      <section
        id="how"
        className="sv-wrap sv-section"
        style={{ paddingTop: 0 }}
        aria-labelledby="how-heading"
      >
        <div className="sv-section-head">
          <span className="sv-eyebrow">How Connection Works</span>
          <h2 id="how-heading" className="sv-h2">
            Three simple steps to unlock your seller cockpit.
          </h2>
        </div>
        <div className="sv-steps">
          {howSteps.map((s, i) => (
            <GlassCard
              key={s.n}
              className="sv-step"
              delay={i * 150}
              elevation="medium"
            >
              <div className="sv-step-n">{s.n}</div>
              <h3>{s.title}</h3>
              <p>{s.desc}</p>
            </GlassCard>
          ))}
        </div>
      </section>

      {/* SECURITY - Trust Badges */}
      <section
        id="security"
        className="sv-wrap sv-section"
        style={{ paddingTop: 0 }}
        aria-labelledby="security-heading"
      >
        <div className="sv-section-head">
          <span className="sv-eyebrow text-accent">Trust & Security</span>
          <h2 id="security-heading" className="sv-h2">
            Trust is the product. Enterprise security at every layer.
          </h2>
          <p className="sv-sub">
            We handle your storefront tokens and financial data with the highest security standards.
          </p>
        </div>
        <div className="sv-feature-grid">
          {securityItems.map((sec, i) => (
            <TrustBadge
              key={sec.title}
              title={sec.title}
              desc={sec.desc}
              delay={i * 100}
            />
          ))}
        </div>
      </section>

      {/* PRICING - with 3D depth on hover */}
      <section
        id="pricing"
        className="sv-wrap sv-section"
        style={{ paddingTop: 0 }}
        aria-labelledby="pricing-heading"
      >
        <div className="sv-section-head">
          <span className="sv-eyebrow">Transparent Pricing</span>
          <h2 id="pricing-heading" className="sv-h2">
            Plans that scale with your Amazon business.
          </h2>
          <div className="flex items-center justify-center gap-3 mt-4">
            <span
              className={`text-xs font-semibold ${
                !annualBilling ? "text-text-primary" : "text-text-tertiary"
              }`}
            >
              Monthly
            </span>
            <button
              onClick={() => setAnnualBilling(!annualBilling)}
              className="relative w-12 h-6 rounded-full bg-accent/20 p-1 transition-colors border border-accent/40"
              aria-label={annualBilling ? "Switch to monthly" : "Switch to annual"}
            >
              <div
                className={`w-4 h-4 rounded-full bg-accent transition-transform ${
                  annualBilling ? "translate-x-6" : ""
                }`}
              />
            </button>
            <span
              className={`text-xs font-semibold ${
                annualBilling ? "text-accent" : "text-text-tertiary"
              }`}
            >
              Annual{" "}
              <span className="bg-accent/20 text-accent text-[10px] px-2 py-0.5 rounded-full border border-accent/30">
                Save 35%
              </span>
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
          {plans.map((plan, i) => (
            <GlassCard
              key={plan.name}
              className={`p-6 rounded-2xl flex flex-col justify-between relative ${
                plan.popular
                  ? "border-accent/50 bg-accent/[0.06] ring-1 ring-accent/30"
                  : ""
              }`}
              elevation={plan.popular ? "high" : "medium"}
              delay={i * 150}
            >
              {plan.popular && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-accent text-surface-0 text-[10px] font-bold uppercase tracking-wider px-3 py-0.5 rounded-full">
                  Most Popular
                </span>
              )}
              <div>
                <h3 className="text-base font-bold text-text-primary">
                  {plan.name}
                </h3>
                <p className="text-xs text-text-tertiary mt-1">{plan.desc}</p>
                <div className="my-5">
                  <span className="text-3xl font-extrabold text-text-primary">
                    {plan.price}
                  </span>
                  <span className="text-xs text-text-tertiary font-medium">
                    / month
                  </span>
                </div>
                <ul className="space-y-2 text-xs text-text-secondary">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-center gap-2">
                      <span className="text-accent font-bold">✓</span> {f}
                    </li>
                  ))}
                </ul>
              </div>
              <Link
                href="/signup"
                className={`sv-btn mt-6 w-full text-center ${
                  plan.popular ? "sv-btn-primary" : "sv-btn-ghost"
                }`}
              >
                {plan.cta}
              </Link>
            </GlassCard>
          ))}
        </div>
      </section>

      {/* FAQ - Accordion with smooth animation */}
      <section
        id="faq"
        className="sv-wrap sv-section"
        style={{ paddingTop: 0 }}
        aria-labelledby="faq-heading"
      >
        <div className="sv-section-head">
          <span className="sv-eyebrow">Frequently Asked Questions</span>
          <h2 id="faq-heading" className="sv-h2">
            Answers to your top questions.
          </h2>
        </div>
        <div className="max-w-2xl mx-auto space-y-3 mt-6">
          {faqs.map((faq, idx) => (
            <GlassCard
              key={idx}
              className="rounded-xl overflow-hidden border border-white/10"
              elevation="low"
              delay={idx * 80}
            >
              <button
                onClick={() => setOpenFaq(openFaq === idx ? null : idx)}
                className="w-full p-4 text-left font-semibold text-xs text-text-primary flex justify-between items-center"
              >
                <span>{faq.q}</span>
                <span className="text-accent font-bold transition-transform duration-200">
                  {openFaq === idx ? "−" : "+"}
                </span>
              </button>
              {openFaq === idx && (
                <div
                  className="px-4 pb-4 text-xs text-text-tertiary leading-relaxed border-t border-white/5 pt-3 animate-fade-in"
                >
                  {faq.a}
                </div>
              )}
            </GlassCard>
          ))}
        </div>
      </section>

      {/* FEEDBACK */}
      <section
        id="feedback"
        className="sv-wrap sv-section"
        style={{ paddingTop: 0, paddingBottom: "40px" }}
      >
        <GlassCard
          className="p-6 md:p-8 rounded-2xl flex flex-col md:flex-row items-center justify-between gap-6 border-l-4 border-l-accent border-t border-r border-b border-black/5 bg-gradient-to-br from-accent/5 to-white/70 backdrop-blur-md shadow-sm"
        >
          <div className="max-w-lg text-left">
            <span className="sv-eyebrow" style={{ color: "var(--accent)" }}>
              Feedback & Suggestions
            </span>
            <h2 className="text-lg font-bold text-text-primary mt-1" style={{ fontSize: "1.25rem" }}>
              Help us shape the future of ScoutVeda
            </h2>
            <p className="text-xs text-text-tertiary leading-relaxed mt-2 font-semibold">
              Have suggestions, feature requests, or encountered a bug? We iterate fast based on seller input. Reach out directly via Email or WhatsApp.
            </p>
          </div>
          <div className="flex flex-wrap gap-3 shrink-0">
            <a
              href="mailto:rameshknk143@gmail.com?subject=ScoutVeda Feedback & Suggestions"
              className="sv-btn sv-btn-ghost flex items-center gap-2 text-xs py-2.5 px-4 border border-black/10 hover:bg-surface-2 cursor-pointer shadow-sm rounded-lg"
              style={{ padding: "10px 16px", fontSize: "11px", fontWeight: "bold" }}
            >
              ✉️ Email Suggestions
            </a>
            <a
              href="https://wa.me/919900000000?text=Hi%20Ram,%20I%20have%20some%20feedback/suggestions%20for%20ScoutVeda..."
              target="_blank"
              rel="noopener noreferrer"
              className="sv-btn sv-btn-primary flex items-center gap-2 text-xs py-2.5 px-4 bg-positive hover:bg-positive/90 text-accent-on cursor-pointer shadow-sm rounded-lg border border-positive/10"
              style={{ padding: "10px 16px", fontSize: "11px", fontWeight: "bold" }}
            >
              💬 WhatsApp Chat
            </a>
          </div>
        </GlassCard>
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

function HeroPreview3D() {
  return (
    <div className="relative w-full max-w-[620px] mx-auto py-10">
      <div className="grid grid-cols-2 gap-4 md:grid-cols-1">
        <div className="relative">
          <OpportunityDial score={82} size={280} />
        </div>
        <div className="md:hidden">
          <Tilt className="relative w-full max-w-[620px] mx-auto py-10">
            <BrowserShowcase />
          </Tilt>
        </div>
      </div>
      <div className="hidden md:block mt-8">
        <Tilt className="relative w-full max-w-[620px] mx-auto py-10">
          <BrowserShowcase />
        </Tilt>
      </div>
    </div>
  );
}

function Icon({ name }: { name: string }) {
  const common = {
    width: 18,
    height: 18,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 2,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
  };
  if (name === "search")
    return (
      <svg {...common}>
        <circle cx="11" cy="11" r="7" />
        <path d="m21 21-4.3-4.3" />
      </svg>
    );
  if (name === "shield")
    return (
      <svg {...common}>
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z" />
      </svg>
    );
  if (name === "coin")
    return (
      <svg {...common}>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v10M9.5 9.5h4a1.5 1.5 0 0 1 0 3h-3a1.5 1.5 0 0 0 0 3h4" />
      </svg>
    );
  return (
    <svg {...common}>
      <path d="M3 17l6-6 4 4 8-8" />
      <path d="M17 7h4v4" />
    </svg>
  );
}