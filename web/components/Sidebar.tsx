"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

const NAV = [
  { href: "/", label: "Trend Radar", icon: "📡" },
  { href: "/validator", label: "Validator", icon: "🎯" },
  { href: "/watchlist", label: "Watchlist", icon: "📋" },
  { href: "/profit-calculator", label: "Profit Calculator", icon: "🧮" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

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
            Ram&apos;s personal product radar · KNK Enterprises
          </p>
          <p className="text-xs text-muted/70 mt-1">
            Not for resale, not tied to City Knights.
          </p>
        </div>

        <nav className="flex flex-col gap-1">
          {NAV.map((item) => {
            const active = pathname === item.href;
            return (
              <Link key={item.href} href={item.href} className="relative">
                {active && (
                  <motion.div
                    layoutId="nav-active"
                    className="absolute inset-0 rounded-xl bg-amber/12 border border-amber/30"
                    transition={{ type: "spring", stiffness: 400, damping: 35 }}
                  />
                )}
                <span
                  className={`relative z-10 flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                    active ? "text-amber" : "text-muted hover:text-text"
                  }`}
                >
                  <span aria-hidden>{item.icon}</span>
                  {item.label}
                </span>
              </Link>
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
