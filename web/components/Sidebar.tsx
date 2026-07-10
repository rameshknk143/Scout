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
  const [selectedMarketplace, setSelectedMarketplace] = useState("amazon.in");

  // close the mobile drawer on route change
  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  const sections: SidebarSection[] = [
    {
      title: "Overview",
      items: [
        {
          href: "/",
          label: "Dashboard",
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2H6a2 2 0 01-2-2v-4zM14 16a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2h-2a2 2 0 01-2-2v-4z" />
            </svg>
          ),
        },
        {
          href: "/alerts",
          label: "Activity / Alerts",
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
          ),
        },
      ],
    },
    {
      title: "Research",
      items: [
        {
          href: "/validator",
          label: "Product Opportunity Finder",
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
          label: "Product Database",
          disabled: true,
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
            </svg>
          ),
        },
        {
          href: "#",
          label: "Competitor Analysis",
          disabled: true,
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 002 2h2a2 2 0 002-2z" />
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
        {
          href: "/watchlist",
          label: "Trend Explorer",
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          ),
        },
      ],
    },
    {
      title: "Catalog & Listings",
      items: [
        {
          href: "#",
          label: "My Products",
          disabled: true,
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
          ),
        },
        {
          href: "/listing",
          label: "Listing Optimizer",
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          ),
        },
        {
          href: "#",
          label: "Listing Health",
          disabled: true,
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          ),
        },
      ],
    },
    {
      title: "Operations",
      items: [
        {
          href: "#",
          label: "Inventory",
          disabled: true,
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          ),
        },
        {
          href: "/profit-calculator",
          label: "Profit & Fees",
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <rect x="4" y="4" width="16" height="16" rx="2" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 9h6M9 13h6M9 17h6" />
            </svg>
          ),
        },
      ],
    },
  ];

  return (
    <>
      {/* Mobile top bar */}
      <div className="md:hidden sticky top-0 z-30 flex items-center justify-between px-4 py-3 border-b border-zinc-200 bg-white">
        <div className="flex items-center gap-2">
          <span className="text-xl">🔭</span>
          <span className="font-bold tracking-tight text-zinc-900">SCOUT</span>
        </div>
        <button
          onClick={() => setOpen(true)}
          aria-label="Open menu"
          className="text-xl leading-none px-1 text-zinc-900"
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
            className="md:hidden fixed inset-0 z-40 bg-black/40"
          />
        )}
      </AnimatePresence>

      <aside
        className={`
          w-64 shrink-0 flex flex-col border-r border-zinc-200/80 px-4 py-6
          fixed inset-y-0 left-0 z-50 bg-white
          transition-transform duration-200 ease-out
          ${open ? "translate-x-0" : "-translate-x-full"}
          md:translate-x-0 md:sticky md:top-0 md:h-screen md:bg-white md:z-10
        `}
      >
        {/* Brand Area */}
        <div className="mb-6 px-2">
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold tracking-tight text-zinc-900">
              🔭 SCOUT
            </span>
          </div>
          <p className="text-[10px] text-zinc-500 mt-2 leading-relaxed font-semibold uppercase tracking-wider">
            KNK ENTERPRISES
          </p>
        </div>

        {/* Navigation Area */}
        <nav className="flex-1 flex flex-col gap-5 overflow-y-auto pr-1">
          {sections.map((section) => (
            <div key={section.title} className="space-y-1">
              <h3 className="text-[9px] font-bold uppercase tracking-widest text-zinc-400 px-2.5">
                {section.title}
              </h3>
              <div className="space-y-0.5">
                {section.items.map((item) => {
                  const active = pathname === item.href;
                  if (item.disabled) {
                    return (
                      <div
                        key={item.label}
                        className="flex items-center gap-2.5 px-2.5 py-1.5 text-xs text-zinc-300 font-medium cursor-not-allowed"
                      >
                        <span className="shrink-0">{item.icon}</span>
                        <span className="flex-1">{item.label}</span>
                      </div>
                    );
                  }

                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className="relative block py-1.5 px-2.5 rounded-lg hover:bg-zinc-50 transition-colors group"
                    >
                      {active && (
                        <motion.div
                          layoutId="nav-active-pill"
                          className="absolute inset-0 rounded-lg bg-zinc-100 border border-zinc-200/40"
                          transition={{ type: "spring", stiffness: 450, damping: 38 }}
                        />
                      )}
                      <span
                        className={`relative z-10 flex items-center gap-2.5 text-xs font-semibold transition-colors ${
                          active ? "text-zinc-950" : "text-zinc-500 hover:text-zinc-950"
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

        {/* Footer / Account / Marketplace selector */}
        <div className="mt-auto pt-4 border-t border-zinc-200 flex flex-col gap-3">
          {/* Marketplace Selector */}
          <div className="px-2">
            <label className="block text-[9px] font-bold uppercase tracking-wider text-zinc-400 mb-1">
              Active Marketplace
            </label>
            <select
              value={selectedMarketplace}
              onChange={(e) => setSelectedMarketplace(e.target.value)}
              className="w-full text-xs font-semibold text-zinc-700 bg-zinc-50 border border-zinc-200 rounded px-2 py-1 focus:outline-none focus:border-zinc-400"
            >
              <option value="amazon.in">🇮🇳 Amazon.in</option>
              <option value="amazon.com" disabled>🇺🇸 Amazon.com (Soon)</option>
              <option value="amazon.co.uk" disabled>🇬🇧 Amazon.co.uk (Soon)</option>
            </select>
          </div>

          {/* Settings & Help */}
          <div className="flex flex-col gap-1 px-2 text-xs font-medium text-zinc-500">
            <Link href="#" className="hover:text-zinc-950 flex items-center gap-2">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="3" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 11-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 11-2.83-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 112.83-2.83l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 112.83 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" />
              </svg>
              Settings
            </Link>
            <Link href="#" className="hover:text-zinc-950 flex items-center gap-2">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
              Documentation
            </Link>
          </div>
        </div>
      </aside>
    </>
  );
}
