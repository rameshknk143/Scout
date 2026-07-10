"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

type SidebarItem = {
  href: string;
  label: string;
  icon: React.ReactNode;
  disabled?: boolean;
};

type SidebarSection = {
  title: string;
  items: SidebarItem[];
};

export default function Sidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  // close the mobile drawer on route change
  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  const sections: SidebarSection[] = [
    {
      title: "Product Research",
      items: [
        {
          href: "/",
          label: "Trend Radar",
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 002 2h2a2 2 0 002-2z" />
            </svg>
          ),
        },
        {
          href: "/validator",
          label: "Validator",
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10" />
              <circle cx="12" cy="12" r="6" />
              <circle cx="12" cy="12" r="2" />
            </svg>
          ),
        },
        {
          href: "#",
          label: "Keyword Research",
          disabled: true,
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 7a2 2 0 012 2m-3.414-1.414A2 2 0 1119 4a2 2 0 01-4.243 2.828M15 7l-3 3M9 13l-4 4v3h3l4-4M9 13L15 7" />
            </svg>
          ),
        },
      ],
    },
    {
      title: "Listing Optimization",
      items: [
        {
          href: "/listing",
          label: "Quality Score",
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          ),
        },
        {
          href: "#",
          label: "Market Intelligence",
          disabled: true,
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M16.243 7.757l-1.061 4.243-4.243 1.061 1.061-4.243 4.243-1.061z" />
            </svg>
          ),
        },
      ],
    },
    {
      title: "Analytics & Pricing",
      items: [
        {
          href: "/analytics",
          label: "Opportunity Scorer",
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          ),
        },
        {
          href: "/profit-calculator",
          label: "Profit Calculator",
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <rect x="4" y="4" width="16" height="16" rx="2" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 9h6M9 13h6M9 17h6" />
            </svg>
          ),
        },
      ],
    },
    {
      title: "Watchlist & Alerts",
      items: [
        {
          href: "/watchlist",
          label: "Watchlist",
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          ),
        },
        {
          href: "/alerts",
          label: "Alerts",
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
          ),
        },
        {
          href: "#",
          label: "Settings",
          disabled: true,
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="3" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 11-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 11-2.83-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 112.83-2.83l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 112.83 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" />
            </svg>
          ),
        },
      ],
    },
  ];

  return (
    <>
      {/* Mobile top bar */}
      <div className="md:hidden sticky top-0 z-30 flex items-center justify-between px-4 py-3 border-b border-white/5 bg-bg/95 backdrop-blur">
        <div className="flex items-center gap-2">
          <span className="text-xl">🔭</span>
          <span className="font-bold tracking-tight text-text">SCOUT</span>
        </div>
        <button
          onClick={() => setOpen(true)}
          aria-label="Open menu"
          className="text-xl leading-none px-1 text-text"
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
          w-64 shrink-0 flex flex-col border-r border-white/5 px-4 py-6
          fixed inset-y-0 left-0 z-50 bg-bg-elevated
          transition-transform duration-200 ease-out
          ${open ? "translate-x-0" : "-translate-x-full"}
          md:translate-x-0 md:sticky md:top-0 md:h-screen md:bg-transparent
        `}
      >
        {/* Brand Area */}
        <div className="mb-8 px-2">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🔭</span>
            <span className="text-lg font-bold tracking-tight text-text">
              SCOUT
            </span>
          </div>
          <p className="text-[10px] text-muted mt-2 leading-relaxed font-medium uppercase tracking-wide">
            KNK ENTERPRISES · RESEARCH
          </p>
        </div>

        {/* Navigation Area */}
        <nav className="flex flex-col gap-6 overflow-y-auto pr-1">
          {sections.map((section) => (
            <div key={section.title} className="space-y-1.5">
              <h3 className="text-[9px] font-extrabold uppercase tracking-widest text-muted/60 px-2.5">
                {section.title}
              </h3>
              <div className="space-y-0.5">
                {section.items.map((item) => {
                  const active = pathname === item.href;
                  if (item.disabled) {
                    return (
                      <div
                        key={item.label}
                        className="flex items-center gap-2.5 px-2.5 py-1.5 text-xs text-muted/40 font-medium cursor-not-allowed"
                      >
                        <span className="shrink-0">{item.icon}</span>
                        <span className="flex-1">{item.label}</span>
                        <span className="text-[8px] uppercase tracking-wider bg-white/5 border border-white/5 px-1 py-0.5 rounded font-bold">
                          Soon
                        </span>
                      </div>
                    );
                  }

                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className="relative block py-1.5 px-2.5 rounded-lg hover:bg-white/5 transition-colors group"
                    >
                      {active && (
                        <motion.div
                          layoutId="nav-active-pill"
                          className="absolute inset-0 rounded-lg bg-white/5 border border-white/10"
                          transition={{ type: "spring", stiffness: 450, damping: 38 }}
                        />
                      )}
                      <span
                        className={`relative z-10 flex items-center gap-2.5 text-xs font-semibold transition-colors ${
                          active ? "text-text" : "text-muted hover:text-text"
                        }`}
                      >
                        <span className={`shrink-0 transition-opacity ${active ? "opacity-100" : "opacity-60 group-hover:opacity-100"}`}>
                          {item.icon}
                        </span>
                        {item.label}
                      </span>
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* Footer Area */}
        <div className="mt-auto pt-4 px-2.5 text-[9px] text-muted/40 border-t border-white/5 leading-relaxed">
          Nightly collections run automatically in the cloud.
        </div>
      </aside>
    </>
  );
}
