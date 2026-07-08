"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

type NavItem = { href: string; label: string; icon: string };
type NavCategory = { id: string; label: string; icon: string; items: NavItem[] };

const NAV: NavCategory[] = [
  {
    id: "product-research",
    label: "Product Research",
    icon: "🔍",
    items: [
      { href: "/", label: "Trend Radar", icon: "📡" },
      { href: "/validator", label: "Validator", icon: "🎯" },
    ],
  },
  { id: "keyword-research", label: "Keyword Research", icon: "🔑", items: [] },
  {
    id: "listing",
    label: "Listing",
    icon: "📝",
    items: [{ href: "/listing", label: "Quality Score", icon: "📝" }],
  },
  { id: "market-intelligence", label: "Market Intelligence", icon: "🧭", items: [] },
  {
    id: "analytics",
    label: "Analytics",
    icon: "📊",
    items: [{ href: "/analytics", label: "Opportunity Scorer", icon: "📊" }],
  },
  {
    id: "pricing",
    label: "Pricing",
    icon: "🧮",
    items: [{ href: "/profit-calculator", label: "Profit Calculator", icon: "🧮" }],
  },
  {
    id: "watchlist-alerts",
    label: "Watchlist & Alerts",
    icon: "📋",
    items: [
      { href: "/watchlist", label: "Watchlist", icon: "📋" },
      { href: "/alerts", label: "Alerts", icon: "🔔" },
    ],
  },
  { id: "settings", label: "Settings", icon: "⚙️", items: [] },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [expanded, setExpanded] = useState<Set<string>>(
    () => new Set(NAV.filter((c) => c.items.some((i) => i.href === pathname)).map((c) => c.id))
  );

  const toggle = (id: string) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });

  // close the mobile drawer on route change
  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  return (
    <>
      {/* Mobile top bar */}
      <div className="md:hidden sticky top-0 z-30 flex items-center justify-between px-4 py-3 border-b border-white/8 bg-bg/95 backdrop-blur">
        <div className="flex items-center gap-2">
          <span className="text-xl">🔭</span>
          <span className="font-bold tracking-tight text-amber">SCOUT</span>
        </div>
        <button
          onClick={() => setOpen(true)}
          aria-label="Open menu"
          className="text-2xl leading-none px-1"
        >
          ☰
        </button>
      </div>

      {/* Mobile backdrop */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setOpen(false)}
            className="md:hidden fixed inset-0 z-40 bg-black/60"
          />
        )}
      </AnimatePresence>

      <aside
        className={`
          w-64 shrink-0 flex flex-col border-r border-white/8 px-5 py-6
          fixed inset-y-0 left-0 z-50 bg-bg-elevated
          transition-transform duration-300 ease-out
          ${open ? "translate-x-0" : "-translate-x-full"}
          md:translate-x-0 md:sticky md:top-0 md:h-screen md:bg-transparent
        `}
      >
        <div className="mb-8">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🔭</span>
            <span className="text-lg font-bold tracking-tight text-amber amber-glow-text">
              SCOUT
            </span>
          </div>
          <p className="text-xs text-muted mt-2 leading-relaxed">
            Personal Amazon India research tool · KNK Enterprises
          </p>
        </div>

        <nav className="flex flex-col gap-1 overflow-y-auto">
          {NAV.map((cat) => {
            const hasItems = cat.items.length > 0;
            const isExpanded = expanded.has(cat.id);
            const containsActive = cat.items.some((i) => i.href === pathname);

            return (
              <div key={cat.id}>
                <button
                  type="button"
                  disabled={!hasItems}
                  onClick={() => toggle(cat.id)}
                  className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                    containsActive ? "text-amber" : "text-muted"
                  } ${hasItems ? "hover:text-text cursor-pointer" : "opacity-50 cursor-default"}`}
                >
                  <span aria-hidden>{cat.icon}</span>
                  <span className="flex-1 text-left">{cat.label}</span>
                  {hasItems ? (
                    <span
                      aria-hidden
                      className={`text-xs transition-transform ${isExpanded ? "rotate-90" : ""}`}
                    >
                      ▶
                    </span>
                  ) : (
                    <span className="text-[10px] uppercase tracking-wide text-muted/50">
                      Soon
                    </span>
                  )}
                </button>

                <AnimatePresence initial={false}>
                  {hasItems && isExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.18 }}
                      className="overflow-hidden pl-4"
                    >
                      {cat.items.map((item) => {
                        const active = pathname === item.href;
                        return (
                          <Link key={item.href} href={item.href} className="relative block">
                            {active && (
                              <motion.div
                                layoutId="nav-active"
                                className="absolute inset-0 rounded-xl bg-amber/12 border border-amber/30"
                                transition={{ type: "spring", stiffness: 400, damping: 35 }}
                              />
                            )}
                            <span
                              className={`relative z-10 flex items-center gap-3 px-3.5 py-2 rounded-xl text-sm font-medium transition-colors ${
                                active ? "text-amber" : "text-muted hover:text-text"
                              }`}
                            >
                              <span aria-hidden>{item.icon}</span>
                              {item.label}
                            </span>
                          </Link>
                        );
                      })}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            );
          })}
        </nav>

        <div className="mt-auto pt-6 text-xs text-muted/70">
          Runs nightly in the cloud — collection continues even if this
          laptop is off.
        </div>
      </aside>
    </>
  );
}
